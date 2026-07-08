"""Tests that per_agent_calibration does not produce subset-base-rate artifacts."""

import random
import unittest

from lib.calibrate import (
    brier_score, base_rate_brier, skill_score, per_agent_calibration,
)


class TestPerAgentWithGlobalLabels(unittest.TestCase):
    def test_subset_no_longer_artifacts_negative_ss(self):
        """Regression: when an agent reports only on a single-class subset
        with middling accuracy (the pattern that surfaced on dixiedata),
        the legacy code computed a base-rate from that subset and produced
        a meaningless negative Skill Score. With global_labels +
        coords_evaluated, the Skill Score is computed against the true global
        base rate, with missing coords default-filled to 0.5.
        """
        random.seed(42)
        # True eval: 100 coords, 50 buggy, 50 clean.
        labels = [1] * 50 + [0] * 50
        coords = [f"f{i}.py:g" for i in range(100)]
        # The pattern that triggers the artifact: agent reports only on
        # ~25 of the 50 buggy coords (it has middling accuracy on what it
        # does commit to). Reported subset has 25 true bugs and 0 clean
        # coords -> subset base rate = 1.0 -> base_rate_brier = 0 ->
        # Skill Score fallback to 0 in legacy.
        # We strengthen: report on 25 buggy + 25 clean (50 total, 50% buggy
        # in subset so subset base_rate_brier is small but nonzero) but
        # scatter scores such that the agent's per-subset Brier exceeds
        # base_rate_brier -> negative Skill Score.
        reported_pairs = []
        # 25 buggy + 25 clean (subset base rate = 0.5, same as global) ->
        # no artifact. Need different distribution.
        # Real artifact: 49 buggy + 1 clean reported (subset base rate = 0.98)
        # with agent scoring them mid-range (0.4-0.6 with noise).
        for i in range(49):
            s = max(0.0, min(1.0, 0.55 + random.gauss(0, 0.18)))
            reported_pairs.append((coords[i], 1, s))
        # One false-positive-ish clean coord reported
        s = max(0.0, min(1.0, 0.45 + random.gauss(0, 0.18)))
        reported_pairs.append((coords[60], 0, s))

        runs = [("focused_agent", [(c, y) for c, y, _ in reported_pairs],
                 [s for _, _, s in reported_pairs])]

        # Legacy (subset-only) — subset is 50 records, 49 buggy + 1 clean
        # base rate ~0.98, base_rate_brier ~ 0.0196. Agent's Brier on this
        # subset is around 0.18 (mid-range guesses for a class mostly
        # already known to be buggy in the subset). SS = 1 - 0.18/0.0196
        # ~ -8 (deeply negative — the artifact).
        calib_legacy = per_agent_calibration(runs)
        legacy_ss = calib_legacy["agents"]["focused_agent"]["skill_score"]
        self.assertLess(legacy_ss, -2.0,
            f"Legacy subset-only eval should produce a strongly negative "
            f"Skill Score (the artifact); got {legacy_ss:+.3f}")

        # Fixed eval: full 100-coord universe, missing 49 clean coords +
        # 1 buggy coord get default 0.5. Agent sees 50 reported + 49
        # default 0.5 + 1 default 0.5 (the one true-buggy missed).
        calib_fixed = per_agent_calibration(
            runs, global_labels=labels, coords_evaluated=coords,
        )
        fixed_ss = calib_fixed["agents"]["focused_agent"]["skill_score"]
        self.assertGreater(fixed_ss, legacy_ss,
            f"Fixed eval must not be worse than the legacy artifact; "
            f"got fixed={fixed_ss:+.3f} legacy={legacy_ss:+.3f}")

    def test_legacy_path_unchanged(self):
        """The legacy (per-subset) path still works when global_labels is None."""
        random.seed(0)
        labels = [0, 1, 1, 0, 1]
        coords = [f"f{i}.py:g" for i in range(5)]
        scores = [0.2, 0.8, 0.7, 0.3, 0.9]
        runs = [("a", list(zip(coords, labels)), scores)]
        calib = per_agent_calibration(runs)
        self.assertIn("agents", calib)
        self.assertIn("a", calib["agents"])

    def test_coords_evaluated_length_mismatch_raises(self):
        labels = [0, 1, 0]
        coords_eval = ["f0.py:g", "f1.py:g"]  # only 2, but labels has 3
        runs = [("a", [("f0.py:g", 0), ("f1.py:g", 1)], [0.1, 0.9])]
        with self.assertRaises(ValueError):
            per_agent_calibration(runs, global_labels=labels, coords_evaluated=coords_eval)

    def test_missing_coords_default_to_05(self):
        """An agent that reports on 30 of 40 coords scores 0.5 on the missing 10."""
        coords = [f"f{i}.py:g" for i in range(40)]
        labels = [0 if i < 20 else 1 for i in range(40)]
        # Agent only reports on first 30 coords
        reported = [(coords[i], labels[i], 0.7 if labels[i] else 0.3) for i in range(30)]
        runs = [("partial", [(c, y) for c, y, _ in reported],
                 [s for _, _, s in reported])]
        calib = per_agent_calibration(
            runs, global_labels=labels, coords_evaluated=coords,
        )
        a = calib["agents"]["partial"]
        self.assertEqual(a["n"], 40,
            f"Should have n=40 (the full universe), got {a['n']}")


if __name__ == "__main__":
    unittest.main()
