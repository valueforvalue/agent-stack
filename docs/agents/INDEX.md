# Agent Docs Index — Progressive Disclosure

The agent-stack repo ships ~16 docs under `core/` + a smaller
addendum tree under `addenda/`. An agent does not need to
load all of them. This index tells you which tier each doc
belongs to and when to load it. The pattern is documented
in [`../core/docs-index-scheme.md`](../core/docs-index-scheme.md).

## Tier 0 — Always loaded

Cross-cuts every task. Load at session start. The agent
should not start work without these in context.

| Doc | Why | Load when | Token cost |
|---|---|---|---|
| [`../core/laws.md`](../core/laws.md) | Non-negotiable laws (earned-by-real-bug). | Always. | ~1.5K |
| [`../core/session-protocol.md`](../core/session-protocol.md) | Procedural rules (no-impl-before-direction, YAGNI, bias-toward-action, proportional depth). | Always. | ~1K |
| [`../core/rpci.md`](../core/rpci.md) | Research → Plan → Critique → Implement flow. | Always (default flow for non-trivial work). | ~2K |
| [`../core/commit-and-branch.md`](../core/commit-and-branch.md) | Commit shape (Conventional Commits prefix + area) + branch policy. | Always. | ~1.2K |
| [`../core/feature-protocol.md`](../core/feature-protocol.md) | Slice discipline + Tier 1-3 commit rule + two-adapter rule + apply-sites checklist. | Always (lite skim if not doing feature work). | ~3K |

Tier 0 total: ~9K tokens. Trim by skipping `feature-protocol.md` on a strictly non-feature session (pure bug fix or pure doc edit).

> **Cross-tier rule.** When the Plan or Critique phase surfaces a "Principle warnings" entry, load
> [`../core/pragmatic-principles.md`](../core/pragmatic-principles.md) — see the entry in Tier 1. The
> trigger is the slice-plan shape; the doc is the *why*. Don't load it proactively.

## Tier 1 — Task-role loaded

Loaded only when the task matches the role. Don't pre-load
all of them. The **load-when** description is the only signal
the agent uses to decide whether to load the doc body. Vague
descriptions = doc never loaded.

### Cross-cutting

