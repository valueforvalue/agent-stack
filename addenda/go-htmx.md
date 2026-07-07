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
specific paths must come before wildcards (`/soldiers/search`
before `/soldiers/*`). A route guard test catches
re-orderings that violate this.

### Redirect contract for click-driven forms

The custom dispatcher (`dispatchDixieDataForm` in
`frontend/app.js`) replaces the legacy parallel `request()`
function. Handlers return `200 OK + X-DixieData-Redirect`,
the dispatcher reads the header, and `window.location.assign()`
navigates the user. Templates use `data-dixie-submit` +
`action=` (instead of `hx-post` / `hx-put` / `hx-delete` for
click-driven forms).

**New handlers keep forgetting the contract.** The
`X-DixieData-Redirect` header must be set BEFORE the response
body is written. Use the `writeExportRedirect(w, ...)` helper
to enforce this.

## Bug catalog (Go + HTMX)

The catalog below is a focused subset of the per-layer bug
patterns. Each entry: symptom, why, `Find it:` grep, fix.

### 1. Frontend wiring (htmx + templ)

#### 1.1 Button doesn't submit because `type="submit"` is missing

**Symptom:** User clicks button. Nothing happens. Network
tab shows no request.

**Why:** HTML default for `<button>` inside a `<form>` is
`type="submit"`, but `<button>` outside a `<form>` defaults
to nothing.

**Find it:**
```bash
grep -rn '<button ' internal/templates/*.templ | grep -v 'type='
```

**Fix:** Add `type="submit"` to the button, OR wrap the
form around it explicitly.

#### 1.2 Form inputs not wired to htmx polling because not inside a `<form>`

**Symptom:** User types in a search input. Results don't
refresh.

**Why:** htmx's `hx-trigger="keyup"` needs to be inside a
`<form>` so the submit event is intercepted.

**Find it:**
```bash
grep -B 1 -A 2 'hx-trigger="keyup' internal/templates/*.templ
```

**Fix:** Wrap the input in `<form hx-get="..." hx-trigger="...">`.

#### 1.3 htmx-swap destroys JS event listeners

**Symptom:** Click handler works on first page load. After
any htmx navigation, the handler is dead.

**Why:** `addEventListener` binds at DOM-creation time. When
htmx replaces the parent element, the listener is GC'd
along with the removed node.

**Find it:**
```bash
grep -rn "addEventListener" frontend/app.js
```

**Fix:** Use `onclick="..."` inline attributes that survive
swap, OR delegate the listener to a stable ancestor (e.g.
`document`).

#### 1.4 In-flight requests race with newer ones

**Symptom:** User types fast. Old search results replace
newer ones.

**Why:** Without `hx-sync`, htmx fires a new request on every
keystroke but doesn't cancel the previous one.

**Find it:**
```bash
grep -rn 'hx-trigger="keyup' internal/templates/*.templ | grep -v "hx-sync"
```

**Fix:** Add `hx-sync="this:replace"` to the form. Or
`hx-sync="this:abort"` to fully abort.

#### 1.5 Polling fragment stops refreshing after job completes

**Symptom:** Progress bar updates every 2s while job runs.
After job completes, polling doesn't stop — it keeps firing
against a terminal-status job.

**Why:** The polling fragment needs a conditional
`hx-trigger`. When the job hits a terminal state, the
fragment should switch to `hx-trigger="none"`.

**Find it:**
```bash
grep -B 2 -A 8 'JobStatusFragment' internal/templates/jobs.templ
```

**Fix:** Add the conditional trigger in the templ block.

#### 1.6 Double-click produces duplicate async work

**Symptom:** User double-clicks "Export PDF". Two exports
run. Toast shows success twice.

**Why:** No debounce on the button. htmx doesn't inherently
dedupe rapid clicks.

**Find it:**
```bash
grep -rln 'hx-post="/export/' internal/templates/*.templ
```

**Fix:** Add a debounce in the Go handler (check job
registry for in-flight job with same kind + params), OR
add a JS click guard that disables the button after first
click.

#### 1.7 Redirect loop on certain routes

**Symptom:** Browser hangs loading `/jobs/...`. Network tab
shows 302 → 302 → 302 chain.

**Why:** Middleware redirects a route to itself. Common when
`/jobs/*` is wildcard-matched but the middleware matches too
broadly.

