---
name: consensus-hunter
description: "Multi-agent consensus bug hunting inspired by Bayesian search theory (Craven's submarine). Runs N independent LLM reviewers in parallel against a codebase, each viewing a different evidence slice, then deterministically aggregates per-coordinate risk scores in logit space. Use when the user wants a structured, audit-able, calibrated scan that scores risk per function, persists over time, and complements the existing bug-hunter skill with a faster read-only phase. Distinct from bug-hunter: parallel + numeric + persistent, where bug-hunter is sequential + narrative + ephemeral."
---

# Consensus Hunter - Multi-Agent Bug Hunt

Parallel, blind, mathematically aggregated bug hunting. Modeled on the Craven
submarine-Bayesian search idea: independent perspectives, deterministic
combination. Translated for LLM agents with three explicit caveats the field
requires: (1) LLM-issued numerics are ordinal not cardinal, so we surface
rank_bands; (2) independence in *evidence slices* beats independence in
temperature; (3) variance is a first-class signal, not noise to average out.

The output is a per-function risk map that can be archived and diffed across
runs. Builds the historical risk ledger that the framework's `complexity.md`
§10 (entropy as default) needs as a lead indicator.

## Table of Contents

- [Usage](#usage)
- [Target](#target)
- [Context Budget](#context-budget)
- [Execution Steps](#execution-steps)
- [Output](#output)
- [Calibration](#calibration)
- [Self-Test Mode](#self-test-mode)
- [Error handling](#error-handling)

```
Phase 1 — Independent Hunt (parallel, blind):
    [slice-1: fn+callers]      [slice-2: git history]      [slice-3: tests+coverage]
            \                          |                          /
             \                         |                         /
              \                        |                        /
               -------->   logit-space aggregator (lib/aggregate.py)   <--------
                                |                  |              |
                       consensus_score    agreement_band   logit_variance
                                |                  |              |
                                +------+-----+-----+              |
                                       |     |                    |
                                       v     v                    v
                                HIGH/MED/LOW  "contested"  surface for
                                  bands       coords       human review

Phase 2 (optional) — Historical Prior Fusion:
       bug_density + churn + co_change priors
            from `lib/prior.py` against the target repo
            fuse with agents via convex combination in logit space

Phase 3 (optional) — Calibration:
       Held-out (knowledge-cutoff) replay against known-bug functions
       y -> Brier / Skill Score per agent
       y -> Platt (a, b) -> apply to next run
       y -> derived agent weights
```

## Usage

```
/consensus-hunter                              # Scan entire project
/consensus-hunter src/                         # Scan specific directory
/consensus-hunter django/db/models/             # Scan specific path
/consensus-hunter --history-prior              # Fuse bug-density + churn + co-change priors
/consensus-hunter --presets 5-agent-preset     # default
/consensus-hunter --presets 3-agent-min        # cheaper
/consensus-hunter --w-prior 0.5                # history prior weight (0..1)
/consensus-hunter --w-prior 0.0                # agents only (no history)
/consensus-hunter --calibrate django --cutoff 2020-01-01
                                              # calibration replay run
/consensus-hunter --calibrate-data .consensus-hunter/calibration.json
                                              # apply saved Platt params + weights
/consensus-hunter --dry-run                    # synthesize agent outputs from synthetic truth
/consensus-hunter --json-only                  # machine-readable output only
```

## Target

The raw arguments are: $ARGUMENTS

**Parse the arguments as follows:**

1. Default `PRESET = "5-agent-preset"`. If `--presets <name>`: set `PRESET`
   and strip the flag.
2. Default `W_PRIOR = 0.5`. If `--w-prior <float>`: set `W_PRIOR` and strip.
   `W_PRIOR = 0.0` disables history priors entirely.
3. If `--history-prior`: enable Phase 2 (history priors); `--no-history-prior`
   disables it (default ON for repos with git history, OFF otherwise).
4. If `--calibrate <repo>`: run Phase 3 (calibration replay). Requires
   `--cutoff YYYY-MM-DD` to fix the knowledge cutoff.
5. If `--calibrate-data <path>`: load `.consensus-hunter/calibration.json`
   and apply its Platt params + agent weights.
6. If `--dry-run`: skip the LLM phase; generate synthetic agent outputs from
   a planted truth set (useful for sanity-checking the aggregator).
7. If `--json-only`: write only `.consensus-hunter/last_run.json`, skip the
   markdown report.

## Context Budget

Each agent gets a separate context window with its own evidence slice.
**Do not** load the same source code into multiple agents — the central
failure mode of naive multi-agent code review is "echo chamber via shared
context" (Diversity Collapse, TMLR). Each agent's window is built from a
distinct slice.

| Preset | Agents | Total LOC budget | Latency |
|---|---|---|---|
| `3-agent-min` | 3 (3 evidence slices, 1 protocol) | ~30k | ~30s/run |
| `5-agent-preset` (default) | 5 (3 evidence slices + 2 reasoning protocols) | ~60k | ~60s/run |

Per-agent context is built by `lib/prior.py` and the slice builder
(see [`presets/5-agent-preset.md`](presets/5-agent-preset.md)).

## Execution Steps

### Step 1 — Validate env

```bash
ls .git       # if history priors requested, require git repo
which git
python -c "import sys; sys.path.insert(0, 'skills/consensus-hunter'); from lib import aggregate, calibrate, prior, schema; print('ok')"
```

If any check fails, surface the error and stop (do not auto-install).

### Step 2 — Build evidence slices (parallel)

For each agent in the preset, build its evidence slice:

- **Static slice (functions + 1-hop call graph)** — agent 1.
- **History slice (git blame + co-change graph + commit-fix keywords)** — agent 2.
- **Test slice (tests + coverage map)** — agent 3.
- **Surface-diff slice** — agent 4 (reasoning protocol: contract-violation framing).
- **Cross-reference slice (type-contract / argument-shape diff)** — agent 5 (reasoning protocol: spec-compliance framing).

Slice details and example prompts: [`presets/5-agent-preset.md`](presets/5-agent-preset.md).

### Step 3 — Run N agents in parallel

Use `Agent` tool with `run_in_background: true` for each agent. Do NOT pass
the output of any agent to any other. Pass them all to the aggregator at
the end. Each agent's prompt MUST include:

- The exact evidence slice it should focus on (no global codebase).
- The exact JSON output schema (`lib/schema.py::INPUT_SCHEMA`).
- Instruction to set `rank_band` for every finding (HIGH/MED/LOW) — the
  rank band is more important than the numeric score.

### Step 4 — Aggregate deterministically

```bash
python -c "
import json, sys
sys.path.insert(0, 'skills/consensus-hunter')
from lib.aggregate import aggregate_run, rank_bands
from lib.schema import validate_input

agent_outputs = [...]  # each parsed from agent_response.json
for o in agent_outputs:
    validate_input(o)

priors = None
if W_PRIOR > 0.0:
    from lib.prior import combined_prior
    from pathlib import Path
    coords = [(o['coord'].split(':')[0], o['coord'].split(':', 1)[1])
              for o in agent_outputs for o in o['findings']]
    priors = combined_prior(Path('.'), coords)

ranked = aggregate_run(agent_outputs, history_priors=priors, w_prior=W_PRIOR)
bands = rank_bands(ranked)
print(json.dumps({'ranked': ranked, 'bands': bands}, indent=2))
"
```

### Step 5 — Optional calibration phase

If `--calibrate <repo>`:

1. Identify the known-bug function set AFTER the cutoff (`repo_slug` + `cutoff`).
   Sources by target:
   - django/sympy: SWE-Bench Verified gold patches via `git show <commit>`.
   - postgres/openssl: CVEfixes function-table (function-changed commits).
   - linux (subsystem): syzbot reports + `Fixes:` commit tags.
2. Replay the run on `repo@<cutoff_commit>`.
3. Compute Brier + Skill Score per agent via `lib/calibrate.py`.
4. Emit `.consensus-hunter/calibration.json` with `{agents: {…}, derived_weights}`.
5. Subsequent runs read `--calibrate-data` and apply.

### Step 6 — Write artifacts

Persist two artifacts (overwrites on rerun, never silently):

```
.consensus-hunter/
├── last_run.json       # full ranked output, schema in lib/schema.py
├── last_run.md         # human-readable heat map (HIGH/MED/LOW tables)
└── history/
    └── <ISO-timestamp>.json
```

`history/` accumulates over runs. **Diffing two runs** is a primary use case
— a coord rising in score across runs is a Lehman §10 lead indicator.

### Step 7 — Report

Print a one-screen summary: top 10 by `consensus_score`, all `contested`
coords (variance > majority band), and any priors that exceeded 0.7.
Concise. The full JSON is in `last_run.json` for callers that want it.

## Output

`.consensus-hunter/last_run.md` is the human surface. Shape:

```markdown
# consensus-hunter — <repo> @ <commit>

Run timestamp: ...
Preset: 5-agent-preset (W_PRIOR=0.5)
Coords evaluated: 412 | HIGH band: 82 | MED: 124 | LOW: 206

## HIGH risk (consensus_score >= 0.7)
| coord | consensus | agreement | variance | prior | top reasoning |
|---|---|---|---|---|---|
| django/db/models/query.py:_filter_or_exclude | 0.91 | unanimous | 0.04 | 0.78 | Tests don't cover 3-way joins... |
...

## CONTESTED coords (variance >> score)
| coord | consensus | n_agents | reasoning |
|---|---|---|---|
...

## Per-agent Skill Scores (if calibrated)
| agent | n | brier | skill | platt_a | platt_b | weight |
|---|---|---|---|---|---|---|
| agent_security | 60 | 0.12 | 0.41 | 1.4 | -0.2 | 1.18 |
...
```

## Calibration

The headline reason this skill exists as a separate workflow: every LLM
emits numbers, and the field has documented that those numbers are *not*
calibrated probability estimates (Spiess et al. ICSE 2025). Until you've
measured Skill Score on a held-out replay of known bugs against your
target repo, your scores are *ranks, not risk numbers*.

**Operational rule:** a run without `--calibrate-data` produces a
*ranked heat map* useful for prioritization. A run with `--calibrate-data`
produces *risk numbers* that can be thresholded across runs. Be honest
about which one your output is.

## Self-Test Mode

`--dry-run` uses a planted truth set to verify the aggregation logic works
end-to-end without paying LLM cost. Tests cover:
- All coords in `last_run.json` follow schema; `validate_input` passes.
- Aggregation is order-invariant (same outputs regardless of agent order).
- Prior fusion produces a different ranking than agents-only on the same
  inputs (`w_prior=0.5` vs `w_prior=0.0` should NOT agree exactly).
- `contested` coords surface in the markdown report.
- Calibration replay (`--calibrate`) writes `.consensus-hunter/calibration.json`.

Run all tests:
```bash
python -m unittest discover -t skills/consensus-hunter skills/consensus-hunter/tests
```

## Error handling

- **Schema invalid** (an agent emitted malformed JSON): skip that agent,
  warn to stderr, continue with remaining agents. Log the bad payload to
  `.consensus-hunter/last_run_errors.json`.
- **Git not found** when `--history-prior` was set: warn, fall back to
  W_PRIOR=0.0 (agents only). Do NOT proceed with half a prior.
- **No git history** in target (e.g. shallow clone <30 days): skip
  Priors A and C (12-month windows); keep prior B (churn) if older history exists.
- **All agents fail**: abort with exit 2; do not write artifacts.
- **One agent fails**: continue; the `agreement_band` will mark those coords
  with `n_agents_reported < expected` so human review knows trust is reduced.
- **Calibration data missing fields**: error out. Partial calibration is
  worse than no calibration (Spiess et al.: "Skill Score would reveal this").

## Anti-patterns

- **The agents see each other's outputs.** NEVER share between agents. This
  is the central failure mode of multi-agent code review (Diversity Collapse).
- **Plain arithmetic mean of probabilities.** Logit-space is correct; the
  difference is meaningful under non-uniform agent weighting.
- **Calling the output "Bayesian" without a prior.** This skill computes a
  proper logit-space posterior only when priors are supplied; calling
  W_PRIOR=0.0 a "Bayesian consensus" is false precision.
- **Treating LLM-issued numerics as calibrated.** They aren't. Use rank_band.
- **Skipping calibration on a new repo.** First-run outputs are rankings;
  cross-run thresholds require a calibration replay.
- **Shipping per-function risk scores without an archive.** The whole point
  of structured output is run-over-run diff. Write to history/ every time.

## References

- [`bug-hunter`](../bug-hunter/SKILL.md) — sequential critique-and-fix companion.
- [`code-review`](../code-review/SKILL.md) — parallel narrative review (different shape).
- [`pr-triage`](../pr-triage/SKILL.md) — single-PR disposition (different purpose).
- [`complexity.md`](../../core/complexity.md) §10 — entropy-as-default rationale for the historical risk ledger this skill builds.
- `presets/5-agent-preset.md`, `presets/3-agent-min.md` — agent definitions.
- `lib/aggregate.py`, `lib/prior.py`, `lib/calibrate.py`, `lib/schema.py` — deterministic core.
- `tests/test_aggregate.py`, `tests/test_calibrate.py`, `tests/test_schema.py` — invariant tests.

External sources cited inline in `lib/`:
- Spiess et al., *Calibration and Correctness of LMs for Code*, ICSE 2025.
- Mozilla Star Chamber — variance-as-signal pattern.
- CodeX-Verify (arXiv:2511.16708) — diminishing-returns curve for N agents.
- Pascarella & Bacchelli (MSR 2017 / ICSE 2025) — time-aware evaluation.
