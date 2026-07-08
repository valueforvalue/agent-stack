"""Aggregation invariants — math sanity."""

import math
import unittest

from lib.aggregate import (
    _logit, _sigmoid, per_coord_posterior, aggregate_run, rank_bands,
)


class TestLogitSigmoidRoundtrip(unittest.TestCase):
    def test_logit_sigmoid_roundtrip(self):
        # Invertibility: sigmoid(logit(p)) == p.
        for p in [0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99]:
            self.assertAlmostEqual(_sigmoid(_logit(p)), p, places=6)

    def test_logit_edge_clamping(self):
        # Should not blow up at extremes — both must stay finite.
        self.assertTrue(math.isfinite(_logit(0.0)))
        self.assertTrue(math.isfinite(_logit(1.0)))
        self.assertTrue(math.isfinite(_sigmoid(1e9)))
        self.assertTrue(math.isfinite(_sigmoid(-1e9)))


class TestPerCoordPosterior(unittest.TestCase):
    def test_single_agent_unanimous(self):
        out = per_coord_posterior([("a", 0.7)])
        self.assertEqual(out["agreement_band"], "single")
        self.assertEqual(out["n_agents_reported"], 1)
        # No prior, no other agents -> raw logit mean, single -> "single" band
        self.assertGreater(out["consensus_score"], 0.5)

    def test_three_close_agents_unanimous(self):
        out = per_coord_posterior([("a", 0.6), ("b", 0.62), ("c", 0.58)])
        self.assertEqual(out["agreement_band"], "unanimous")
        self.assertLess(out["logit_variance"], 0.01)

    def test_three_disagreeing_agents_contested(self):
        out = per_coord_posterior([("a", 0.05), ("b", 0.5), ("c", 0.95)])
        self.assertEqual(out["agreement_band"], "contested")
        self.assertGreater(out["logit_variance"], 0.1)

    def test_history_prior_lifts_score(self):
        # Without prior, three agents at 0.55 -> mean near 0.55.
        # With strong prior (0.95), the score should pull up significantly.
        no_prior = per_coord_posterior([("a", 0.55), ("b", 0.55), ("c", 0.55)])
        with_prior = per_coord_posterior(
            [("a", 0.55), ("b", 0.55), ("c", 0.55)],
            history_prior=0.95,
            w_prior=0.5,
        )
        self.assertGreater(with_prior["consensus_score"], no_prior["consensus_score"])

    def test_logit_averaging_pulls_extreme(self):
        # Under EQUAL weights, logit-space averaging weights confident
        # predictions more than plain arithmetic does. When two agents
        # confidently say 0.99 and one says 0.01, logit averaging lands at
        # sigmoid(logit_avg) = sigmoid((4.595+4.595-4.595)/3) ~= 0.822,
        # whereas plain arithmetic would be 0.663. The right space is the
        # one where the central tendency of a calibrated ensemble reflects
        # confidence honestly.
        out = per_coord_posterior([("a", 0.99), ("b", 0.99), ("c", 0.01)])
        self.assertAlmostEqual(out["consensus_score"], 0.822, places=2)

    def test_logit_weighted_pulls_extreme_more_than_plain_mean(self):
        # With one low-trust agent (weight 0.2) and two high-trust agents
        # (weight 1), logit-space weighting should be more sensitive to the
        # high-trust majority than plain arithmetic weighting.
        #
        # Plain arithmetic weighted: (0.99 + 0.99 + 0.01*0.2)/2.2 = 0.909
        # Logit weighted (renormalized so weights sum to n):
        #   w' = w * (n / sum(w))
        #   mean_logit = sum(w'*logit(s)) / n
        #   = sigmoid(...) ~= 0.977
        # The logit number should be HIGHER than the plain-arithmetic number —
        # confirming that logit-space weighting respects the confidence
        # asymmetry the way the arithmetic mean does not.
        from lib.aggregate import aggregate_run
        out_a = {
            "agent_id": "high_a",
            "findings": [{
                "coord": "x.py:f", "score": 0.99, "rank_band": "HIGH",
                "evidence_quote": "ev", "reasoning": "r" * 25,
            }],
        }
        out_b = {
            "agent_id": "high_b",
            "findings": [{
                "coord": "x.py:f", "score": 0.99, "rank_band": "HIGH",
                "evidence_quote": "ev", "reasoning": "r" * 25,
            }],
        }
        out_c = {
            "agent_id": "low_trust",
            "findings": [{
                "coord": "x.py:f", "score": 0.01, "rank_band": "LOW",
                "evidence_quote": "ev", "reasoning": "r" * 25,
            }],
        }
        weights = {"high_a": 1.0, "high_b": 1.0, "low_trust": 0.2}
        ranked = aggregate_run(
            [out_a, out_b, out_c], agent_weights=weights, w_prior=0.0,
        )
        # Compare to the analytic plain-arithmetic weighted expectation.
        plain_weighted = (0.99 * 1.0 + 0.99 * 1.0 + 0.01 * 0.2) / (1.0 + 1.0 + 0.2)
        # Logit-space weighted should be STRICTLY HIGHER when high-trust agents
        # are confident and the low-trust agent is unconfident in the other direction.
        self.assertGreater(ranked[0]["consensus_score"], plain_weighted)
        self.assertLess(ranked[0]["consensus_score"], 1.0)