**Find it:** Walk the redirect middleware logic. Find the
matching chain.

**Fix:** Tighten the route pattern OR add a guard condition
to skip the redirect for already-redirected paths.

#### 1.8 htmx swap target doesn't exist or is detached

**Symptom:** Click fires. Request succeeds. Nothing visible
changes. No error in console.

**Why:** `hx-target="#some-id"` references an ID that either
doesn't exist in the rendered HTML, or was detached by a
prior swap.

**Find it:**
```bash
grep -rn 'hx-target="#' internal/templates/*.templ
```

**Fix:** Either render the target in the endpoint response,
or change `hx-target` to a stable parent.

**Defensive tooling:** `internal/templates/hx_guard_test.go`
warns about ad-hoc `#id` selectors that aren't in the
`internal/uiids.Registry`.

#### 1.12 Polling fragment wipes the whole layout because `hx-target` inherits from `<body>`

**Symptom:** Page loads briefly with the full layout, then
blanks out.

**Why:** `frontend/index.html` declared
`<body hx-get="/calendar" hx-trigger="load" hx-target="body"
hx-swap="outerHTML">`. htmx resolves inherited
`hx-target="body"` for inner polling elements, so a polling
response innerHTML-swaps the entire body.

**Find it:**
```bash
grep -rn 'hx-trigger' internal/templates/*.templ | grep -v 'hx-target'
```

**Fix:** Add `hx-target="this"` to the polling wrapper.

**Regression net:** `internal/templates/layout_test.go` →
`TestLayoutReviewCountBadgeTargetsItself`.

#### 1.13 Pre-mux placeholder cascades into an infinite layout stack

**Symptom:** During the brief window between the Wails
process starting and the chi router being ready, the
layout's polling fragments return the startup placeholder.
htmx innerHTML-swaps it, the placeholder's body carries
its own htmx triggers, and the next poll returns the same
placeholder. Each cycle stacks a fresh `<div class="app-shell">`
inside the previous one.

**Why:** `App.ServeHTTP` falls through to
`renderStartupPlaceholder` whenever `a.mux == nil`. The
placeholder is a full HTML doc with `hx-*` attributes.

**Fix (two-part):**
- (a) Detect htmx fragment requests via the `HX-Request`
  header and return `204 No Content`.
- (b) Drop `hx-get` / `hx-trigger` / `hx-target` / `hx-swap`
  attributes from the placeholder's `<body>`.

#### 1.14 Polling fragment cascades during setup / recovery / startupErr blocks

**Symptom:** During setup-required, pending recovery, or
fatal startup error, polling fragments that aren't in the
allowlist get redirected (303) or errored (500). The
browser follows the redirect to the block page (full HTML
doc), and htmx innerHTML-swaps it into the badge wrapper.

**Why:** Every blocked-state branch in `App.ServeHTTP`
returns a redirect or error unconditionally.

**Find it:**
```bash
grep -n 'http.Redirect\|http.Error' internal/appshell/lifecycle.go
```

**Fix:** Detect `HX-Request: true` in each blocked branch
and return `204 No Content` with `X-DixieData-Redirect`
pointing at the destination page.

#### 1.9 [REGRESSION-PRONE] POST-then-navigate handler must use the redirect contract

**Symptom:** Click handler runs (side effect happens), but
the page never navigates. The user is stuck on the form
page and re-clicks, producing duplicate work.

**Why:** Handler returns 200 + toast header but forgets to
call `writeExportRedirect(w, ...)` or set
`X-DixieData-Redirect` directly.

**Find it:**
```bash
grep -rn 'StatusSeeOther\|http\.Redirect' internal/appshell/*.go \
  | grep -v _test.go | grep -v writeExportRedirect
```

**Fix:** Call `writeExportRedirect(w, routebuilder.X(...))`
before writing the response body.

### 2. View markup (templ)

#### 2.1 Stray syntax in templ output

**Symptom:** Page renders with a literal `\_ = summary`
showing on screen.

**Why:** Typos in templ code, or copy-paste of Go syntax
into a templ block.

**Find it:**
```bash
grep -rn '\\_ =\|@_' internal/templates/*.templ
```

**Fix:** Correct the templ syntax.

#### 2.3 Date/timezone handling in display

**Symptom:** Anniversary shows on the wrong day, or birthday
shows a day early/late.

