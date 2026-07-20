# addenda/

Per-stack extensions to the core docs. Each file in this
directory covers the stack-specific bug patterns, framework
quirks, helper templates, and worked examples that aren't
general enough to live in `core/`.

## v1 addenda

- [`go-htmx.md`](go-htmx.md) (Tier-1, ~460 lines) — Go backend
  + HTMX frontend + templ view templates + chi router + Wails /
  WebView2 host. The canonical addendum. Covers dialog-guard
  law + routebuilder / htmxattr / uiids pattern + framework
  quirks + Go testing recipes (var-_, build-tag diag,
  table-driven consolidation) + HTMX-specific guard tests +
  adopting-these-tests starter set. Loaded by default for any
  Go-adopter session.
- [`go-htmx-bug-catalog.md`](go-htmx-bug-catalog.md)
  (Tier-2 reference, ~900 lines) — Companion bug catalog.
  Bug catalog §1–§6 (per-layer patterns with `Find it:`
  greps) + bug-class → first-place-to-look navigation table +
  Security (govulncheck workflow) + Mutation testing
  (go-mutesting workflow). Loaded on demand when chasing a
  specific bug or running a per-layer audit, **not** at
  session start.

## Loading

Load exactly one addendum per repo. The init script asks
which one to wire into the target repo. If your stack isn't
listed, ship your own addendum modeled on `go-htmx.md` and
PR it back.

## What goes in an addendum

- Stack-specific laws (Go doc comments, JSX prop
  conventions, etc.).
- The named framework's drift-prone patterns (HTMX swap
  target inheritance, React effect dependencies, Django ORM
  N+1 queries, etc.).
- Helper templates (dialog-guard for Wails, debounce for
  React effects, retry-with-backoff for SQLAlchemy, etc.).
- Per-layer bug catalog with `Find it:` greps.
- Worked examples from real shipped bugs in the stack.
- **A paired `docs/learning/addenda/<stack>.md`** with the
  5-minute mental model + top-3 readings + addendum-first
  reading order + failure-mode catalogue. The two files
  ship together (see `docs/learning/README.md` §'When to
  extend this dir').

## What stays out of an addendum

- Anything already in `core/` — link back to it.
- Project-specific vocabulary — that lives in the adopting
  repo's glossary.
- Vendor-specific crash histories — quote the upstream
  issue but link to it, don't paste it.