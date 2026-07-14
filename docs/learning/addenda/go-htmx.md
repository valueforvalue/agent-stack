# Knowledge Portfolio — `addenda/go-htmx.md`

Per-stack entry for the Go + HTMX + templ + chi + Wails
addendum. Read this *before* reading the addendum itself if
you're onboarding onto a Go + HTMX repo for the first time.

## Mental model in 5 minutes

The five building blocks, in the order they compose:

1. **Go handler** — runs in the Wails process. Returns
   either a templ fragment (HTML), a `303 See Other`, a
   `200 OK + X-App-Redirect` header for the dispatcher, or
   a `204 No Content + X-App-Redirect` for htmx fragment
   requests. **The handler is the seam.**
2. **templ component** — typed HTML rendered into a string
   buffer. Lives in `internal/templates/*.templ` (one file
   per screen + one for shared layout primitives). The
   templ CLI generates `_templ.go` files from the `.templ`
   sources. **Never hand-edit `_templ.go`.**
3. **htmx attribute** — declarative wiring on the
   rendered HTML. Three classes: `hx-get`/`hx-post`/
   `hx-put`/`hx-delete` (HTTP verb + URL), `hx-target`
   (DOM surface ID), `hx-trigger` (event + timing), plus
   `hx-swap` (how to apply the response).
4. **Wails App struct** — the per-process actor. Holds all
   state; goroutines receive a pointer. The Wails `runtime`
   field is nil until `Startup()` completes; handle that.
5. **The dispatcher** — `frontend/app.js`
   `dispatchAppForm`. Replaces the legacy parallel
   `request()` function. Read the
   `X-App-Redirect` header; call
   `window.location.assign()` if present. Templates use
   `data-app-submit` to opt into the dispatcher.

If you can name those five in 5 minutes, the rest of the
addendum is mechanical.

## Top-3 books / articles

1. **HTMX in 100 seconds** (bigskysoftware/htmx YouTube)
   — the 10-minute mental model for hx-get/hx-target/hx-swap
   semantics. Skip the rest of the intro docs; come back for
   specifics when the addendum points at them.
2. **tutorial.edge.templ** (templ.guide) — the "I've never
   seen templ before" tutorial. Two hours. The
   `Layout(project)` pattern is the one the addendum
   inherits.
3. **Wails docs: Application Lifecycle** (wails.io) — the
   `Startup` / `Shutdown` / `OnStartup` / `OnShutdown` callback
   order. The dialog-guard law is downstream of this lifecycle.

## Addendum-first reading order

When onboarding onto a Go + HTMX repo:

1. `addenda/go-htmx.md` §'Stack laws' — dialog-guard law
   first; it's the failure mode that bites first.
2. `addenda/go-htmx.md` §'Framework quirks' — the
   `hxAttr(el, name)` helper rule + the `htmxattr.Mux`
   string-vs-SafeURL gotcha. Both prevent real bugs.
3. `core/laws.md` — the universal laws apply; the addendum
   adds stack-specific ones.
4. The addendum's 'Bug catalog §1.*' (Frontend wiring) and
   'Bug catalog §4.*' (Backend handlers) — in order; the
   §1 sections are the lower-hanging-fruit bugs.
5. `addenda/go-htmx.md` §'HTMX-specific guard tests' — the
   starter set an adopter should add first.

Skip the §5 (Build / CI), §6 (Database), and the §3-* JS bugs
on first read. They're tier-1 for when you're working *in*
those layers; tier-2 for general orientation.

## Failure-mode catalogue

The "I burned fingers on this" snippets from the
`docs/audit/pragmatic-programmer-audit-2026-07.md` per-tier
tip rows (when the evidence cited the Go + HTMX stack). These
are the rules the audit found implicit but not pinned:

- **Tip #19 *Forgo Following Fads*** — implicit in the
  templ + chi + goldmark choices; *no* written policy. If
  a future PR proposes a 'rewrite in Go + React Router'
  migration, the *cited* stack rationale is the only
  defense.
- **Tip #31 *Failing Test Before Fixing Code*** — pinned
  by `core/tdd.md`, but the Go-specific worked example
  is `tools/tune/snapshot_test.go`. Read it; the
  per-iter SQL footprint doc-comment pattern is the local
  operational form.
- **Tip #34 *Don't Assume It — Prove It*** — the
  `tools/tune/snapshot_test.go` per-iter SQL footprint
  doc-comment is the worked example. Read §1.12 Algorithm
  Speed in `core/pragmatic-principles.md` for the why.
- **Tip #40 *Finish What You Start*** — the defer pattern
  is the Go-specific form. Read the `defer` linter in the
  starter set; missing defers are a recurring class.
- **Tip #47 *Avoid Global Data*** — the Wails `App`
  struct is per-process (one per app launch); the
  dialog-guard mutex is per-`App`, not global. The pattern
  scales to `internal/jobs` workers.
- **Tip #48 *If It's Important Enough To Be Global, Wrap It
  in an API*** — the `(*App).guardedSaveFileDialog`
  wrapper is the canonical example. The dangerous thing
  (the Wails dialog call) is wrapped behind a safe API.
- **Tip #53 *Shared State Is Incorrect State*** — the
  per-slot mutex pattern (LoadOrStore + defer Delete) is
  the worked example. See `core/laws.md` §'No unguarded
  re-entrant UI calls' for the law.
- **Tip #54 *Random Failures Are Often Concurrency
  Issues*** — `audit/race-stress.yml` workflow +
  `internal/dates` property-test gate. Run the stress
  suite; don't trust single-thread unit tests for
  background work.

## References

- `addenda/go-htmx.md` — the addendum this entry complements
- `core/pragmatic-principles.md` §'warn + cite protocol' —
  the violation documentation rule
- `docs/audit/pragmatic-programmer-audit-2026-07.md` — the
  per-tip evidence per rows cross-referenced above
