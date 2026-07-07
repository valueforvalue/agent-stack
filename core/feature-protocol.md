# Feature Add Protocol

The canonical procedure for adding a new feature to a repo
that adopts agent-stack. Pairs with [`rpci.md`](rpci.md)
(procedural flow) and the issue framework in
`../issues/` (issue filing); this doc owns the
feature-specific decisions, commit shape, and module
discipline.

## Pre-flight checklist

Tick these before any recon:

- [ ] **Glossary** — read the repo's glossary end-to-end. If
      the feature adds a domain concept, propose a glossary
      entry in the issue body.
- [ ] **Flow** — read [`rpci.md`](rpci.md). The four phases
      (Research → Plan → Critique → Implement) apply.
      Features default to **full RPCI** unless one-line
      bug-fix-shaped.
- [ ] **Bug patterns** — read [`bug-patterns.md`](bug-patterns.md)
      §layer for every layer the feature touches.
- [ ] **Cross-layer contract** — read
      [`code-changes.md`](code-changes.md) when the feature
      touches multiple layers.
- [ ] **Index** — read the repo's docs-index to know which
      tier-1/2 docs to load for this task.
- [ ] **TDD anchor** — read [`tdd.md`](tdd.md). Every slice
      pins its user-facing acceptance criterion with a
      failing test BEFORE the slice lands.

## When to use

| Task shape | Flow |
|---|---|
| One-line bug fix, clear repro | Skip the protocol. Bug protocol applies. |
| One-commit feature | Lightweight. Issue body has Use case + Acceptance + Regression net. No slice plan. |
| Multi-file feature, 2-3 layers | Full protocol. Use case + Decisions + Apply-sites + Acceptance + Slice plan in the issue body. |
| Subsystem feature, 4+ files | Full protocol + design artifact. Issue body + `docs/designs/<slug>.md`. |
| Cross-cutting, 6+ files, design questions | Full protocol + heavy artifacts (`RESEARCH.md` → `PRD.md` → `TASKS.csv`). |

## Tracer bullets (vertical-slice discipline)

Build a tiny, end-to-end slice first, get feedback, then
expand. AI agents are prone to outrunning their headlights —
building whole layers in isolation before the critical path
is validated. The 3-tier commit rule below is the
enforcement mechanism: every commit is one slice, every
slice crosses every layer, no slice ships without a
regression net running green.

**Hard rule:** do not start the next slice until the
previous commit is green AND the user has seen the working
surface. A fresh context window for each slice is ideal.

## The 3-tier commit rule

One commit = one of:

### Tier 1 — user-visible outcome

The whole feature lands in one commit because no
intermediate state is shippable. Rare in single-binary
single-user apps; more common in libraries where one
breaking change is the deliverable.

### Tier 2 — vertical slice across one boundary

A backend vertical (schema + service + handler) OR a UI
vertical (view + JS + audit probe) in one commit, because
alone it doesn't compile or doesn't surface to the user.
**Always paired with at least one matching UI apply-site in
the same PR** (see "Backend-first law" in the repo's laws
doc).

### Tier 3 — apply-site unit

One apply-site = one commit, when each apply-site is
independently significant.

**The rule:** if you can write a one-sentence commit subject
that doesn't need "and", it's atomic. If it needs "and"
twice, decompose.

**Anti-patterns:**

- Per-layer micro-commits (one for schema, one for service,
  one for handler, one for UI). Each independently
  uncompilable. Bundle into a Tier 2 vertical.
- Mega-commit (everything for a feature in one commit).
  Hides the apply-site unit; impossible to revert one slice
  without losing the others.

## Module discipline (deep-module)

### Define the facade before the internals

Write the **public service interface** + **DTO contracts**
BEFORE any internal code. UI and tests cross this seam; the
implementation is invisible behind it.

```pseudo
// Service signature (public seam) — write this first
interface TagService {
    NormalizeName(raw string) string
    UpsertByName(raw string) (Tag, error)
    Attach(personID int64, tagID int64) error
    // ... only methods demanded by acceptance criteria
}

// DTO returned to UI (boundary mapping)
struct TagDTO {
    ID, Name, NormalizedName, CreatedAt
}
```

Internal helpers are private to the package and not in the
interface. If a caller needs them, the seam is wrong.

### Service is the seam

- UI depends on the service's DTOs, never on the persistence
  struct.
- Tests cross the service's interface, not the persistence
  layer.
- If a view file imports the DB / model package to reach a
  struct directly, the seam is broken — add a DTO.

### Deletion test

Would deleting this module break N callers?

- **N == 0** → pass-through, refactor into the caller.
- **N >= 2** → earning its keep, keep the module.
- **N == 1** → borderline; often premature extraction.

### The two-adapter rule

Before adding a new public method to an existing service,
ask: "Does an acceptance criterion demand this method, OR
is there a second adapter that needs it?"

If neither, the method is speculative. Drop it.

### Don't return persistence structs to UI

Map to a DTO at the boundary. Persistence structs can grow
columns without breaking UI.

## Prefactor before slicing

"Look for opportunities to prefactor the code to make the
implementation easier. Make the change easy, then make the
easy change."

Run a lite explore before writing the slice plan: look for
module shapes that will force the slices to take
workarounds, look for facades that the new feature will
leak across, look for existing tests that the new feature
will silently break.

If a prefactor is identified, it ships as a separate slice
*BEFORE* the feature slices. The prefactor is not Tier 1
(no user-visible outcome) — it lands in `### Maintenance`
CHANGELOG and gets its own atomic commit.

## Issue template

The full feature template lives in `../issues/feature-template.md`.
This section summarizes what goes in each section of the
issue body.

**User story** is for the next maintainer, not for the
agent. "I want to organise X by ad-hoc categories" — not
"add a tag table with a many-to-many join."

**Apply sites** is a checklist, not prose. Prose hides
gaps; checkboxes make them visible.

**Glossary changes** are required when the feature
introduces a new domain term, even if it feels obvious. The
glossary is the contract.

**Acceptance criteria** are testable in 5 minutes by a
human with the build.

**Slice plan** mirrors the 3-tier commit rule. Each slice
names its tier in the subject and ships the whole tier in
one commit.

## When to load what

| If you're working on... | Read these (in order) |
|---|---|
| Any feature | This file, then the repo's glossary |
| Backend handler / service | `code-changes.md`, `bug-patterns.md` backend section |
| View template / framework wiring | `bug-patterns.md` view section |
| Frontend JS | `bug-patterns.md` frontend section |
| Native dialog | The addendum that owns the stack |
| Database schema | The migration history (latest two) |
| Audit smoke probe | The audit playbook |

## Anti-patterns

- **Ship the backend first, UI later.** Violates the
  backend-first law. Don't ship "backend-only" PRs for
  features.
- **One mega-commit.** Hides slice boundaries; impossible
  to revert one surface.
- **Per-layer micro-commits.** Each uncompilable.
- **Speculative public API.** Adding methods that no
  acceptance criterion demands.
- **Returning persistence structs to UI.** Breaks the seam.
- **Glossary drift.** Adding a feature without updating the
  glossary.
- **Smoke probe missing.** Every UI apply-site needs a
  probe that checks both response shape AND `page.url()`
  after the click.

## References

- The repo's glossary — read first
- [`rpci.md`](rpci.md) — Research → Plan → Critique → Implement
- `../issues/feature-template.md` — full issue body template
- [`bug-patterns.md`](bug-patterns.md) — per-layer bug patterns
- [`code-changes.md`](code-changes.md) — cross-layer contract