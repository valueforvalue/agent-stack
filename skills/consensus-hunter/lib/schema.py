"""
JSON schemas for the consensus-hunter skill.

The agent-side LLM emits one `AgentDiagnosticOutput` per agent (input schema).
The aggregator emits a `CoordRiskScore` per (file:function) coordinate plus a
top-level `run_report.json` and a `heatmap.md` archive.

The cardinal rule: scores are ORDINAL, not cardinal. Treat any aggregation
across runs / repos / model families with skepticism; calibrate before reading
absolute probability claims.
"""

from __future__ import annotations

import json
from typing import Any

# --- Input schema (what each LLM agent emits) -------------------------------

INPUT_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "AgentDiagnosticOutput",
    "type": "object",
    "required": ["agent_id", "findings"],
    "properties": {
        "agent_id": {
            "type": "string",
            "description": "Stable identifier; matched against preset.",
        },
        "evidence_slice": {
            "type": "string",
            "description": "Which slice of the codebase this agent saw "
                           "(e.g. 'static:fn+callers', 'history:git_blame_24mo').",
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "coord", "score", "rank_band",
                    "evidence_quote", "reasoning",
                ],
                "properties": {
                    "coord": {
                        "type": "string",
                        "pattern": r"^[^\s].+:[^\s].+$",
                        "description": "file_path:function_name — stable id.",
                    },
                    "score": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Verbalized failure probability. "
                                       "Treat as ORDINAL within a single run.",
                    },
                    "rank_band": {
                        "type": "string",
                        "enum": ["HIGH", "MED", "LOW"],
                        "description": "Coarse band the agent is committing to. "
                                       "Survives bad calibration.",
                    },
                    "evidence_quote": {
                        "type": "string",
                        "minLength": 10,
                        "description": "Verbatim line(s) from the evidence slice "
                                       "the agent is reacting to.",
                    },
                    "reasoning": {
                        "type": "string",
                        "minLength": 20,
                        "description": "Plain-English reasoning from this agent.",
                    },
                },
            },
        },
    },
}

# --- Output schema (what the aggregator emits per coord) --------------------

COORD_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "CoordRiskScore",
    "type": "object",
    "required": [
        "coord", "consensus_score", "agreement_band",
        "n_agents_reported", "logit_variance",
    ],
    "properties": {
        "coord": {"type": "string"},
        "consensus_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Posterior in [0,1]. If history prior was fused, "
                           "this is the prior-augmented posterior; otherwise "
                           "the flat-prior logit-averaged mean.",
        },
        "agreement_band": {
            "type": "string",
            "enum": ["unanimous", "majority", "contested", "single"],
            "description": "'unanimous' if all agents within 0.2 logit of "
                           "consensus; 'majority' if >=3 of N or 2 of 2 "
                           "within 0.3 logit; 'contested' otherwise; "
                           "'single' if only one agent reported this coord.",
        },
        "n_agents_reported": {"type": "integer", "minimum": 1},
        "logit_variance": {
            "type": "number",
            "minimum": 0.0,
            "description": "Sample variance of per-agent logit scores. "
                           "HIGH variance + LOW consensus_score often means "
                           "an underspecified surface worth human review.",
        },
        "contributing_agents": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["agent_id", "score", "rank_band", "reasoning"],
                "properties": {
                    "agent_id": {"type": "string"},
                    "score": {"type": "number"},
                    "rank_band": {"type": "string"},
                    "reasoning": {"type": "string"},
                    "evidence_quote": {"type": "string"},
                },
            },
        },
        "history_prior_p": {
            "type": ["number", "null"],
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "History prior fused into consensus_score, if any.",
        },
    },
}


def validate_input(obj: dict[str, Any]) -> None:
    """Cheap structural check — real validation requires jsonschema at runtime,
    but this catches the common mistakes early."""
    if not isinstance(obj, dict):
        raise ValueError(f"expected dict, got {type(obj).__name__}")
    for key in ("agent_id", "findings"):
        if key not in obj:
            raise ValueError(f"missing required key: {key!r}")
    if not isinstance(obj["findings"], list):
        raise ValueError("findings must be a list")
    for i, f in enumerate(obj["findings"]):
        if not isinstance(f, dict):
            raise ValueError(f"findings[{i}] is not a dict")
        for key in ("coord", "score", "rank_band", "evidence_quote", "reasoning"):
            if key not in f:
                raise ValueError(f"findings[{i}] missing required key: {key!r}")
        s = f["score"]
        if not (isinstance(s, (int, float)) and 0.0 <= s <= 1.0):
            raise ValueError(f"findings[{i}].score out of [0,1]: {s!r}")
        if f["rank_band"] not in {"HIGH", "MED", "LOW"}:
            raise ValueError(f"findings[{i}].rank_band bad: {f['rank_band']!r}")


def dump_schema(name: str) -> str:
    if name == "input":
        return json.dumps(INPUT_SCHEMA, indent=2)
    if name == "coord":
        return json.dumps(COORD_SCHEMA, indent=2)
    raise ValueError(f"unknown schema: {name}")