| Doc | Load when | Token cost |
|---|---|---|
| [`../core/glossary-discipline.md`](../core/glossary-discipline.md) | A new domain term lands in the slice, OR the adopting repo's glossary is missing entries. | ~1K |
| [`../core/code-changes.md`](../core/code-changes.md) | The change crosses multiple layers (view + framework + handler + service + DB). | ~1.8K |
| [`../core/pragmatic-principles.md`](../core/pragmatic-principles.md) | Designing a new feature, refactoring, reviewing a PR, or deciding whether a slice is about to violate a principle. Each principle (§1.1-§1.16) has a "When you might violate" section listing *known* cases where the repo legitimately breaks the principle. The "warn + cite protocol" is the enforcement mechanism — the slice plan gets a "Principle warnings" block (wired from `rpci.md` Plan template AND `feature-protocol.md` Issue template), the user signs off as part of the Critique gate, the rationale lands in the commit message + CHANGELOG. **Tier 1 by design**: the doc is ~5K tokens (too big for Tier 0's 2K-per-doc ceiling), but every Tier 0 doc that needs it cross-references it so the agent loads it during Plan time, not proactively. | ~5K |
| [`../core/complexity.md`](../core/complexity.md) | Designing a new module, debating YAGNI vs broad interface, reviewing for strategic-programming correctness. Cite §-numbers in code review. | ~3K |
| [`../core/bug-patterns.md`](../core/bug-patterns.md) | Investigating a regression whose root-cause class is unclear. Stack-agnostic catalog. For per-stack specifics, load the relevant addendum. | ~3K |
| [`../core/tdd.md`](../core/tdd.md) | Every slice that lands code. RED test pins the slice's acceptance criterion BEFORE code lands. | ~2K |
| [`../core/adr-discipline.md`](../core/adr-discipline.md) | A decision durable enough that the next LLM session (or a human six months from now) needs it without reading the chat log. | ~1.5K |
| [`../core/subagent-pattern.md`](../core/subagent-pattern.md) | The work matches a subagent type's description; OR the main context budget is at risk. | ~1.2K |
| [`../core/agent-memory.md`](../core/agent-memory.md) | Adopting a repo for the first time; OR the session is moving toward handoff. | ~1.3K |

### Bug work

| Doc | Load when | Token cost |
|---|---|---|
| [`../core/bug-patterns.md`](../core/bug-patterns.md) (already above) | Plus the stack-specific addendum from Tier 1 addenda. | — |
| The addendum that owns the stack (`addenda/<stack>.md`) | The bug class matches the addendum's bug catalog (Frontend wiring / View markup / Frontend JS / Backend / etc.). | ~5–10K |

### Feature work

| Doc | Load when | Token cost |
|---|---|---|
| [`../core/feature-protocol.md`](../core/feature-protocol.md) (already in Tier 0) | — | — |
| `../issues/feature-template.md` | Adding a new feature. Mirror the template's sections in the issue body. | ~0.5K |
| The stack-specific addendum | The feature crosses the stack's layer boundaries (e.g. Go + HTMX features touch templ + chi + frontend JS). | ~5–10K |

### Schema / database

| Doc | Load when | Token cost |
|---|---|---|
| The adopting repo's migration history | A slice touches schema. Read the latest two migrations before writing the next. | per-file |

### Process / meta

| Doc | Load when | Token cost |
|---|---|---|
| [`../core/docs-index-scheme.md`](../core/docs-index-scheme.md) | Reviewing tier placement (quarterly); OR adding a new agent-facing doc and not sure which tier. | ~1K |
| [`../learning/README.md`](../learning/README.md) + the relevant `../learning/addenda/<stack>.md` | Onboarding onto a stack for the first time, or the audit's per-tier tip rows surface a 'burned-fingers' bullet pointing at the stack. The 5-minute mental model + top-3 readings section gets an agent productive faster than reading the addendum cold. | ~1K per per-stack entry |

## Tier 2 — On-demand

Lives under `addenda/` and is NOT loaded by default. Load only
when the task matches the addendum's stack.

| Doc | Load when | Token cost |
|---|---|---|
| `addenda/go-htmx.md` | Working on a Go + HTMX + templ + chi + Wails repo. Contains the canonical dialog-guard law + the HX guard tests (route-table integrity, response-shape contract, swap-scope re-binding, OOB target integrity, route-order wildcard ordering). | ~10K |
| (future) `addenda/react.md`, `addenda/python.md`, etc. | Same idea, per-stack addenda for other stacks. | per-stack |

## Token-cost audit

The Tier 0 budget targets ≤10K tokens of "always loaded"
context. Anything above that line should be moved to Tier 1 +
scoped behind a `Load when:` description. Each Tier 1 doc
should stay under ~5K tokens per role; per-addendum docs can
go higher because they only load when the stack matches.

When a Tier 0 doc grows past its target budget, split it:
the *principle* stays at Tier 0; the *operational detail*
moves to a Tier 1 doc the agent loads on-demand.

## How to use

1. Read Tier 0 at session start. Stop. Do not load Tier 1 yet.
2. Read the task. Identify which Tier 1 doc(s) match.
3. Load only those Tier 1 docs.
4. If the task references a specific stack addendum (HTMX,
   React, etc.), load that addendum's relevant section, not
   the whole file.

If a doc you'd expect to find isn't listed, it's either in
the wrong tier (open an issue) or it doesn't exist yet (open
an issue with a "missing doc" label).

## Retention

Tier 2 docs that age out (superseded by newer guard tests,
resolved bugs, etc.) move under `docs/historical/` per
[`../core/docs-index-scheme.md`](../core/docs-index-scheme.md)
§"Retention". The Tier 2 entry above stays in this index as
a pointer; the body moves out of `addenda/` and into
`docs/historical/addenda-archived/<stack>.md`.

## References

- [`../core/docs-index-scheme.md`](../core/docs-index-scheme.md) —
  the pattern this index implements
- [`../core/laws.md`](../core/laws.md) §"Tier-0 docs have a
  size ceiling" — the enforced budget
- [Anthropic: Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Will Larson: Progressive disclosure and large files](https://lethain.com/agents-large-files/)
