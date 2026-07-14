# Knowledge Portfolio — Framework-Level Reading Lists

> Tip #9 (*Invest Regularly in Your Knowledge Portfolio*) —
> the framework-level home for the per-agent / per-adopter
> learning material that the audit doc cross-references.

## What this dir is

A `docs/learning/` lane for the per-stack reading lists the
agent-stack framework recommends *before* touching a stack's
addendum or running scripts/init.sh against a target repo.

The pattern follows DixieData's `docs/learning/` convention
(per the Tip #9 audit row in `docs/audit/pragmatic-programmer-audit-2026-07.md`).
Each `docs/learning/addenda/<stack>.md` carries the
stack-specific prereqs: the framework's intrinsic mental
model + the top-3 bookend readings + the addendum-specific
guard tests to read first.

## Per-stack entries

| Stack | Entry | Status |
|---|---|---|
| `addenda/go-htmx.md` | [`addenda/go-htmx.md`](addenda/go-htmx.md) | Seeded — first per-stack entry |
| `addenda/react.md` | (not shipped) | Open — when addendum lands |
| `addenda/python.md` | (not shipped) | Open — when addendum lands |
| `addenda/vue.md` | (not shipped) | Open — when addendum lands |
| `addenda/typescript.md` | (not shipped) | Open — when addendum lands |
| `addenda/angular.md` | (not shipped) | Open — when addendum lands |
| `addenda/ruby.md` | (not shipped) | Open — when addendum lands |

## What goes in a per-stack entry

Four sections per entry. Keep the format parallel so the
agent knows what to expect:

1. **Mental model in 5 minutes** — the core abstraction that
   makes the rest click. If you can't name it in 5 minutes,
   the entry isn't done.
2. **Top-3 books / articles** — the bookend readings. Tip #9
   recommends 3+ hours of reading per month on adjacent
   topics; the top-3 list is the *floor*, not the ceiling.
3. **Addendum-first reading order** — which sections of
   `core/` + the per-stack `addenda/` to load in what order
   when onboarding.
4. **Failure-mode catalogue** — the "I burned fingers on
   this" snippets from the audit's per-tier tip rows. Tip
   #94 (*Find Bugs Once*) is the meta-rule this section
   operationalizes at the per-stack level.

## When to extend this dir

- **A new addendum lands.** The addendum's first commit
  also seeds `docs/learning/addenda/<stack>.md` with the
  four-section structure above. The `addenda/`
  "what goes in an addendum" checklist (per
  `addenda/README.md`) gains a 5th item pointing here.
- **A new audit closure.** When a `❌ Gap` audit tip is
  *closed* (a follow-up commit lands the rule), the closure
  can optionally add a bullet to the relevant per-stack
  entry. The audit doc is the source of truth; this dir is
  the *learning surface*.
- **Quarterly.** Each per-stack entry should be re-read in
  full once a quarter. If a book is no longer relevant or a
  new "I burned fingers" snippet deserves a paragraph, edit
  in place. The dir is a *living* list, not a snapshot.

## References

- `core/pragmatic-principles.md` §1.1 DRY (vocabulary DRY
  applies here — one reading-list dir, not N copies per
  addendum)
- `core/pragmatic-principles.md` §1.16 It's All Writing
  (this dir is meta-documentation in the spirit of
  Chapter 13's "treat docs as code")
- Tip #9 in `docs/audit/pragmatic-programmer-audit-2026-07.md`
  — the audit row this dir closes
- DixieData's `docs/learning/` convention (per DixieData's
  CONTEXT.md §'Laws' earn-by-real-bug provenance)
