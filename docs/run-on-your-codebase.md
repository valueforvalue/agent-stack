# Run on Your Codebase

What to do with the framework once you've cloned or vendored it.
Covers the practical adoption patterns, the order in which to apply
the primitives, and the LLM-driven workflow for the calibration skill.

This doc is intentionally operational. For design rationale, see the
respective per-doc READMEs and citations in `core/complexity.md`.

## Tier 0 — adopt the framework scaffolding (one-time, 30-60 min)

These travel with any repo you bootstrap. They pay off forever.

### 1. Copy `core/` into your repo

```bash
cp -r framework/core /path/to/your-repo/docs/agents/
cp framework/AGENTS.md.tmpl /path/to/your-repo/AGENTS.md
cp framework/CONTEXT.md.tmpl /path/to/your-repo/CONTEXT.md
```

Or run the framework's `scripts/init.sh` for an interactive bootstrap
that handles this for you.

The five rules in `core/session-protocol.md` (no implementation
before direction, batched discovery, YAGNI, bias toward action,
proportional depth) — and their refinements (e.g. YAGNI for
features only, not interfaces) — are now live for every LLM session
on your repo.

### 2. Adapt `complexity.md` to your context

`core/complexity.md` is the framework's primitive. To get the value:

- Replace §2 (tactical-vs-strategic), §3 (pull complexity downward),
  §5 (rule of three) examples with cited references to **your**
  existing docs (`MISTAKES.md`, `ARCHITECTURE_MAP.md`, ADR-by-ADR).
- The framework version reads as a one-pager; the per-repo version
  becomes 50-100 lines with your codebase's evidence anchored.

### 3. Wire `commit-and-branch.md` and `feature-protocol.md`

Adopting repos typically already have commit-shape and feature
protocols. The framework's versions blend conventional commits with
the 3-tier commit rule (Tier 1 whole-feature, Tier 2 vertical slice,
Tier 3 apply-site). Align your existing rules with the framework's
naming or document the divergence.

### 4. Initialize an ADR discipline

`core/adr-discipline.md` (and your `core/laws.md`) provide the
templates. Create `docs/adr/0001-*.md` and grow from there. Promote
to a law when a bug ships that an ADR would have prevented; the ADR
is the historical anchor, the law is the enforceable rule.

## Tier 1 — adopt the operational primitives (one-day pilot)

These need a small pilot to validate the workflow before scale-out.

### 5. `tdd.md` — source-anchored red-green-refactor

Test pinning is the easiest framework primitive to adopt and the
hardest to skip once you have it. Pair with your existing
CI/lint/format chain; the bar is "every commit has a failing test
that pins user-facing acceptance."

### 6. Run a calibration replay (LLM-driven)

The headline operational primitive. Steps:

```bash
# From the framework repo, with your codebase as a sibling:

# A. Build the held-out label set
python scripts/build_held_out.py \
    --repo /path/to/your-repo \
    --target <path/within/your-repo> \
    --since <YYYY-MM-DD> --until <YYYY-MM-DD> \
    --output /path/to/your-repo/.consensus-hunter/eval_coords.json

# B. Extract function bodies at the cutoff
python scripts/extract_function_bodies.py \
    --repo /path/to/your-repo \
    --cutoff <sha> \
    --eval /path/to/your-repo/.consensus-hunter/eval_coords.json \
    --output /path/to/your-repo/.consensus-hunter/function_bodies.json

# C. Drive the 5 agents (parent agent or operator invokes each).
#    See step 7 below for the LLM-driven loop.

# D. Run the calibration aggregator
python skills/consensus-hunter/scripts/run_real_agent_calibration.py \
    --repo /path/to/your-repo \
    --emit /path/to/your-repo/.consensus-hunter/calibration.json
```

The full operational guide is at
[`skills/consensus-hunter/OPERATIONS.md`](../skills/consensus-hunter/OPERATIONS.md).
The v0.1 caveat: the `build_held_out.py` and `extract_function_bodies.py`
scripts live in the per-repo `scripts-tmp/` for now; v0.2 moves them
into the framework.

**What to expect on a clean run:**

- `consensus.logit_averaged_skill_score` in +0.05 to +0.30 range on
  single-model configurations (multi-model v1.1 lands higher).
- `consensus.precision_at_k` between 0.7 and 1.0 — the operational
  number to defend.
- `per_agent.history_churn` as the highest-weighted agent on Go and
  Python codebases with structured commit messages (matches both
  django and dixiedata calibrations).

## Tier 2 — operationalize (1-2 weeks of use)

### 7. The LLM-driven agent loop

For an LLM-driven calibration, the parent agent (the one running
the conversation) follows:

```
for each agent in [static_security, history_churn, test_coverage,
                   contract_violator, spec_compliance]:
  1. Build the evidence slice for this agent per
     skills/consensus-hunter/presets/5-agent-preset.md.
     - static_security:      function body + 1-hop callers
     - history_churn:        git blame for last 24 months
     - test_coverage:        tests touching the function
                              + uncovered branches
     - contract_violator:    signature + caller argument shapes
     - spec_compliance:      docstring + commit-intent text

  2. Run the agent prompt. The agent emits:
     {
       "agent_id": "...",
       "evidence_slice": "...",
       "findings": [
         {"coord": "<file>:<fn>", "score": 0..1,
          "rank_band": "HIGH|MED|LOW",
          "evidence_quote": "...",
          "reasoning": "..."}
       ]
     }

  3. Validate against lib/schema.py::INPUT_SCHEMA.

  4. Capture to .consensus-hunter/captured/agent_<id>.json.
```

Bottleneck realities:

- **Context budget.** A 5-agent preset on a 36-coord eval with full
  evidence slices burns ~60k LOC of LLM context. Plan accordingly.
- **Wall-clock.** With sequential prompting, expect 10-30 minutes
  per calibration run.
- **Concurrency.** If your LLM client caps concurrent invocations
  (commonly 3), split pass-1 (3 evidence slices) from pass-2 (2
  reasoning protocols) per the framework's `--max-concurrent` flag.
- **Reproducibility.** Single-model 5-agent runs converge tightly;
  `agreement_band` becomes uninformative (see OPERATIONS.md §4).
  Multi-model is the path to getting disagreement back.

### 8. Run consensus-hunter on every PR

Once calibrated, point the skill at the diff:

```bash
python skills/consensus-hunter/scripts/scan_diff.py \
    --repo /path/to/your-repo \
    --base main --head feature-branch \
    --emit .consensus-hunter/diff_scan.json
```

The framework's design supports this; the v0.1 stub at
`scripts/scan_diff.py` is a TODO marker. v0.2 fills it in following
the OPERATIONS.md protocol on the changed file:set.

### 9. Build the historical risk ledger

Long-term value is per-coord risk drift over time. After each
calibration or scan, append to `.consensus-hunter/history/<iso-timestamp>.json`.
The diff between consecutive runs tells you which coordinates are
rising in risk — the Lehman §10 lead indicator that `complexity.md`
references.

## What this looks like week-to-week

After Tier 0 (one-time):

- Every LLM session loads `core/session-protocol.md` and refines
  its behavior against the five rules.
- Your `commit-and-branch.md` enforces the framework's commit shape.
- Every cross-layer change cites the relevant § of `complexity.md`.

After Tier 1 (one-day pilot):

- A calibration replay has been run; you have a real Skill Score
  number for your codebase.
- The 5-agent preset JSON for your target module is committed
  under `skills/consensus-hunter/` so future runs reuse the same
  prompt structure.

After Tier 2 (a few weeks of use):

- Each PR triggers a diff scan.
- The risk ledger accumulates; coords rising in score are surfaced
  in code review.
- ADRs and laws accumulate; the framework's portable rules and the
  codebase's local rules cross-reference each other instead of
  drifting.

## Anti-patterns

- **Adopt core/ without complexity.md.** YAGNI's reconciliation rule
  is implicit without it; agents will regress to a one-line reading
  of YAGNI and either over-extract or under-abstract.
- **Run consensus-hunter without `--calibrate-data`.** Without the
  prior calibration, scores are ranks, not risk thresholds. Be honest
  about which one you're producing.
- **Skip the time-aware split.** If you don't fix a knowledge cutoff
  before exploring the post-cutoff history, you have data leakage
  and the calibration is theatre.
- **Single-model 5-agent without `agreement_band` honesty.** The band
  becomes uniformly `unanimous`; document this and don't pretend it's
  signal.

## References

- [`core/session-protocol.md`](../core/session-protocol.md) — the
  five rules every LLM session loads at start.
- [`core/complexity.md`](../core/complexity.md) — why each Tier 0/1
  rule exists.
- [`core/feature-protocol.md`](../core/feature-protocol.md) — the
  3-tier commit rule.
- [`skills/consensus-hunter/SKILL.md`](../skills/consensus-hunter/SKILL.md)
  — the skill definition.
- [`skills/consensus-hunter/OPERATIONS.md`](../skills/consensus-hunter/OPERATIONS.md)
  — calibration methodology and gotchas.
- [`scripts/init.sh`](../scripts/init.sh) — interactive bootstrap
  for a target repo.
