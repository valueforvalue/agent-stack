"""
End-to-end django@2020-06-01 calibration run.

This script is a *measurement* step, not a real-LLM calibration. It drives
the consensus-hunter measurement pipeline end-to-end against the REAL held-out
bug set extracted from django's post-cutoff commit history.

The agent outputs are simulated with three personas:
  - "good": high accuracy (~80% agreement with truth)
  - "noisy": mid accuracy (~60% agreement)
  - "biased": skewed by a systematic error mode

This lets us measure:
  - Does the calibration harness extract a clean Skill Score?
  - Does the consensus aggregation beat any single agent?
  - Does Platt scaling lift Skill Score as Spiess et al. predicted?
  - Does Brier / base-rate / agreement_band distribution look sane?

A real LLM calibration replaces the `simulate_agents` function below with
calls to the parent process or an LLM SDK.

Usage:
    python scripts/run_django_calibration.py \
        --repo cal-targets/django \
        --cutoff 2020-06-01 \
        --emit .consensus-hunter/calibration.json
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import sys
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from calibrate_runner import load_held_out_bugs, build_label_set  # noqa: E402
from lib.aggregate import aggregate_run, _logit, _sigmoid  # noqa: E402
from lib.calibrate import (  # noqa: E402
    brier_score, skill_score, fit_platt, apply_platt,
    per_agent_calibration,
)
from lib.schema import validate_input  # noqa: E402


@dataclass
class AgentPersona:
    agent_id: str
    accuracy: float       # probability the score is "right direction"
    bias: float           # mean offset; + means overconfident, - means under
    noise: float          # std dev added
    evidence_slice: str

    def score(self, is_buggy: bool, rng: random.Random) -> float:
        target = 0.80 if is_buggy else 0.20
        # Add persona bias
        target = target + self.bias
        # Coin flip: with prob (1 - accuracy) invert
        if rng.random() > self.accuracy:
            target = 1.0 - target
        # Noise
        v = target + rng.gauss(0, self.noise)
        return max(0.0, min(1.0, v))


def simulate_agents(
    coords_evaluated: list[str],
    labels: list[int],
    personas: list[AgentPersona],
    seed: int,
) -> list[dict]:
    """Synthesize per-agent JSON outputs against (coord, label) pairs."""
    rng = random.Random(seed)
    outputs = []
    for persona in personas:
        findings = []
        for c, y in zip(coords_evaluated, labels):
            s = persona.score(bool(y), rng)
            band = "HIGH" if s > 0.7 else ("MED" if s > 0.3 else "LOW")
            findings.append({
                "coord": c,
                "score": round(s, 4),
                "rank_band": band,
                "evidence_quote": f"synthetic evidence line for {c}",
                "reasoning": f"synthetic reasoning for {c} by {persona.agent_id}",
            })
        outputs.append({
            "agent_id": persona.agent_id,
            "evidence_slice": persona.evidence_slice,
            "findings": findings,
        })
    return outputs


SCENARIOS = {
    "best_case": [
        AgentPersona("static_security",   0.80, 0.00, 0.10, "static:fn+callers"),
        AgentPersona("history_churn",     0.78, 0.00, 0.12, "history:git_blame_24mo"),
        AgentPersona("test_coverage",     0.82, 0.00, 0.10, "test:branch-coverage"),
        AgentPersona("contract_violator", 0.75, 0.00, 0.13, "contract:fn-sig+callers"),
        AgentPersona("spec_compliance",   0.77, 0.00, 0.11, "spec:docstring+commit-intent"),
    ],
    "varied": [
        AgentPersona("static_security",   0.82, 0.00, 0.10, "static:fn+callers"),
        AgentPersona("history_churn",     0.50, 0.00, 0.20, "history:git_blame_24mo"),
        AgentPersona("test_coverage",     0.78, 0.00, 0.12, "test:branch-coverage"),
    ],
    "biased_one": [
        AgentPersona("static_security",   0.80, +0.05, 0.10, "static:fn+callers"),
        AgentPersona("history_churn",     0.80, -0.10, 0.10, "history:git_blame_24mo"),
        AgentPersona("test_coverage",     0.80, +0.10, 0.10, "test:branch-coverage"),
        AgentPersona("contract_violator", 0.80, -0.05, 0.10, "contract:fn-sig+callers"),
        AgentPersona("spec_compliance",   0.80,  0.00, 0.10, "spec:docstring+commit-intent"),
    ],
    "uniform_random": [
        AgentPersona("random_a", 0.50, 0.00, 0.30, "random:slices"),
        AgentPersona("random_b", 0.50, 0.00, 0.30, "random:slices"),
        AgentPersona("random_c", 0.50, 0.00, 0.30, "random:slices"),
    ],
}


def run_scenario(
    name: str,
    personas: list[AgentPersona],
    coords_evaluated: list[str],
    labels: list[int],
    seed: int = 42,
) -> dict:
    outputs = simulate_agents(coords_evaluated, labels, personas, seed)
    for o in outputs:
        validate_input(o)

    ranked = aggregate_run(outputs, history_priors=None, w_prior=0.0)
    by_coord = {r["coord"]: r["consensus_score"] for r in ranked}

    # Top-K precision/recall where K = number of known bugs (a useful operating point)
    n_bugs = sum(labels)
    sorted_coords = [r["coord"] for r in ranked]
    top_k_set = set(sorted_coords[:n_bugs])
    tp = sum(1 for c in top_k_set if labels[coords_evaluated.index(c)] == 1)
    precision_at_k = tp / max(1, n_bugs)
    base_rate = sum(labels) / len(labels)
    lift_over_base = precision_at_k - base_rate

    # Per-agent metrics
    per_agent_pairs = []
    for o in outputs:
        f_by_c = {f["coord"]: f["score"] for f in o["findings"]}
        al, asc = [], []
        for c in coords_evaluated:
            if c in f_by_c:
                al.append((c, labels[coords_evaluated.index(c)]))
                asc.append(f_by_c[c])
        per_agent_pairs.append((o["agent_id"], al, asc))

    calib = per_agent_calibration(per_agent_pairs)
    consensus_pred = [by_coord.get(c, 0.0) for c in coords_evaluated]
    consensus_brier = brier_score(consensus_pred, labels)
    consensus_ss = skill_score(consensus_pred, labels)

    # Apply Platt-aggregation: average the Platt-calibrated agent scores
    # in logit space, then sigmoid. This is the "best-case" ensemble.
    a_params = {aid: (calib["agents"][aid]["platt_a"],
                       calib["agents"][aid]["platt_b"])
                for aid in calib["agents"]}
    platt_logits = []
    for c in coords_evaluated:
        per_agent_logits = []
        per_agent_weights = []
        for o in outputs:
            for f in o["findings"]:
                if f["coord"] == c:
                    a, b = a_params[o["agent_id"]]
                    platt_pred = apply_platt(f["score"], a, b)
                    per_agent_logits.append(_logit(platt_pred))
                    per_agent_weights.append(calib["derived_weights"].get(o["agent_id"], 1.0))
        if per_agent_logits:
            avg = sum(l * w for l, w in zip(per_agent_logits, per_agent_weights)) / sum(per_agent_weights)
            platt_logits.append(_sigmoid(avg))
        else:
            platt_logits.append(0.5)
    platt_consensus_ss = skill_score(platt_logits, labels)

    return {
        "scenario": name,
        "n_coords": len(coords_evaluated),
        "n_bugs": n_bugs,
        "consensus_brier": round(consensus_brier, 4),
        "consensus_skill_score": round(consensus_ss, 4),
        "platt_consensus_skill_score": round(platt_consensus_ss, 4),
        "precision_at_k": round(precision_at_k, 4),
        "base_rate": round(base_rate, 4),
        "lift_over_base": round(lift_over_base, 4),
        "per_agent": {
            aid: {
                "brier": r["brier"],
                "skill_score": r["skill_score"],
                "platt_skill_score": r["platt_skill_score"],
                "weight": round(calib["derived_weights"].get(aid, 1.0), 3),
            }
            for aid, r in calib["agents"].items()
        },
        "agreement_band_distribution": {
            b: sum(1 for r in ranked if r["agreement_band"] == b)
            for b in ("unanimous", "majority", "contested", "single")
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--cutoff", required=True)
    ap.add_argument("--app-only", action="store_true", default=True)
    ap.add_argument("--emit", type=Path, default=Path(".consensus-hunter/calibration.json"))
    args = ap.parse_args()

    held = load_held_out_bugs(args.repo, args.cutoff)
    if args.app_only:
        held = [(f, fn) for f, fn in held
                if not f.startswith(("tests/", "docs/"))
                and "/tests/" not in f
                and "test_" not in f]
    print(f"held-out (post-cutoff bug-keyword app code): {len(held)} functions")

    # Build the eval universe: every function we might evaluate.
    # For calibration, we evaluate against a fixed coord set:
    #  - All held-out bug coords (known buggy, label=1)
    #  - Plus a sample of clean coords (label=0) drawn from the same modules
    #    to balance the class distribution.
    from pathlib import Path as P
    import re
    py_files = []
    for p in args.repo.rglob("django/**/*.py"):
        s = str(p)
        if any(part.startswith(".") or part in {"venv", "site-packages",
                                                  "__pycache__", "tests", "migrations"}
               for part in p.parts):
            continue
        py_files.append(p)

    fn_re = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    all_coords: set[tuple[str, str]] = set()
    for p in py_files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        rel = str(p.relative_to(args.repo)).replace("\\", "/")
        for line in text.splitlines():
            m = fn_re.match(line)
            if m:
                all_coords.add((rel, m.group(1)))

    held_keys = set(held)
    buggy_coords = sorted([f"{f}:{fn}" for (f, fn) in all_coords
                           if (f, fn) in held_keys])
    clean_pool = sorted([f"{f}:{fn}" for (f, fn) in all_coords
                         if (f, fn) not in held_keys])
    import random
    rng = random.Random(7)
    # balance: equal count, kept separate so labels line up
    n_each = min(len(buggy_coords), len(clean_pool), 100)
    clean_sample = rng.sample(clean_pool, n_each)

    # Use the union as coords_evaluated, with labels aligned by position
    coords_evaluated = sorted(buggy_coords[:n_each]) + clean_sample
    labels = [1] * n_each + [0] * n_each
    assert len(coords_evaluated) == len(labels) == 2 * n_each
    print(f"eval universe: {len(coords_evaluated)} coords ({n_each} known-buggy, {n_each} known-clean)")

    scenarios = {}
    for name, personas in SCENARIOS.items():
        scenarios[name] = run_scenario(name, personas, coords_evaluated, labels, seed=42)
        s = scenarios[name]
        print(f"  scenario={name:14s}  brier={s['consensus_brier']:.3f}  "
              f"ss={s['consensus_skill_score']:.3f}  "
              f"platt_ss={s['platt_consensus_skill_score']:.3f}  "
              f"prec@k={s['precision_at_k']:.3f} (lift={s['lift_over_base']:+.3f})  "
              f"bands={s['agreement_band_distribution']}")

    payload = {
        "schema": "consensus-hunter/calibration-dashboard/v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo": str(args.repo),
        "cutoff": args.cutoff,
        "eval_universe": {
            "n": len(coords_evaluated),
            "n_buggy": sum(labels),
            "base_rate": round(sum(labels) / len(labels), 4),
        },
        "scenarios": scenarios,
    }
    args.emit.parent.mkdir(parents=True, exist_ok=True)
    with args.emit.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nwrote {args.emit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
