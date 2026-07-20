# Go + HTMX + templ + chi + Wails Addendum

Stack-specific patterns for a Go-rendered templ + HTMX + chi
router + Wails / WebView2 host. This is the canonical
addendum — the most-tested, most-exercised in the
agent-stack.


## Stack laws (non-negotiable)

These extend the universal laws in `../core/laws.md`. They
were earned by real bugs in shipped code.

### Every native dialog call is guarded against re-entry

Wails v2.12.0 on Windows runs every native `SaveFileDialog`
and `OpenFileDialog` on the UI thread. If two of them land
on the message loop at the same time, WebView2 loses focus
while the Wails `onFocus` handler calls `Chromium.Focus()`
→ `MoveFocus()` and the frontend process dies with
`Chrome_WidgetWin_0. Error = 1412`. The double-click is
enough.

The contract:

- Every HTTP handler that calls `a.SaveFileDialog` /
  `a.OpenFileDialog` / `a.OpenDirectoryDialog` /
  `a.OpenMultipleFilesDialog` MUST guard the call with
  `a.inFlight.LoadOrStore(dupKey, struct{}{})` and `defer
  a.inFlight.Delete(dupKey)`.
- Every Wails binding that opens a native dialog from JS
  MUST go through a Go helper that carries the same guard.
- The guard key must be unique enough to distinguish
  concurrent exports of different kinds but stable enough to
  collapse duplicate clicks on the same button. Use
  `kind|filename|filters` or the equivalent.
- The slot is released AFTER the dialog returns (`defer
  Delete`), never before. Releasing early re-opens the race.

**Three patterns for the guard:**

#### Pattern A — route through `guardedSaveFileDialog`

```go
func (a *App) guardedSaveFileDialog(kind string, opts runtime.SaveDialogOptions) (string, bool) {
    dupKey := fmt.Sprintf("export|%s|%s|%v", kind, opts.DefaultFilename, opts.Filters)
    if _, loaded := a.inFlight.LoadOrStore(dupKey, struct{}{}); loaded {
        return "", false
    }
    defer a.inFlight.Delete(dupKey)
    path, err := a.SaveFileDialog(opts)
    if err != nil || path == "" {
        return "", false
    }
    return path, true
}
```

Use this when you can express the dedup key as
`kind + filename + filters`. The kind prefix keeps two
different exports independent.

#### Pattern B — inline `inFlight` guard

For call sites that need a more specific key, copy the
inline shape:

```go
dupKey := fmt.Sprintf("kind|%s", uniqueIdentifier)
if _, loaded := a.inFlight.LoadOrStore(dupKey, struct{}{}); loaded {
    debug.FromContext(r.Context()).Debug("handlerName duplicate request rejected")
    respondError(w, r, KindUnavailable,
        "Export already in progress; please wait for the save dialog.", nil)
    return
}
defer a.inFlight.Delete(dupKey)

path, err := a.SaveFileDialog(runtime.SaveDialogOptions{ /* ... */ })
```

#### Pattern C — guard helper that returns a sentinel error

For helpers called from both an HTTP handler and a Wails
binding, return a sentinel error and map it at the call
site:

```go
var errExportInFlight = errors.New("export already in flight")

func exportFullDatabasePDFPath(...) (string, error) {
    if _, loaded := a.inFlight.LoadOrStore(dupKey, struct{}{}); loaded {
        return "", errExportInFlight
    }
    defer a.inFlight.Delete(dupKey)
    // ...
}
```

### Every templ `hx-*` URL goes through a routebuilder

`internal/routebuilder.X()` is the typed builder for URLs.
Prefer it over raw string literals — the goquery guard test
flags bare `hx-get="/foo"` strings as a code smell.

### Every persistent DOM surface ID is in the registry

`internal/uiids.Registry` carries every persistent surface
ID (panel, region, modal, overlay) the view templates
reference. Ad-hoc selectors are allowed but emit a warning
during `make tpl`.

### Exported Go identifiers carry doc comments

Go-specific version of the universal law. The doc comment:

- Starts with the identifier name (the `go doc` synopsis
  line is the first sentence).
