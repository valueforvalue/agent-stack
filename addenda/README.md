# addenda/

Per-stack extensions to the core docs. Each file in this
directory covers the stack-specific bug patterns, framework
quirks, helper templates, and worked examples that aren't
general enough to live in `core/`.

## v1 addenda

- [`go-htmx.md`](go-htmx.md) — Go backend + HTMX frontend +
  templ view templates + chi router + Wails / WebView2 host.
  This is the canonical addendum; covers dialog-guard law +
  routebuilder / htmxattr / uiids pattern + bug catalog §1–§6.

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

## What stays out of an addendum

- Anything already in `core/` — link back to it.
- Project-specific vocabulary — that lives in the adopting
  repo's glossary.
- Vendor-specific crash histories — quote the upstream
  issue but link to it, don't paste it.