class TestAggregateRun(unittest.TestCase):
    def test_ranks_by_consensus_score_desc(self):
        out_a = {
            "agent_id": "a",
            "findings": [
                {"coord": "x.py:f", "score": 0.9, "rank_band": "HIGH",
                 "evidence_quote": "ev", "reasoning": "r" * 25},
            ],
        }
        out_b = {
            "agent_id": "b",
            "findings": [
                {"coord": "x.py:f", "score": 0.8, "rank_band": "HIGH",
                 "evidence_quote": "ev", "reasoning": "r" * 25},
                {"coord": "y.py:g", "score": 0.3, "rank_band": "LOW",
                 "evidence_quote": "ev", "reasoning": "r" * 25},
            ],
        }
        ranked = aggregate_run([out_a, out_b])
        # x.py:f should outrank y.py:g
        self.assertEqual(ranked[0]["coord"], "x.py:f")
        self.assertEqual(ranked[1]["coord"], "y.py:g")

    def test_coord_only_reported_by_one_agent_lands_single_band(self):
        out_a = {
            "agent_id": "a",
            "findings": [
                {"coord": "only_a.py:f", "score": 0.7, "rank_band": "MED",
                 "evidence_quote": "ev", "reasoning": "r" * 25},
            ],
        }
        out_b = {
            "agent_id": "b", "findings": [],
        }
        ranked = aggregate_run([out_a, out_b])
        self.assertEqual(ranked[0]["agreement_band"], "single")
        self.assertEqual(ranked[0]["n_agents_reported"], 1)

    def test_history_prior_fuses_per_coord(self):
        out_a = {
            "agent_id": "a",
            "findings": [
                {"coord": "x.py:f", "score": 0.5, "rank_band": "MED",
                 "evidence_quote": "ev", "reasoning": "r" * 25},
            ],
        }
        priors = {"x.py:f": 0.95}
        ranked = aggregate_run([out_a], history_priors=priors, w_prior=0.5)
        self.assertEqual(ranked[0]["history_prior_p"], 0.95)
        # 0.5 agent pulled toward 0.95 by 50% -> somewhere north of 0.5
        self.assertGreater(ranked[0]["consensus_score"], 0.7)


class TestRankBands(unittest.TestCase):
    def test_bucketing_by_quintile(self):
        ranked = [
            {"coord": f"f{i}.py:g", "consensus_score": 1.0 - i * 0.01}
            for i in range(10)
        ]
        bands = rank_bands(ranked)
        # 5 in HIGH (top 20%), 5 in MED/LOW remainder
        self.assertEqual(len(bands["HIGH"]), 2)
        self.assertEqual(len(bands["MED"]), 3)
        self.assertEqual(len(bands["LOW"]), 5)


if __name__ == "__main__":
    unittest.main()