- Explains the contract, not the implementation.
- Lives immediately above the declaration, with no blank
  line between the comment and the identifier.

CI regression gate: enforce a 70% coverage floor on every
package under `internal/` and `pkg/` with ≥5 exported
identifiers. Run `go test ./internal/buildinfo/ -run
TestPerPackageDocCoverageFloor` to verify.


## Framework quirks

### The htmx attr strip in app.js

At `DOMContentLoaded`, `frontend/app.js` strips `hx-get`,
`hx-post`, `hx-put`, `hx-delete`, `hx-trigger`, `hx-confirm`,
`hx-include` from every element in the DOM. The strip exists
to prevent htmx's auto-handler from double-firing alongside
app.js's own `request()` / `queueRequest()` handlers.

**Before stripping, the file caches each attr to a
`data-hx-*` mirror.** All the JS handlers (`getMethod`,
`getUrl`, `request`, `queueRequest`, `triggerInputRequest`)
read via the `hxAttr(el, name)` / `hxHas(el, name)` helpers,
which prefer the live attr and fall back to the mirror.

Implications:

- Use `hxAttr(el, name)` and `hxHas(el, name)` instead of
  `el.getAttribute(name)` / `el.hasAttribute(name)` for any
  `hx-*` attribute. Direct reads return `null` / `false`.
- Use `[hx-X], [data-hx-X]` in `closest()` selectors.
- Don't re-introduce the strip. If you find yourself tempted
  to re-add `el.removeAttribute("hx-X")` somewhere, the
  right answer is `e.stopImmediatePropagation()` instead.

### `htmxattr.Mux` returns plain `string` for URL values

`templ.RenderAttributes` type-switches on `string`, `*string`,
`bool`, etc. but NOT on `templ.SafeURL`. When an attribute
value is a `SafeURL`, `RenderAttributes` silently drops the
attribute. Symptom: every `hx-get` / `hx-post` button
renders without those attrs and clicks do nothing.

The fix is structural: `htmxattr.Mux.Attrs()` returns
`string`, never `templ.SafeURL`. Tests that assert
`templ.SafeURL` in the value pass — they don't exercise
`RenderAttributes`. Smoke probes are the only thing that
catches this.

### Route registration order

The chi router walks the route table in registration order;
specific paths must come before wildcards (`/records/search`
before `/records/*`). A route guard test catches
re-orderings that violate this.

### Redirect contract for click-driven forms

The custom dispatcher (`dispatchAppForm` in
`frontend/app.js`) replaces the legacy parallel `request()`
function. Handlers return `200 OK + X-App-Redirect`,
the dispatcher reads the header, and `window.location.assign()`
navigates the user. Templates use `data-app-submit` +
`action=` (instead of `hx-post` / `hx-put` / `hx-delete` for
click-driven forms).

**New handlers keep forgetting the contract.** The
`X-App-Redirect` header must be set BEFORE the response
body is written. Use the `writeExportRedirect(w, ...)` helper
to enforce this.


## Go testing recipes

> Sibling of [`../core/testing-philosophy.md`](../core/testing-philosophy.md).
> The core doc gives the *bar* (which tests earn their place);
> this section gives the *Go-specific recipes* that meet it.

### 1. `var _ Foo = bar` is a declaration, not a test

Per core §"Compile-time checks masquerading as runtime tests":
package-level only. Never inside `func Test...`.

```go
// GOOD — package-level, zero runtime cost
var _ render.Renderer = (*TemplView)(nil)

func TestTemplView(t *testing.T) { ... }

// BAD — inflates test count, runs `go test` machinery
func TestImplementsRenderer(t *testing.T) {
    var _ render.Renderer = (*TemplView)(nil)
}
```

### 2. Build-tag convention for diagnostic probes

Per core §"Diagnostic tests that always skip":
file-existence / binary-built / env-var-gated tests live
under `//go:build diag`.

```go
//go:build diag
package mypkg

func TestLiveBinarySmoke(t *testing.T) {
    if _, err := os.Stat("bin/myapp.exe"); err != nil {
        t.Skip("binary not built")
    }
    // ...
}
```

