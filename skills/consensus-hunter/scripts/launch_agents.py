"""
Agent launcher for consensus-hunter.

Drives the 5 agents in two passes when --max-concurrent < 5:

  Pass 1 (3 evidence slices, default ceiling-friendly):
    agent_static_security     -> static:fn+callers slice
    agent_history_churn       -> history:git_blame_24mo slice
    agent_test_coverage       -> test:branch-coverage slice

  Pass 2 (2 reasoning protocols, reuse slice-1 cached evidence):
    agent_contract_violator   -> contract:fn-sig+callers slice
    agent_spec_compliance     -> spec:docstring+commit-intent slice

Each agent outputs JSON to <out>/<agent_id>.json conforming to
lib/schema.py::INPUT_SCHEMA.

NOTE: this script is a thin orchestration layer that prepares evidence
slices and produces agent prompts. It does NOT itself perform LLM calls;
that's the parent process's job (the python harness in this conversation).
For an automated/headless run, replace this stub with calls to your
preferred LLM client (Anthropic SDK, OpenAI SDK, local Ollama, etc.).

The reason it's stub-only: the consensus-hunter skill is designed to be
invoked by another agent (via the Agent tool), where the prompts and
outputs are conversational, not pipelined through Python. This script
exists to make the orchestration reproducible for benchmarking.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


# The five agent definitions — copied verbatim from presets/5-agent-preset.md
# so a benchmarker has the whole preset in one place.
AGENTS = [
    {
        "agent_id": "static_security",
        "evidence_slice": "static:fn+callers",
        "pass": 1,
        "system_prompt": (
            "You are a defensive code reviewer focused on security boundary conditions. "
            "You receive: function bodies + their 1-hop callers, scoped tight. "
            "DO NOT request more code. Enumerate every place the function could "
            "fail safe in a hostile environment."
        ),
        "user_prompt": (
            "Review the supplied evidence slice and emit JSON matching the schema:\n"
            "{'agent_id': 'static_security', 'evidence_slice': 'static:fn+callers', "
            "'findings': [{'coord': '<file>:<fn>', 'score': 0..1, "
            "'rank_band': 'HIGH|MED|LOW', 'evidence_quote': '...', 'reasoning': '...'}]}\n"
            "Every reported coord must include a verbatim quote from the slice you saw. "
            "Only report coords you actually saw. Skip benign ones."
        ),
    },
    {
        "agent_id": "history_churn",
        "evidence_slice": "history:git_blame_24mo",
        "pass": 1,
        "system_prompt": (
            "You are a deep-history reviewer. You receive: per-function git blame "
            "across the last 24 months + the file's co-change graph. "
            "A function fixed multiple times in 24 months is a finding regardless "
            "of current state. A function whose file mostly changes with suspicious "
            "neighbors inherits risk."
        ),
        "user_prompt": (
            "Review the evidence and emit JSON {'agent_id': 'history_churn', "
            "'evidence_slice': 'history:git_blame_24mo', 'findings': [...]}."
        ),
    },
    {
        "agent_id": "test_coverage",
        "evidence_slice": "test:branch-coverage",
        "pass": 1,
        "system_prompt": (
            "You are a coverage-gap reviewer. You receive: tests touching each "
            "function + the coverage map (uncovered branches). "
            "For each UNCOVERED branch, hypothesize an input that would expose a defect."
        ),
        "user_prompt": (
            "Review the evidence and emit JSON {'agent_id': 'test_coverage', "
            "'evidence_slice': 'test:branch-coverage', 'findings': [...]}."
        ),
    },
    {
        "agent_id": "contract_violator",
        "evidence_slice": "contract:fn-sig+callers",
        "pass": 2,
        "system_prompt": (
            "You are a contract-compliance reviewer. You receive: function signatures "
            "+ every public caller's argument shape + return types. "
            "Walk every public caller: does the call satisfy the function's "
            "precondition? Does the function return what the caller expects?"
        ),
        "user_prompt": (
            "Review the evidence and emit JSON {'agent_id': 'contract_violator', "
            "'evidence_slice': 'contract:fn-sig+callers', 'findings': [...]}."
        ),
    },
    {
        "agent_id": "spec_compliance",
        "evidence_slice": "spec:docstring+commit-intent",
        "pass": 2,
        "system_prompt": (
            "You are an intent-validation reviewer. You receive: docstring + module "
            "docs + commit messages that last touched the function + linked issue text "
            "via git log --grep. Find divergences between what the function DOES and "
            "what it DOCUMENTS."
        ),
        "user_prompt": (
            "Review the evidence and emit JSON {'agent_id': 'spec_compliance', "
            "'evidence_slice': 'spec:docstring+commit-intent', 'findings': [...]}."
        ),
    },
]


def slice_file_for(repo: Path, evidence_slice: str) -> Path:
    """Real evidence slice construction is repo-specific and intentionally
    out of scope for the v0.1 stub. This function returns a placeholder path
    to the slice; the parent process builds the actual context content."""
    return repo / ".consensus-hunter" / "slices" / f"{evidence_slice.replace(':', '_')}.txt"


def write_prompts(out_dir: Path, agents: list[dict], evidence_dir: Path) -> None:
    """Emit one file per agent containing its evidence slice reference +
    prompts ready for an LLM client to consume."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for a in agents:
        path = out_dir / f"{a['agent_id']}.prompt.json"
        with path.open("w") as f:
            json.dump({
                "agent_id": a["agent_id"],
                "evidence_slice": a["evidence_slice"],
                "evidence_path": str(slice_file_for(evidence_dir, a["evidence_slice"])),
                "system_prompt": a["system_prompt"],
                "user_prompt": a["user_prompt"],
                "output_schema_path": str(Path(__file__).resolve().parent.parent / "data" / "schema" / "input.example.json"),
            }, f, indent=2)
    print(f"wrote {len(agents)} prompt file(s) to {out_dir}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--max-concurrent", type=int, default=3)
    args = ap.parse_args()

    # Split into two passes for environments with concurrency caps.
    pass1 = [a for a in AGENTS if a["pass"] == 1]
    pass2 = [a for a in AGENTS if a["pass"] == 2]
    if args.max_concurrent < 5:
        print(f"--max-concurrent={args.max_concurrent}: running in 2 passes "
              f"({len(pass1)} then {len(pass2)}).")
    write_prompts(args.out, AGENTS, args.repo)
    print(f"next step: parent process invokes each agent's LLM with the "
          f"prompt file from {args.out}, captures responses to "
          f"{args.out}/agent_<id>.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
