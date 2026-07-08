"""Real-agent calibration runner for the django@2020-06-01 surface.

Loads the 5 captured agent JSON files, runs the aggregator, computes Brier
+ Skill Score + per-agent metrics + agreement-band distribution against the
held-out ground-truth labels in eval_coords.json.

Compared to the simulated version, this one:
  - Uses real captured agent outputs (.consensus-hunter/captured/agent_*.json)
  - Uses real held-out labels from post-cutoff django git history
  - Computes per-agent calibration metrics
  - Writes a calibration report

Usage:
    python scripts/run_real_agent_calibration.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from calibrate_runner import build_label_set  # noqa: E402
from lib.aggregate import aggregate_run  # noqa: E402
from lib.calibrate import (  # noqa: E402
    brier_score, skill_score, per_agent_calibration,
)


CAPTURED = Path(".consensus-hunter/captured")
EVAL = Path(".consensus-hunter/eval_coords.json")
EMIT = Path(".consensus-hunter/calibration.json")


def main() -> int:
    if not EVAL.exists():
        print(f"missing: {EVAL}")
        return 2

    manifest = json.load(EVAL.open())
    eval_coords = manifest["coords"]
    coords_evaluated = [c["coord"] for c in eval_coords]
    labels = [c["label"] for c in eval_coords]
    n_bugs = sum(labels)
    base_rate = n_bugs / max(1, len(labels))

    # Load all captured agent outputs
    outputs = []
    for p in sorted(CAPTURED.glob("agent_*.json")):
        obj = json.load(p.open())
        outputs.append(obj)
    if not outputs:
        print("no captured agent outputs in", CAPTURED)
        return 2
    print(f"loaded {len(outputs)} agent output files")

    # Aggregate
    ranked = aggregate_run(outputs, history_priors=None, w_prior=0.0)
    by_coord = {r["coord"]: r["consensus_score"] for r in ranked}

    consensus_pred = [by_coord.get(c, 0.5) for c in coords_evaluated]
    consensus_brier = brier_score(consensus_pred, labels)
    consensus_ss = skill_score(consensus_pred, labels)

    # Precision@K where K = #bugs
    sorted_coords = [r["coord"] for r in ranked if r["coord"] in set(coords_evaluated)]
    top_k = sorted_coords[:n_bugs]
    top_k_set = set(top_k)
    tp = sum(1 for c in top_k_set if labels[coords_evaluated.index(c)] == 1)
    prec_at_k = tp / max(1, n_bugs)

    # Per-agent calibration
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

    # Naive-mean comparator (no logit space): arithmetic mean over agents
    naive_pred = []
    for c in coords_evaluated:
        per_agent = []
        for o in outputs:
            for f in o["findings"]:
                if f["coord"] == c:
                    per_agent.append(f["score"])
        naive_pred.append(sum(per_agent) / max(1, len(per_agent)))
    naive_brier = brier_score(naive_pred, labels)
    naive_ss = skill_score(naive_pred, labels)

    report = {
        "schema": "consensus-hunter/calibration-real-agent/v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cutoff": manifest["cutoff"],
        "cutoff_sha": manifest["cutoff_sha"],
        "eval_universe": {
            "n": len(coords_evaluated),
            "n_buggy": n_bugs,
            "base_rate": round(base_rate, 4),
        },
        "consensus": {
            "logit_averaged_brier": round(consensus_brier, 4),
            "logit_averaged_skill_score": round(consensus_ss, 4),
            "naive_arithmetic_mean_brier": round(naive_brier, 4),
            "naive_arithmetic_mean_skill_score": round(naive_ss, 4),
            "precision_at_k": round(prec_at_k, 4),
            "lift_over_base": round(prec_at_k - base_rate, 4),
        },
        "per_agent": {
            aid: {
                "brier": r["brier"],
                "skill_score": r["skill_score"],
                "platt_skill_score": r["platt_skill_score"],
                "derived_weight": round(calib["derived_weights"].get(aid, 1.0), 4),
            }
            for aid, r in calib["agents"].items()
        },
        "agreement_band_distribution": {
            b: sum(1 for r in ranked if r["agreement_band"] == b)
            for b in ("unanimous", "majority", "contested", "single")
        },
        "top_5_highest_consensus": [
            {"coord": r["coord"], "score": r["consensus_score"],
             "band": r["agreement_band"], "label": labels[coords_evaluated.index(r["coord"])]}
            for r in ranked[:5] if r["coord"] in set(coords_evaluated)
        ],
        "top_5_lowest_consensus": [
            {"coord": r["coord"], "score": r["consensus_score"],
             "band": r["agreement_band"], "label": labels[coords_evaluated.index(r["coord"])]}
            for r in ranked[-5:] if r["coord"] in set(coords_evaluated)
        ],
    }

    EMIT.parent.mkdir(parents=True, exist_ok=True)
    with EMIT.open("w") as out:
        json.dump(report, out, indent=2)

    print(f"\n=== REAL-AGENT CALIBRATION RESULTS ===")
    print(f"Eval universe: {len(coords_evaluated)} coords ({n_bugs} known-buggy, {len(coords_evaluated)-n_bugs} clean)")
    print(f"Base rate: {base_rate:.2%}")
    print()
    print("Consensus metrics:")
    print(f"  logit-averaged Brier        = {consensus_brier:.4f}")
    print(f"  logit-averaged Skill Score  = {consensus_ss:.4f}")
    print(f"  naive-arithmetic Brier      = {naive_brier:.4f}")
    print(f"  naive-arithmetic Skill Score= {naive_ss:.4f}")
    print(f"  precision@K                = {prec_at_k:.4f}")
    print(f"  lift over base             = {prec_at_k - base_rate:+.4f}")
    print()
    print("Per-agent metrics:")
    print(f"  {'agent':<24}  {'brier':>7}  {'SS':>6}  {'platt_ss':>8}  {'weight':>7}")
    for aid, r in calib["agents"].items():
        print(f"  {aid:<24}  {r['brier']:>7.4f}  {r['skill_score']:>+6.4f}  {r['platt_skill_score']:>+8.4f}  "
              f"{calib['derived_weights'].get(aid, 1.0):>7.4f}")
    print()
    print(f"Agreement band distribution: {report['agreement_band_distribution']}")
    print()
    print(f"Top 5 by consensus:")
    for x in report["top_5_highest_consensus"]:
        bug = "BUGGY" if x["label"] == 1 else "clean"
        print(f"  {x['coord']:65s} score={x['score']:.3f}  band={x['band']:<10s}  label={bug}")
    print()
    print(f"\nwrote {EMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