Run with: `go test -tags=diag ./...`. The CI matrix runs
both the default and `diag` suites on a schedule (not on
every PR) to keep signal high and cost bounded.

### 3. Table-driven consolidation for per-surface tests

Per core §"Consolidation": N per-surface render or
handler tests that share shape collapse into one
table-driven test. The table IS the coverage map.

```go
func TestSurfaceIDs(t *testing.T) {
    cases := []struct {
        name string
        path string
        want []string
    }{
        {"landing", "/", []string{"#app", "#toast"}},
        {"settings", "/settings", []string{"#app", "#settings-foldout"}},
        // add a row per new surface, not a new func
    }
    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            rec := serveGET(tc.path)
            for _, id := range tc.want {
                if !strings.Contains(rec.Body.String(), id) {
                    t.Errorf("missing surface %s", id)
                }
            }
        })
    }
}
```

**When NOT to consolidate** (per core §"Consolidation"):
each test exercises a genuinely different code path. The
HTMX-specific guard tests in §"HTMX-specific guard tests"
below are an example — each test owns a different invariant
(route-table integrity vs response-shape contract vs swap
re-binding), so they stay separate even though they all
serve HTTP.

### 4. Mutation testing

Per core §"Test-the-tests" (Tip #64): `go-mutesting` is
the Go-specific operational form. See §"Mutation testing"
above for the workflow + `.mutesting.yaml`. The mutation
score is the *complement* to line coverage: a test file at
100% line coverage with a 20% mutation score is testing
coverage inflation, not state coverage.

### 5. Stdlib re-test anti-pattern

Cut any test whose core assertion is "the stdlib function
works as documented." Examples from the audit (issue
#626):

- Wrapping `sync.Map.LoadOrStore` and asserting the
  documented return value — test the *wiring* (your code
  calls `LoadOrStore` with the right key), not the
  function itself.
- Wrapping `strings.Contains` and asserting `true` for a
  string that obviously contains the substring.
- Wrapping `fmt.Sprintf` and asserting a known formatted
  output.

**Decision rule:** if you can replace the stdlib call in
the test with the literal expected value and the test
still passes, the test is testing the stdlib, not your
code. Cut it.

### 6. Brittle-test mitigation in Go

Per core §"Brittle tests": assert on structural
properties, not exact strings. In Go this usually means:

- `strings.Contains(body, "data-theme=\"high-contrast\"")`
  not `body == "<html lang=\"en\" data-theme=\"high-contrast\"...>"`.
- Use the existing `htmxattr.Mux` allowlist rather than
  asserting on rendered `hx-*` attribute strings.
- For snapshot tests: pin the *byte-stable primitives*
  (per `core/complexity.md` §1.10's imposed-duplication
  carve-out), not the full render output of a screen.

### References

- [`../core/testing-philosophy.md`](../core/testing-philosophy.md)
  — the bar this section implements
- §"Mutation testing" above — `go-mutesting` workflow
- §"HTMX-specific guard tests" below — already follows
  the philosophy doc's "static checks → linters" rule
- §"Exported Go identifiers carry doc comments" above —
  the doc-comment floor the carve-outs in §1 and §5
  depend on


## HTMX-specific guard tests

The patterns below are guard tests you write *before* the
slice lands, not after. Each one fails the moment the
listed shape of drift appears. Borrowed from
[Innei's LobeHub Next.js → Hono migration field report](https://innei.in/en/posts/tech/nextjs-shell-hono-backend-migration)
(the *route-shell guard test* is the reference architecture)
and [HTMX issue #3300](https://github.com/bigskysoftware/htmx/issues/3300)
(the after-swap re-binding gotcha).

### 1. Route-table integrity (chi ↔ templates, both directions)

**The bug.** Two halves of the system drifted: a handler
was added (or removed, or refactored) and the corresponding
template attribute was not updated. Or vice versa. The Innei
pattern iterates every route file and asserts each contains
only imports + handler-forward exports — any logic that
creeps back fails CI.

For Go + HTMX, the analogous test runs both directions:

**Forward (handlers → templates).** Build a set of
`chi.RoutePattern`s from the router. For every handler,
assert at least one template references one of its URLs
through the typed URL builder. Handlers with no caller are
orphaned.

**Reverse (templates → handlers).** Walk every rendered
HTML for `hx-get="..."` / `hx-post="..."` / `hx-put="..."`
attributes. Assert each target path is registered in the chi
router. Templates referencing unregistered routes are the
"click does nothing" bug class.

Both tests use the typed URL builder as the shared
vocabulary — a raw `hx-get="/soldiers/search"` string
bypasses the builder and breaks the test. That's the
point: raw strings force maintainers to update the
guard.

### 2. Response-shape contract (handler struct ↔ HTML)

**The bug.** Handler returns the right status code with the
wrong fields, or the template renders a data attribute the
handler doesn't emit. Tests that assert response status +
content-type alone don't catch this.

The fix is a struct-to-template assertion: for each
handler+template pair, assert that every `{{ .Field }}` in
the template's typed render corresponds to a field on the
handler's returned DTO. Mismatches are the
*response-shape mismatch* pattern in the meta-catalog.

### 3. Swap-scope re-binding test (HTMX #3300)

**The bug.** A click handler works on first page load,
breaks after the first swap. The cause is that the
listener was attached during boot to elements that htmx
later replaced via `hx-swap="outerHTML"`. The
[canonical HTMX issue #3300](https://github.com/bigskysoftware/htmx/issues/3300)
documents that `afterswap` fires only on the swap *target*,
not on the swapped-out region's former listeners.

The test:

- For each template region that uses `hx-swap="outerHTML"`,
  assert that any `addEventListener` call inside the
  region is either:
  - Rewritten as `hx-on::after-swap="..."`, OR
  - Delegated to a stable ancestor (`document`,
    `<body>`, or a region that is never swapped), OR
  - Bound to an element explicitly marked
    `hx-on::load="install()"` + `hx-on::after-swap="install()"`
    symmetrically.

This is the additive form of the §3.3 / §3.7 entries
above: the *catalogue* says "use `hx-on::after-swap`"; the
*guard test* enforces it.

### 4. OOB target integrity

**The bug.** A handler returns an OOB (out-of-band) swap
that names a target by id, but no element with that id is
in the current DOM. The swap silently does nothing.

The test asserts: for every `hx-swap-oob="id:X"` (or the
templ equivalent), the id is registered in
`internal/uiids.Registry`. Bare string IDs in OOB swaps are
a code smell; the test catches them.

### 5. Route-order wildcard ordering (chi-specific)

**The bug.** `chi` walks the route table in registration
order; wildcards swallow too eagerly. A common symptom is
a wildcard handler `/{prefix}/*` registered *before* the
specific path `/{prefix}/{id}/edit`. The specific path
becomes dead code.

The test asserts: for any wildcard pattern
`/.../*` registered at depth N, no more specific pattern
sharing the same prefix exists at depth > N. That is,
specifics must come first. This generalises the §1 in
the meta-catalog and the "Redirect loop" §1.7 entry.


## Adopting these tests

A minimal starter set for a Go + HTMX + templ + chi repo:

1. `internal/router/route_table_test.go` — forward + reverse
   route integrity (guard test #1).
2. `internal/templates/response_shape_test.go` — handler
   struct ↔ template field contract (guard test #2).
3. `internal/templates/swap_scope_test.go` — outerHTML
   regions have correct re-binding discipline (guard test
   #3).
4. `internal/templates/oob_integrity_test.go` — OOB targets
   are in `uiids.Registry` (guard test #4).
5. `internal/router/route_order_test.go` — specifics before
   wildcards (guard test #5).

The starter set reads as a deployment contract: when a
slice lands a new route, a new template, or a new OOB
target, exactly one of these tests changes. If you change
code without changing a test, you've shipped uncovered
behaviour.

## References

- `../core/laws.md` — universal laws
- `../core/code-changes.md` — cross-layer working contract
- `../core/bug-patterns.md` — stack-agnostic catalog
- Wails v2 upstream: <https://github.com/wailsapp/wails>
- HTMX: <https://htmx.org/>
- templ: <https://templ.guide/>
- chi router: <https://github.com/go-chi/chi>

