"""
Calibration harness.

The skill's headline claim is that LLM-issued numeric scores can be turned
into actionable per-coordinate risk. That claim is meaningless without
measurement. This module provides the measurement:

  - Brier score per agent on a labeled held-out set
  - Skill score (Brier - base_rate_brier) per agent
  - Platt scaling parameters (slope + intercept) for monotone rescaling
  - Per-agent weight derivation from Brier

Held-out data shape: list of (coord_id, known_buggy_0_or_1, agent_score)
triples. Real source is bugs known after a knowledge-cutoff timestamp.

Calibration targets (per the design doc):
  1. django/django via SWE-Bench Verified gold patches
  2. Then postgres/postgres via CVEfixes + commit-Fixes tags

For initial development, the tests/ directory ships a synthetic held-out
fixture so the harness is testable without external data.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable

EPS = 1e-6


# --- Metrics -----------------------------------------------------------------


def brier_score(predictions: list[float], labels: list[int]) -> float:
    """Mean squared error between predicted probability and binary label."""
    if len(predictions) != len(labels):
        raise ValueError("predictions and labels must align")
    if not predictions:
        return 0.0
    return sum((p - y) ** 2 for p, y in zip(predictions, labels)) / len(predictions)


def base_rate_brier(labels: list[int]) -> float:
    """Brier score of the constant predictor P(y=1) = base_rate."""
    if not labels:
        return 0.0
    base = sum(labels) / len(labels)
    return sum((base - y) ** 2 for y in labels) / len(labels)


def skill_score(predictions: list[float], labels: list[int]) -> float:
    """Skill score = 1 - (Brier / base_rate_brier). 1.0 = perfect; 0 = base rate;
    negative = worse than constant. The metric Spiess et al. 2025 recommends
    over ECE for this domain."""
    bb = base_rate_brier(labels)
    bs = brier_score(predictions, labels)
    if bb < EPS:
        return 0.0
    return 1.0 - (bs / bb)


# --- Platt scaling -----------------------------------------------------------


def fit_platt(
    predictions: list[float], labels: list[int], lr: float = 0.5, epochs: int = 200
) -> tuple[float, float]:
    """Fit Platt scaling: logit(P_calibrated) = a * logit(P_raw) + b
    via batch gradient descent on the binary cross-entropy loss.

    Returns (a, b). The Platt transform is monotone — does not change
    ranking, only rescaling. Per Spiess et al., this lifts Skill Score from
    near-zero on raw LLM scores to ~0.05–0.15 (the only published number).

    v1 implements this from scratch because pulling scikit-learn as a
    hard dependency for an in-skill library is bad form; pure-stdlib
    gradient descent on logit space is <40 LOC.
    """
    if not predictions:
        return 1.0, 0.0
    a, b = 1.0, 0.0
    n = len(predictions)
    for _ in range(epochs):
        # Forward pass
        grad_a = 0.0
        grad_b = 0.0
        for p, y in zip(predictions, labels):
            z = max(EPS, min(1.0 - EPS, p))
            logit_p = math.log(z / (1.0 - z))
            cal_logit = a * logit_p + b
            # sigmoid
            sig = 1.0 / (1.0 + math.exp(-cal_logit))
            err = sig - y
            grad_a += err * logit_p
            grad_b += err
        a -= lr * grad_a / n
        b -= lr * grad_b / n
    return a, b


def apply_platt(p: float, a: float, b: float) -> float:
    """Apply Platt parameters to a raw score."""
    z = max(EPS, min(1.0 - EPS, p))
    logit_p = math.log(z / (1.0 - z))
    cal_logit = a * logit_p + b
    return 1.0 / (1.0 + math.exp(-cal_logit))


# --- Agent weighting --------------------------------------------------------


def derive_weights(
    agent_brier: dict[str, float],
    labels_brier: float,
    min_weight: float = 0.5,
) -> dict[str, float]:
    """Per-agent weight from inverse-Brier.

    Higher weight = better calibrated. Uncalibrated or worse-than-base-rate
    agents fall back to `min_weight` * their share. Weight is renormalized
    to sum to len(agents) so the arithmetic is comparable to uniform 1/n.
    """
    if not agent_brier:
        return {}
    inv = {}
    for aid, b in agent_brier.items():
        # If agent is at-or-worse than base rate, give minimum weight.
        if b >= labels_brier * 1.5:
            inv[aid] = min_weight
        else:
            # Inverse scaling; perfect (brier ~0) -> inv ~ 1/baseline.
            inv[aid] = 1.0 / max(b, EPS)
    total = sum(inv.values())
    n = len(inv)
    return {aid: (v / total) * n for aid, v in inv.items()}


def per_agent_calibration(
    runs: list[tuple[str, list[tuple[str, int]], list[float]]],
) -> dict:
    """Score per-agent on a labeled held-out set.

    Args:
        runs: list of (agent_id, [(coord, known_label)], [agent_score]) triples.
              The lists for coord and score must align.

    Returns:
        dict with per-agent brier, skill score, platt (a, b), and overall
        derived weight.
    """
    per_agent: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for agent_id, labeled, scores in runs:
        if len(labeled) != len(scores):
            raise ValueError(f"{agent_id}: labeled/score length mismatch")
        for (coord, y), s in zip(labeled, scores):
            per_agent[agent_id].append((y, s))

    out: dict = {"agents": {}, "global": {}}
    all_labels: list[int] = []
    for agent_id, pairs in per_agent.items():
        labels = [y for y, _ in pairs]
        preds = [s for _, s in pairs]
        bs = brier_score(preds, labels)
        ss = skill_score(preds, labels)
        a, b = fit_platt(preds, labels)
        platt_preds = [apply_platt(s, a, b) for s in preds]
        platt_ss = skill_score(platt_preds, labels)
        out["agents"][agent_id] = {
            "n": len(labels),
            "brier": round(bs, 4),
            "skill_score": round(ss, 4),
            "platt_a": round(a, 4),
            "platt_b": round(b, 4),
            "platt_skill_score": round(platt_ss, 4),
        }
        all_labels.extend(labels)

    out["global"] = {
        "n_total": len(all_labels),
        "base_rate": round(sum(all_labels) / max(1, len(all_labels)), 4),
        "base_rate_brier": round(base_rate_brier(all_labels), 4),
    }

    agent_brier = {a: r["brier"] for a, r in out["agents"].items()}
    out["derived_weights"] = derive_weights(
        agent_brier, out["global"]["base_rate_brier"]
    )
    return out
