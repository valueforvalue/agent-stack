"""Schema shape tests — input/output validation."""

import unittest

from lib.schema import validate_input, INPUT_SCHEMA, COORD_SCHEMA


class TestInputSchemaShape(unittest.TestCase):
    def test_required_keys_present(self):
        for k in ("agent_id", "findings"):
            self.assertIn(k, INPUT_SCHEMA["required"])

    def test_findings_required_keys(self):
        item = INPUT_SCHEMA["properties"]["findings"]["items"]
        for k in ("coord", "score", "rank_band", "evidence_quote", "reasoning"):
            self.assertIn(k, item["required"])

    def test_rank_band_enum(self):
        item = INPUT_SCHEMA["properties"]["findings"]["items"]
        enum = item["properties"]["rank_band"]["enum"]
        self.assertEqual(set(enum), {"HIGH", "MED", "LOW"})

    def test_score_bounded(self):
        item = INPUT_SCHEMA["properties"]["findings"]["items"]
        prop = item["properties"]["score"]
        self.assertEqual(prop["minimum"], 0.0)
        self.assertEqual(prop["maximum"], 1.0)


class TestCoordSchemaShape(unittest.TestCase):
    def test_required_keys_present(self):
        for k in ("coord", "consensus_score", "agreement_band",
                  "n_agents_reported", "logit_variance"):
            self.assertIn(k, COORD_SCHEMA["required"])

    def test_agreement_band_enum(self):
        prop = COORD_SCHEMA["properties"]["agreement_band"]
        self.assertEqual(
            set(prop["enum"]),
            {"unanimous", "majority", "contested", "single"},
        )


class TestValidateInput(unittest.TestCase):
    def _good(self):
        return {
            "agent_id": "test_agent",
            "findings": [{
                "coord": "x.py:f",
                "score": 0.7,
                "rank_band": "MED",
                "evidence_quote": "line of code",
                "reasoning": "here is my reasoning " * 3,
            }],
        }

    def test_valid_input_passes(self):
        validate_input(self._good())  # should not raise

    def test_missing_agent_id(self):
        bad = self._good()
        del bad["agent_id"]
        with self.assertRaises(ValueError):
            validate_input(bad)

    def test_missing_finding_key(self):
        bad = self._good()
        del bad["findings"][0]["rank_band"]
        with self.assertRaises(ValueError):
            validate_input(bad)

    def test_out_of_range_score(self):
        bad = self._good()
        bad["findings"][0]["score"] = 1.5
        with self.assertRaises(ValueError):
            validate_input(bad)

    def test_bad_rank_band(self):
        bad = self._good()
        bad["findings"][0]["rank_band"] = "MAYBE"
        with self.assertRaises(ValueError):
            validate_input(bad)


if __name__ == "__main__":
    unittest.main()