**Why:** Date construction without explicit timezone.
`time.Date(...)` defaults to UTC.

**Find it:**
```bash
grep -rn "time.Date\|time.Now" internal/calendar/ internal/dates/
```

**Fix:** Pass `time.Local` or use the user's stored
timezone offset.

#### 2.4 `00` day sentinel handling

**Symptom:** Birth date "1923-00-00" renders as "January 0,
1923" or "N/A" instead of just "1923".

**Why:** Many records have partial dates recorded with
day=00 meaning "unknown day". The formatters don't always
skip the day gracefully.

**Fix:** Detect `day==0` and render year-only.

### 3. Frontend JS (app.js + app.css)

#### 3.1 Floating dock overlap / mobile overflow

**Symptom:** On mobile, content is cut off at 6px. Floating
dock overlaps the bottom content area.

**Why:** Layout chrome wasn't tested at narrow viewports.

**Fix:** Cap top-shell width; add bottom padding to main
content to clear the dock.

#### 3.2 Stale data after async response

**Symptom:** User clicks "Load Backup". Backup loads. The
shared status panel still shows the old archive contents.

**Why:** htmx swapped a fragment that didn't include the
panel, OR the handler returned 200 but didn't trigger a
refresh.

**Fix:** Either include the panel in the swap target, OR
add an explicit htmx trigger after the load completes.

#### 3.3 htmx not loaded on every page

**Symptom:** Some pages silently drop htmx behavior because
`htmx.min.js` wasn't loaded.

**Why:** Template loads htmx conditionally based on path or
feature flag.

**Fix:** Load htmx unconditionally in layout.

#### 3.4 JS submit interceptor bypasses htmx redirect

**Symptom:** A form has `hx-post` AND a `submit` event
listener that calls `event.preventDefault()`. The
`HX-Redirect` header from the server is NEVER honored.

**Why:** The JS path owns the entire submit cycle; htmx
never sees the response.

**Fix:** Pick ONE path and own it. Either delete the JS
listener and route through the redirect contract, or delete
the `hx-post` attribute and let the JS handler own the
flow. Never carry both.

#### 3.5 Stale status panel after submit

**Symptom:** User clicks a button. The handler runs, the
side effect happens, the toast displays, but the target
panel does not refresh.

**Why:** Four sub-patterns: wrong `hx-target`, no redirect
after success, response below the viewport fold, or
scan/quality results render into wrong div.

**Fix:** Per sub-pattern. Verify target id exists, add
`writeExportRedirect`, scroll panel into view, pin id with
a registry constant.

#### 3.6 Outside-click handler closes the panel the trigger just opened

**Symptom:** First click on a top-nav foldout trigger does
nothing visible. Workaround: click any other top-nav link
first, then click the trigger.

**Why:** Two click handlers fire in bubble order. The
trigger's own click handler opens the panel; the
document-level outside-click handler closes it again on
the same bubble.

**Fix:** In the document-level outside-click handler, add
`if (trigger === target || trigger.contains(target)) continue;`
at the top of the loop body.

#### 3.7 installFoldouts runs once on DOMContentLoaded

**Symptom:** First click on a top-nav foldout trigger on a
fresh cold-start does nothing. After navigating away and
back, the click works.

**Why:** `installFoldouts()` runs once on
`DOMContentLoaded`, but the trigger is rendered later by an
htmx swap. The htmx re-init hook never re-runs the install.

**Fix:** Make the install function idempotent and add it to
the htmx re-init hook (`initializeDynamicContent` or
analog).

### 4. Backend handlers

#### 4.1 Goroutine / subscription leak

**Symptom:** Over time, goroutines accumulate. Memory
grows. Eventually OOM.

**Why:** `Subscribe` to a channel creates a goroutine. If
the subscriber doesn't `Unsubscribe` when done, the
goroutine runs forever.

**Fix:** Add `defer unsub()` at the top of the goroutine.

#### 4.2 Race condition on shared state

**Symptom:** Sporadic test failures or production data
corruption. Passes 99% of the time.

**Why:** Concurrent read/write to a map or struct without a
mutex.

**Fix:** Add `sync.Mutex` around the shared state. Run
`go test -race ./...` to catch the next one.

#### 4.3 Nil-guard gap

**Symptom:** Panic on a path that's rare in dev but common
in prod.

