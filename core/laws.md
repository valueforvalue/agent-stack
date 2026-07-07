# Laws (non-negotiable)

These are not style preferences. Each one was earned by a real
bug that crashed an app, lost data, or confused a user. Treat
any code that violates a law as a bug that must be fixed before
the change can ship.

Adopting repos should add their own laws here as they earn
them. The list below is the agent-stack default; each law
should cite its origin (issue number, commit hash, ADR).

## Universal laws (every stack)

### No unguarded re-entrant UI calls

If a UI operation opens a native dialog, modal, file picker,
or any other re-entrant surface, **a second invocation while
the first is still open must be rejected before it reaches
the host**. The Wails WebView2 crash history (see
`addenda/go-htmx.md`) is the canonical example; the principle
generalizes to every host that runs UI work on a single
thread (Electron, Tauri, Qt, GTK, Win32 native, Cocoa).

Implementation contract:

- The guard must be in-process (mutex or atomic flag), not
  network-level. The race is intra-process.
- The guard key must distinguish concurrent operations of
  different kinds (e.g. PDF export vs JPG export) but
  collapse duplicate clicks on the same button.
- The slot is released AFTER the dialog returns, never
  before. Releasing early re-opens the race.

### Doc comments on exported identifiers

Every exported identifier in a public-facing package — function,
type, variable, constant, including methods on exported types
— carries a doc comment.

- Starts with the identifier name.
- Explains the contract, not the implementation. What does
  the caller need to know? What are the preconditions? What
  does it return on success and on the common failure modes?
- Lives immediately above the declaration, with no blank
  line between the comment and the identifier.

CI regression gate: enforce a coverage floor (e.g. 70%) on
every package with ≥5 exported identifiers. The floor is a
regression gate, not a target — aim for 100% on every new PR.

### Glossary is a contract

If a repo maintains a glossary (typically `CONTEXT.md` or
`docs/GLOSSARY.md`), introducing a new domain term without
updating the glossary is a bug. UI copy, ADRs, and future
features depend on the glossary's vocabulary.

The companion doc [`glossary-discipline.md`](glossary-discipline.md)
documents the maintenance pattern.

## Stack-specific laws

These live in the addendum that owns the stack. Examples:

- `addenda/go-htmx.md` — Every native dialog call is guarded;
  exported Go identifiers carry doc comments (Go-specific
  version of the universal law); every framework URL goes
  through a typed builder; every persistent DOM surface ID
  is in the registry.
- (future) `addenda/react.md` — props immutable; effects list
  dependencies; context boundaries explicit.
- (future) `addenda/python.md` — type hints on public surface;
  no mutable default args.

## Promoting a rule to a law

A rule becomes a law when:

1. A bug shipped that the rule would have prevented (cite
   the issue/commit).
2. Code review without the rule consistently misses the bug.
3. The rule is enforceable by a guard test or a CI check.

If a rule fails any of those, it's still a guideline — keep
it in the per-feature doc, not in this file.