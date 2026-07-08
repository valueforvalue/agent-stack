"""Calibration invariants — Brier, Platt, weights."""

import random
import unittest

from lib.calibrate import (
    brier_score, base_rate_brier, skill_score,
    fit_platt, apply_platt, derive_weights, per_agent_calibration,
)


class TestBrierAndSkill(unittest.TestCase):
    def test_perfect_predictor(self):
        labels = [1, 1, 0, 0, 1]
        predictions = [1.0, 1.0, 0.0, 0.0, 1.0]
        self.assertAlmostEqual(brier_score(predictions, labels), 0.0, places=6)
        # perfect score
        ss = skill_score(predictions, labels)
        self.assertAlmostEqual(ss, 1.0, places=6)

    def test_baseline_predictor_is_zero_skill(self):
        labels = [1, 0, 0, 0, 0]
        predictions = [0.2] * 5  # matches base rate
        ss = skill_score(predictions, labels)
        self.assertAlmostEqual(ss, 0.0, places=6)

    def test_worse_than_baseline_is_negative(self):
        labels = [1, 0, 0, 0, 0]
        predictions = [0.8] * 5  # always says bug, but base rate is 20%
        ss = skill_score(predictions, labels)
        self.assertLess(ss, 0)


class TestPlattScaling(unittest.TestCase):
    def test_platt_preserves_ranking(self):
        random.seed(1)
        labels = [random.choice([0, 1]) for _ in range(50)]
        predictions = [random.random() for _ in range(50)]
        a, b = fit_platt(predictions, labels)
        # Apply Platt; the relative order must not change (monotone transform).
        ranked_pairs = sorted(
            zip(predictions, [apply_platt(p, a, b) for p in predictions])
        )
        ranked_preds = [p for p, _ in ranked_pairs]
        ranked_cal = [c for _, c in ranked_pairs]
        # If monotone: cal[i] <= cal[i+1] for all i.
        for i in range(len(ranked_cal) - 1):
            self.assertLessEqual(ranked_cal[i], ranked_cal[i + 1] + 1e-9)

    def test_platt_lifts_skill_score_on_systematically_miscalibrated(self):
        random.seed(2)
        labels = [1 if random.random() < 0.3 else 0 for _ in range(80)]
        # Predictions uniformly drawn from 0..1 — uncorrelated with truth.
        predictions = [random.random() for _ in range(80)]
        raw_ss = skill_score(predictions, labels)
        a, b = fit_platt(predictions, labels)
        cal = [apply_platt(p, a, b) for p in predictions]
        cal_ss = skill_score(cal, labels)
        # Monotone transform shouldn't hurt; either stays equal or improves.
        self.assertGreaterEqual(cal_ss, raw_ss - 1e-6)


class TestDeriveWeights(unittest.TestCase):
    def test_better_agent_gets_higher_weight(self):
        # Agent A: Brier 0.10 (good)
        # Agent B: Brier 0.40 (worse-than-baseline)
        agent_brier = {"A": 0.10, "B": 0.40}
        baseline = 0.20
        w = derive_weights(agent_brier, baseline)
        self.assertGreater(w["A"], w["B"])

    def test_weights_sum_to_n(self):
        agent_brier = {"A": 0.10, "B": 0.20, "C": 0.30}
        w = derive_weights(agent_brier, labels_brier=0.20)
        self.assertAlmostEqual(sum(w.values()), 3, places=6)


class TestPerAgentCalibration(unittest.TestCase):
    def test_full_pipeline_emits_all_metrics(self):
        random.seed(3)
        labels = [1 if random.random() < 0.25 else 0 for _ in range(60)]
        preds_a = [random.random() for _ in range(60)]
        preds_b = [random.random() for _ in range(60)]
        coords = [(f"f{i}.py:g", y) for i, y in enumerate(labels)]
        runs = [
            ("a", coords, preds_a),
            ("b", coords, preds_b),
        ]
        out = per_agent_calibration(runs)
        self.assertIn("agents", out)
        self.assertIn("global", out)
        self.assertIn("derived_weights", out)
        self.assertIn("brier", out["agents"]["a"])
        self.assertIn("platt_a", out["agents"]["a"])
        self.assertEqual(out["global"]["n_total"], 120)
        # derived_weights is a dict of agent_id -> weight, sum should be n
        self.assertAlmostEqual(
            sum(out["derived_weights"].values()), 2, places=4
        )


if __name__ == "__main__":
    unittest.main()