**Why:** Code path that "always works in dev" because the
test setup pre-populates state.

**Fix:** Add the nil check, or restructure so the call
site guarantees non-nil.

#### 4.4 Dead context parameter

**Symptom:** Handler signature accepts `ctx context.Context`
but never uses it. Operations can't be cancelled.

**Why:** Refactor that added context didn't update all call
sites.

**Find it:**
```bash
grep -rn "func.*ctx context.Context" internal/appshell/ | grep -v "_test.go"
```

**Fix:** Either remove the parameter, or actually use it
(pass to DB queries, pass to HTTP clients, etc.).

#### 4.5 Setup order — middleware depends on services that haven't started

**Symptom:** On startup, the first request crashes because
service X isn't initialized yet.

**Why:** Middleware or route handler runs before
`app.Startup()` completes.

**Fix:** Move service init before the server starts, OR
add a "ready" check in middleware.

#### 4.6 SQLite BUSY under load

**Symptom:** Stress test produces intermittent `database is
locked` errors.

**Why:** SQLite serializes writers.

**Fix:** Add retry logic with backoff. Tune `busy_timeout`
PRAGMA.

#### 4.7 Build / file path — wrong dir

**Symptom:** Production build fails to find templates or
binaries that work in dev.

**Why:** Hardcoded paths from dev environment leak into
release code.

**Fix:** Use `runtime.Caller` or `os.Executable()` to anchor
the path, not `os.Getwd()`.

#### 4.8 Wails runtime guards

**Symptom:** Tests that exercise app handlers crash because
wails runtime isn't available (no frontend).

**Why:** Handler calls `runtime.EventsEmit(...)` directly.

**Fix:** Add nil-guard: `if a.runtime != nil { ... }`.

#### 4.10 Unguarded native dialog crashes the app

**Symptom:** Click "Export PDF". Native save dialog
appears, then the app dies. `crash.log` shows
`[WebView2 Error] The parameter is incorrect.` followed by
`Failed to unregister class Chrome_WidgetWin_0. Error = 1412`.

**Why:** Two `SaveFileDialog` calls land on the UI thread at
the same time. WebView2's `MoveFocus` race fires the
`go-webview2` global error callback, which is hard-coded to
`os.Exit(1)`.

**Fix:** See the dialog-guard law at the top of this
addendum. Pattern A (route through `guardedSaveFileDialog`),
Pattern B (inline `inFlight` guard), or Pattern C (sentinel
error from helper).

#### 4.11 Duplicate-job-handling

**Symptom:** User double-clicks "Export Database PDF". The
expected behaviour is one job is enqueued and the second
click navigates to the existing `/jobs/{id}`. The actual
failure modes: second click produces a second job, second
click returns an error body, second click sees a stale
registry.

**Fix:** Only `defer a.inFlight.Delete(dupKey)` on the
happy path. Preserve the in-flight map across registry
reloads. Add the `if dupJob != nil { writeExportRedirect(...); return }`
branch as the first thing the handler does after dedup.

#### 4.12 Toast header encoding (mojibake)

**Symptom:** Toast displays Unicode characters (ellipsis,
em-dash, smart quotes) as mojibake (`â€¦`, `â€"`).

**Why:** Chromium's WHATWG Fetch decodes HTTP/1.x response
headers as Windows-1252 by default.

**Fix:** Route every `X-DixieData-Toast` write through a
`sanitiseToastForHeader` helper that translates polished
Unicode to ASCII twins at the header boundary. Source keeps
the polished characters.

#### 4.13 Route misregistered or wrong verb

**Symptom:** A clickable button or form posts and the
server returns 405 with no error in the UI.

**Why:** New routes are registered against the chi router.
When a handler is refactored (POST → DELETE), the route
registration can drift.

**Fix:** Match the HTTP method to the handler's allowed
methods. Use the chi route table guard test.

#### 4.16 Fragment-204-no-client-listener

**Symptom:** Fresh app load with `setupRequired=true` shows
a white page with no nav, no CSS, no content. The browser
console is clean.

**Why:** Wails serves raw `frontend/index.html` as the
initial document. htmx fires the load request with
`HX-Request: true`. If the server is in a blocked state, it
writes `204 + X-DixieData-Redirect`. htmx receives a 204,
does not swap, and the body stays empty.

