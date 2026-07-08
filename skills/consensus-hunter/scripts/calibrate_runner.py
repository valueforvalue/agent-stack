"""
Calibration runner: drives the consensus-hunter skill against a real repo
at a knowledge cutoff, computes Brier + Skill Score against a known-bug
ground truth set.

This script is the empirical half of consensus-hunter. Its job is to take
a target repo at a fixed commit (the knowledge cutoff) and a labeled
held-out set (bugs disclosed AFTER the cutoff), run the agents, and
measure how well the resulting risk scores separate buggy from clean
functions.

The script is deliberately separate from the agent-launching logic:
  - The 5 agents are launched by `launch_agents.py` (parallel; supports
    a max-concurrent cap for environments that limit it).
  - This script consumes the captured JSON outputs, runs the aggregator,
    computes the metrics, and emits the calibration report.

References:
  - Spiess et al. ICSE 2025 -> Skill Score is the right metric.
  - Pascarella & Bacchelli -> time-aware split is mandatory.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable

from lib.aggregate import aggregate_run
from lib.calibrate import brier_score, skill_score, per_agent_calibration
from lib.schema import validate_input


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LIB = ROOT / "lib"


def load_agent_outputs(out_dir: Path) -> list[dict]:
    """Load all *.json files in `out_dir` that look like agent outputs."""
    outputs = []
    for p in sorted(out_dir.glob("agent_*.json")):
        with p.open() as f:
            obj = json.load(f)
        try:
            validate_input(obj)
            outputs.append(obj)
        except ValueError as e:
            print(f"WARN: skipping {p.name}: {e}")
    return outputs


def load_held_out_bugs(repo: Path, cutoff: str) -> list[tuple[str, str]]:
    """Walk git log on the repo, find bug-fixing commits after `cutoff`,
    resolve to (file, function) pairs via the commit patch.

    Cheap keyword filter (fix/bug/sec/CVE). v1.1 should pull from a tagged
    CVE commit list — BugSwarm + SWE-Bench gold patches first.
    """
    import re
    kw = re.compile(r"\b(fix(?:es|ed)?|bug|cve[- ]?\d|sec(?:urity)?|bpo[- ]?\d+)\b", re.IGNORECASE)
    since = ["--since", cutoff]
    log_format = "--pretty=format:COMMIT:%H %ad %s"
    log = subprocess.run(
        ["git", "-C", str(repo), "log"] + since + ["--date=short", log_format, "-p"],
        capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
    )
    if log.returncode != 0:
        raise RuntimeError(f"git log failed: {log.stderr}")

    fn_re = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    cur_commit = None
    cur_files: list[tuple[str, list[str]]] = []  # (file, lines)
    in_patch = False
    for line in log.stdout.splitlines():
        if line.startswith("COMMIT:"):
            # Process previous commit if it qualified
            if cur_commit and cur_files:
                msg_match = kw.search(cur_commit_text)
                if msg_match:
                    for fpath, lines in cur_files:
                        for ln in lines:
                            m = fn_re.match(ln)
                            if m:
                                key = (fpath, m.group(1))
                                if key not in seen:
                                    seen.add(key)
                                    out.append(key)
            # Reset
            parts = line[len("COMMIT:"):].split(" ", 2)
            cur_commit = parts[0]
            cur_commit_text = parts[2] if len(parts) > 2 else ""
            cur_files = []
            in_patch = False
        elif line.startswith("diff --git"):
            in_patch = True
            # crude: filename comes after "+++ b/"
            # but we just rely on "+++" lines next
        elif line.startswith("+++ b/"):
            fpath = line[len("+++ b/"):].strip()
            cur_files.append([fpath, []])
        elif in_patch and line.startswith("+") and not line.startswith("+++"):
            if cur_files:
                cur_files[-1][1].append(line[1:])
    return out


def build_label_set(
    held_out: list[tuple[str, str]],
    coords: Iterable[str],
) -> list[int]:
    """For each candidate coord, return 1 if buggy per `held_out`, else 0."""
    held_keys = set(held_out)
    return [1 if tuple(c.split(":", 1)) in held_keys else 0 for c in coords]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--cutoff", required=True, help="ISO date (e.g. 2020-06-01)")
    ap.add_argument("--outputs", required=True, type=Path,
                    help="Directory of agent_*.json captured from the run.")
    ap.add_argument("--emit", required=True, type=Path,
                    help="Path to write .consensus-hunter/calibration.json")
    args = ap.parse_args()

    if not args.repo.exists():
        print(f"ERROR: repo not found: {args.repo}")
        return 2

    # Step 1 — load agent outputs
    outputs = load_agent_outputs(args.outputs)
    if not outputs:
        print(f"ERROR: no agent outputs found in {args.outputs}")
        return 2
    print(f"loaded {len(outputs)} agent output file(s)")

    # Step 2 — gather coords under evaluation
    all_coords = set()
    for o in outputs:
        for f in o["findings"]:
            all_coords.add(f["coord"])
    coord_list = sorted(all_coords)
    print(f"coords under evaluation: {len(coord_list)}")

    # Step 3 — held-out bug labels from git history after cutoff
    held_out = load_held_out_bugs(args.repo, args.cutoff)
    labels = build_label_set(held_out, coord_list)
    n_bugs = sum(labels)
    print(f"held-out bugs in this surface: {n_bugs} / {len(labels)} ({n_bugs/max(1,len(labels)):.2%})")

    # Step 4 — aggregate
    ranked = aggregate_run(outputs, history_priors=None, w_prior=0.0)
    by_coord = {r["coord"]: r["consensus_score"] for r in ranked}

    # Step 5 — per-agent metrics
    per_agent_pairs: list[tuple[str, list[tuple[str, int]], list[float]]] = []
    for o in outputs:
        findings_by_coord = {f["coord"]: f["score"] for f in o["findings"]}
        agent_labels: list[tuple[str, int]] = []
        agent_scores: list[float] = []
        for c in coord_list:
            if c in findings_by_coord:
                agent_labels.append((c, labels[coord_list.index(c)]))
                agent_scores.append(findings_by_coord[c])
        per_agent_pairs.append((o["agent_id"], agent_labels, agent_scores))

    calib = per_agent_calibration(per_agent_pairs)

    # Step 6 — aggregator metrics (consensus_score as a single predictor)
    consensus_pred = [by_coord.get(c, 0.0) for c in coord_list]
    consensus_label = labels
    calib["consensus"] = {
        "n": len(consensus_pred),
        "brier": round(brier_score(consensus_pred, consensus_label), 4),
        "skill_score": round(skill_score(consensus_pred, consensus_label), 4),
    }

    # Step 7 — emit
    args.emit.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema": "consensus-hunter/calibration/v1",
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "repo": str(args.repo),
        "cutoff": args.cutoff,
        "n_coords_evaluated": len(coord_list),
        "n_buggy_in_surface": n_bugs,
        "n_agents": len(outputs),
        "calibration": calib,
    }
    with args.emit.open("w") as f:
        json.dump(meta, f, indent=2)
    print(f"wrote {args.emit}")
    print()
    print("Summary:")
    print(f"  consensus Skill Score = {calib['consensus']['skill_score']:.3f}")
    print(f"  consensus Brier       = {calib['consensus']['brier']:.3f}")
    for aid, r in calib["agents"].items():
        print(f"  {aid:32s} n={r['n']:4d}  brier={r['brier']:.3f}  ss={r['skill_score']:.3f}  platt_ss={r['platt_skill_score']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
