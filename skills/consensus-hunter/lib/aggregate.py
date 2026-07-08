"""
Aggregation: logit-space averaging + per-agent weighting + history prior fusion.

This is the math that turns N independent `AgentDiagnosticOutput`s into a
deterministic per-coordinate `CoordRiskScore`. Three operations:

  1. LOGIT-AVERAGED MEAN — averages probabilities in logit space, which is
     the right space for combining probability estimates. Naive arithmetic
     averaging over-weights confident wrong answers and under-weights
     uncertain right answers (the classic ensemble pathology).

  2. PER-AGENT WEIGHTING — each agent carries a weight derived from its
     held-out Brier score on the calibration set (see `calibrate.py`).
     Uncalibrated agents fall back to uniform weight 1/n.

  3. HISTORY-PRIOR FUSION — convex combination in logit space:
        μ = sigmoid(w_agent · logit_mean + w_prior · logit(p_hist))
     where w_agent + w_prior = 1 (after per-agent weight re-normalization).

The output also carries:
  - agreement_band: 'unanimous' / 'majority' / 'contested' / 'single'
  - logit_variance: sample variance of per-agent logit scores
  - per-agent contributions for transparency

References:
  - Spiess et al., "Calibration and Correctness of LMs for Code," ICSE 2025
    -> argues rescaling is required; we don't trust raw score cardinal claims.
  - Wang et al. (Amazon), "Calibrating Verbalized Probabilities," 2024
    -> verbalized probabilities need an "invert-softmax" trick; we run on
       rank_band (3 levels) which is more robust to this pathology.
  - Mozilla Star Chamber -> variance-as-signal surfaced explicitly.
"""

from __future__ import annotations

import math
from typing import Iterable

# --- Numerical guards --------------------------------------------------------

EPS = 1e-6


def _logit(p: float) -> float:
    """Logit. Clamps to [EPS, 1-EPS] before transform to avoid +/-inf."""
    p_clamped = max(EPS, min(1.0 - EPS, p))
    return math.log(p_clamped / (1.0 - p_clamped))


def _sigmoid(x: float) -> float:
    """Numerically stable sigmoid — avoids exp() of large positives."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


# --- Aggregation primitives --------------------------------------------------


def per_coord_posterior(
    agent_scores: list[tuple[str, float]],
    history_prior: float | None = None,
    w_prior: float = 0.5,
    logit_band_unanimous: float = 1.0,
    logit_band_majority: float = 2.5,
) -> dict:
    """Aggregate N agent scores for one coordinate into a CoordRiskScore.

    Args:
        agent_scores: list of (agent_id, score) tuples. Score in [0,1].
            Weights are read from the calibrate.py weights; if not provided
            uniformly, weights are 1/n.
        history_prior: optional p_hist in [0,1] from prior.py.
        w_prior: 0..1 weight given to the history prior vs the agents. The
            agent share is (1 - w_prior).
        logit_band_unanimous: logit-space radius for "unanimous" band.
        logit_band_majority: logit-space radius for "majority" band.

    Returns:
        dict matching COORD_SCHEMA. Aggregation is deterministic given
        the same inputs.
    """
    if not agent_scores:
        raise ValueError("agent_scores must be non-empty")

    n_agents = len(agent_scores)
    logits = [_logit(s) for _, s in agent_scores]
    mean_logit = sum(logits) / n_agents
    var_logit = sum((l - mean_logit) ** 2 for l in logits) / n_agents

    # Weighted logit-sum. Per-agent Brier-weighted variant lives in
    # `calibrate.py`; uniform 1/n when agent_weights not supplied.
    if history_prior is not None and w_prior > 0.0:
        agent_share = 1.0 - w_prior
        fused_logit = agent_share * mean_logit + w_prior * _logit(history_prior)
    else:
        fused_logit = mean_logit

    consensus = _sigmoid(fused_logit)

    # Agreement band
    if n_agents == 1:
        band = "single"
    else:
        max_dev = max(abs(l - mean_logit) for l in logits)
        if max_dev <= logit_band_unanimous:
            band = "unanimous"
        elif max_dev <= logit_band_majority:
            band = "majority"
        else:
            band = "contested"

    return {
        "consensus_score": round(consensus, 6),
        "agreement_band": band,
        "n_agents_reported": n_agents,
        "logit_variance": round(var_logit, 6),
        "_mean_logit": round(mean_logit, 6),
    }


def aggregate_run(
    agent_outputs: list[dict],
    history_priors: dict[str, float] | None = None,
    agent_weights: dict[str, float] | None = None,
    w_prior: float = 0.5,
) -> list[dict]:
    """Aggregate a complete run from N independent AgentDiagnosticOutputs.

    Args:
        agent_outputs: list of validated AgentDiagnosticOutput dicts.
        history_priors: optional {coord -> p_hist} from prior.py.
        agent_weights: optional {agent_id -> weight} from calibrate.py.
            Defaults to uniform. Weights are renormalized to sum to
            n_agents so the math is comparable to uniform.
        w_prior: weight given to history prior (0 disables priors).

    Returns:
        list of CoordRiskScore dicts, ranked by consensus_score desc.
    """
    if history_priors is None:
        history_priors = {}

    # Group findings by coord across agents
    by_coord: dict[str, list[tuple[str, float, str]]] = {}
    for output in agent_outputs:
        aid = output["agent_id"]
        for f in output["findings"]:
            coord = f["coord"]
            by_coord.setdefault(coord, []).append((aid, f["score"], f.get("rank_band", "MED")))

    out = []
    for coord, reports in by_coord.items():
        # Apply per-agent weights (renormalized to sum n)
        if agent_weights:
            total_w = sum(agent_weights.get(aid, 1.0) for aid, _, _ in reports)
            weighted = [
                (aid, score * (agent_weights.get(aid, 1.0) / (total_w / len(reports))))
                for aid, score, _ in reports
            ]
        else:
            weighted = [(aid, score) for aid, score, _ in reports]

        # Re-clamp after weighting transform
        weighted = [(aid, max(EPS, min(1.0 - EPS, s))) for aid, s in weighted]

        agg = per_coord_posterior(
            agent_scores=weighted,
            history_prior=history_priors.get(coord),
            w_prior=w_prior if coord in history_priors else 0.0,
        )

        out.append({
            "coord": coord,
            **agg,
            "history_prior_p": history_priors.get(coord),
            "contributing_agents": [
                {
                    "agent_id": aid,
                    "score": s,
                    "rank_band": rb,
                }
                for aid, s, rb in reports
            ],
        })

    out.sort(key=lambda r: -r["consensus_score"])
    return out


def rank_bands(ranked_coords: list[dict]) -> dict[str, list[str]]:
    """Bucket ranked coords into HIGH / MED / LOW bands by quantile, for
    the archived heatmap report."""
    n = len(ranked_coords)
    if n == 0:
        return {"HIGH": [], "MED": [], "LOW": []}
    high_cut = max(1, n // 5)
    med_cut = max(high_cut + 1, n // 2)
    return {
        "HIGH": [r["coord"] for r in ranked_coords[:high_cut]],
        "MED": [r["coord"] for r in ranked_coords[high_cut:med_cut]],
        "LOW": [r["coord"] for r in ranked_coords[med_cut:]],
    }
