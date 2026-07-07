# Docs Index Scheme — 3-Tier Progressive Disclosure

A repo that adopts agent-stack should maintain a
`docs/agents/INDEX.md` (or equivalent) that organizes its
agent-facing docs by tier. This file documents the pattern.

## The three tiers

### Tier-0 — always loaded

Cross-cuts every task. Load at session start. The agent
should not start work without these in context.

Examples: glossary + laws, session protocol, commit shape,
TDD discipline, RPCI flow, bug catalog, cross-layer contract.

Cross-reference these from the repo's main `AGENTS.md` so
they're pulled into the agent's context automatically.

### Tier-1 — task-role loaded

Loaded only when the task matches the role. Don't pre-load
all of them; load only the ones that match.

Examples:

- Bug work → bug-pattern catalog + manual audit playbook
- Feature work → feature protocol + CLI plan + tune iteration
- UI hunt / redesign → UI map + wireframes for the affected
  screen
- Schema / database → migration history (latest two)
- Process / meta → PRD + research + services

### Tier-2 — on-demand

Lives under `docs/historical/` (or similar) and is NOT loaded
by default. Load only when the issue, PR, ADR, or explicit
user direction names the doc.

Examples: historical handoffs, resolved audits, past
per-surface rendering reviews, old design discussions.

## Retention

Tier-2 docs are retained for traceability but not loaded by
default. The retention rule typically caps at the latest
3 rounds in the working tree; older rounds move to
`docs/historical/`.

## How to use

1. Read Tier-0 at session start. Stop. Do not load Tier-1 yet.
2. Read the task. Identify which Tier-1 doc(s) match.
3. Load only those Tier-1 docs.
4. If the task references a specific historical artifact by
   name or number, load it from Tier-2. Otherwise, ignore
   the Tier-2 docs entirely.

If a doc you'd expect to find isn't listed in the index, it's
either in the wrong tier (open an issue) or it doesn't exist
yet (open an issue with a "missing doc" label).

## Adopting this pattern

1. Create `docs/agents/INDEX.md` with the three tier sections.
2. Move existing agent-facing docs to their tier-appropriate
   category.
3. Cross-reference Tier-0 docs from `AGENTS.md` at the repo
   root so they auto-load.
4. Mark any Tier-2 doc with a clear retention timestamp.
5. Re-evaluate tier placement every quarter — a Tier-2 doc
   that gets referenced repeatedly probably belongs at Tier-1.

## References

- [`session-protocol.md`](session-protocol.md) — what the
  agent reads at session start
- [`glossary-discipline.md`](glossary-discipline.md) — Tier-0
  glossary maintenance