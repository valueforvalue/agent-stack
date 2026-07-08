# 3-Agent Preset (cheap mode)

For routine pre-commit runs where full 5-agent cost is overkill. Three
evidence slices only; reasoning protocols are uniform.

Cost: ~30k LOC context budget vs 60k for the 5-agent preset. Latency ~30s.

## The three agents

### Agent 1 — `static_security`

Same slice as `5-agent-preset.md` agent 1. Reduced precision on intent
divergence (no spec-compliance agent), but catches the same security
boundaries.

### Agent 2 — `history_churn`

Same slice as `5-agent-preset.md` agent 2. Without the cross-reference
agent, history carries more weight — `w_prior` should be set higher
when using this preset (recommend `w_prior=0.6`).

### Agent 3 — `test_coverage`

Same slice as `5-agent-preset.md` agent 3. Highest-precision lens,
retained even in the cheap preset.

## When to use

- Pre-commit hook where 5-agent cost is too much.
- Inner loop during a feature slice (every commit) vs the outer
  5-agent run on the full feature branch.
- Massive repos (>1M LOC) where 5-agent preset hits context limits;
  3-agent finishes a run that 5-agent times out on.

## What you give up

- Contract compliance lens (caller/callee mismatch).
- Intent validation (doc vs implementation drift).

If those failure modes are the historical signature of bugs in your
repo, this preset underfits. Don't use it as your *only* preset.