**Fix:** Add an `htmx:afterRequest` listener that reads
`X-DixieData-Redirect` from any 204 response and calls
`window.location.assign(redirect)`. Single hook covers all
blocked states.

#### 4.17 Open handle in data dir blocks restore

**Symptom:** A `.ddbak` (or analog backup) restore fails
with `Access is denied` when DixieData.exe has
`jobs.jsonl` open inside the data dir.

**Why:** DixieData.exe holds the handle alive for the
lifetime of the process. On Windows, an open handle on any
descendant file blocks the parent directory's rename.

**Fix:** Convention: the data dir contains ONLY the SQLite
database + the image store. All app-level state (logs,
caches, WALs) MUST live under `appdata.LogsDir(dataDir)`,
the sibling logs directory.

#### 4.20 Backend-first landing

**Symptom:** A feature is declared "shipped" in a PR. The
user runs the app and cannot find the feature anywhere.

**Why:** The feature is decomposed into a "data layer"
commit and a "UI layer" commit, the data layer lands first,
the PR is opened and merged, and the UI layer slips.

**Fix:** Don't ship backend-only PRs for features. Mirror
the issue's apply-sites checklist in the PR description
and tick boxes as commits land. Run
`audit/discover_orphan_handlers.mjs` (or analog) in CI.

### 5. Build / CI

#### 5.1 PowerShell `$?` vs `$LASTEXITCODE`

**Symptom:** CI step runs `Expand-Archive` which returns
success but sets `$LASTEXITCODE` differently. Subsequent
step fails.

**Fix:** Use `$?` (the boolean success indicator) instead of
`$LASTEXITCODE` for the previous command's success.

#### 5.2 Build flag not passed

**Symptom:** A script's `-Root` flag is needed for some
path operations. CI doesn't pass it.

**Fix:** Audit every script's flags against CI invocation.

#### 5.3 Windows-native extraction tool

**Symptom:** Cross-platform tar.exe extraction differs from
PowerShell's `Expand-Archive`. Subtle differences in path
handling.

**Fix:** Use the right tool for the right artifact.
PowerShell for .zip, tar.exe for .tar.gz.

### 6. Database

#### 6.1 FTS5 delete not actually deleting

**Symptom:** Person Record updates leave stale entries in
the FTS5 index. Search returns ghost results.

**Why:** FTS5 needs explicit delete when the row changes.

**Fix:** Wrap UPDATE in a transaction that deletes the old
FTS row and inserts the new one.

#### 6.2 Normalization mismatch

**Symptom:** Filtering by state="Virginia" returns results
for "VA" too, but not for " virginia" (with leading space).

**Why:** Filter doesn't normalize before comparing.

**Fix:** Normalize via the canonical normalizer before the
where clause.

## Bug class → first place to look

Quick reference table for Go + HTMX apps:

| Symptom | First place to look |
|---|---|
| Click does nothing | §1.1 button type / §1.2 form wrap |
| Click fires but nothing changes | §1.8 htmx target missing |
| Worked before, broken after navigation | §1.3 listener destroyed by swap |
| Stale results | §1.4 hx-sync missing |
| Progress keeps polling | §1.5 terminal-state trigger |
| Handler runs, toast shows, page doesn't navigate | §1.9 redirect contract |
| Double-click produces duplicate job | §4.11 dedup helper / in-flight slot |
| Toast shows mojibake | §4.12 HTTP header charset |
| 405 from a clickable form | §4.13 wrong HTTP method |
| Floating dock covers content | dock height + padding drift |
| Panic on rare path | §4.3 nil guard |
| Goroutine leak | §4.1 missing Unsubscribe |
| Date wrong by 1 day | §2.3 timezone |
| Output missing references | dataDir resolution |
| Search returns ghost | §6.1 FTS5 sync |
| Works in dev, fails in release | §4.7 hardcoded paths |
| Tests crash on missing frontend | §4.8 wails runtime nil |

## References

- `../core/laws.md` — universal laws
- `../core/code-changes.md` — cross-layer working contract
- `../core/bug-patterns.md` — stack-agnostic catalog
- Wails v2 upstream: <https://github.com/wailsapp/wails>
- HTMX: <https://htmx.org/>
- templ: <https://templ.guide/>
- chi router: <https://github.com/go-chi/chi>