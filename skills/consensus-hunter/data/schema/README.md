# Schema fixtures for consensus-hunter

Two JSON files in this directory:

  - `input.example.json`   — example of the input each LLM agent emits
                              (matches `lib/schema.py::INPUT_SCHEMA`)
  - `coord.example.json`   — example of the output the aggregator emits
                              per (file:function) coordinate
                              (matches `lib/schema.py::COORD_SCHEMA`)

These fixtures are the canonical examples used in the SKILL.md quick
start, in the integration tests, and in the calibration harness.
