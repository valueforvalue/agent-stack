# Bug Patterns — Stack-Agnostic Catalog

This document captures recurring bug patterns at a high
level. The per-layer specifics live in the addendum for the
target stack.

The patterns are grouped by where the bug lives in the
stack: **frontend wiring** (view + framework attributes),
**view markup**, **frontend JS**, **backend handlers**, and
**build / CI**. A final section covers debugging workflow.

Adopting repos should extend this catalog with their own
stack-specific patterns in their addendum.

## The meta-patterns (every stack)

### Drift between layers

Two halves of one system drifted apart; the bug surfaced
only at runtime. See [`code-changes.md`](code-changes.md)
for the working contract that prevents this.

### Invoker wiring gap

UI button calls a helper that queries the DOM for a target
element, gets `null`, and silently early-returns. The
feature is fully implemented server-side but the user sees
no feedback. The fix is always: a smoke probe that asserts
the target element is in the DOM AND not in a hidden state.

### Response-shape mismatch

Handler is registered but the response shape doesn't match
what the client expects. The client follows a redirect to
raw HTML, or parses JSON as a navigation, or vice versa.
The fix is always: a handler test that asserts response
status, content-type, and key body fields.

### Orphan handler / fragment-as-redirect

A handler ships with no caller, OR a fragment endpoint's
HTML is followed as a navigation because a header told the
client to redirect. The fix is always: an orphan-handler
probe that walks the route table against client invokers.

### Adjacent race / state-machine collision

The slice's own click handler does the right thing, but a
different handler attached to a higher-priority event
reacts to the same event and undoes the work. The fix is
always: a smoke probe that asserts the state 50–200ms
after the click, after the event has fully bubbled.

### Unguarded re-entrant UI call

If a UI operation opens a native dialog, modal, file
picker, or any other re-entrant surface, a second
invocation while the first is still open must be rejected
before it reaches the host. See [`laws.md`](laws.md) §"No
unguarded re-entrant UI calls".

### Date / timezone handling

Anniversary shows on the wrong day, or birthday shows a
day early/late. Date construction without explicit
timezone; the formatter defaults to UTC. The fix is
always: pass the user's stored timezone offset.

### Goroutine / subscription / handle leak

Over time, background work accumulates. Memory grows.
Eventually OOM. The fix is always: a `defer cleanup()` at
the top of the goroutine / handler.

### Nil-guard gap

Panic on a path that's rare in dev but common in prod.
Code path that "always works in dev" because the test setup
pre-populates state. The fix is always: add the nil check,
or restructure so the call site guarantees non-nil.

### Hardcoded paths

Production build fails to find files that work in dev.
Hardcoded paths from dev environment leak into release
code. The fix is always: use `runtime.Caller` /
`os.Executable()` to anchor the path.

## Debugging workflow

When you see a regression, work this checklist in order:

### 1. Identify the layer

Before reading code, name the layer:

- Did the user click something? → frontend wiring.
- Did a page render wrong? → view markup.
- Did a button or toggle stop working after navigation? →
  framework-swap destroyed a listener.
- Is it slow / hangs? → backend. Check for leaks, race
  conditions, lock timeouts.
- Is it an export / file output? → output formatter.
- Screen reader broken? → accessibility.
- Build / CI failure? → build / CI.

### 2. The four diagnostic commands

```bash
# What's currently in this template?
grep -n 'framework-attr\|@\|render ' <view files>

# What template renders a URL? (catches wrong-selector class)
go test <view-package> -run TestAttributeURLsUseBuilders -v

# Is the boundary intact? (catches architectural drift)
go test <architecture-package> -v

# Are there races?
go test -race ./...
```

### 3. Three files to read first when a regression appears

1. The attribute-URL guard test — is the URL going through
   a builder?
2. The architecture-boundary test — is the import
   boundary still intact?
3. The recent commits touching the affected file.

### 4. When to add a regression test

If a bug was found by accident (manual testing, code
review, prod report) and the fix is non-obvious, **add a
snapshot or behavioral test that would have caught it.**
This is what codifies "we already burned fingers on this."

## Bug class → first place to look

Quick reference table for "the page does X wrong, where's
the bug":

| Symptom | First place to look |
|---|---|
| Click does nothing | Frontend wiring: button type / form wrap |
| Click fires but nothing changes | Frontend wiring: target missing |
| Worked before, broken after navigation | Framework-swap destroyed listener |
| Stale results | Sync directive missing |
| Progress keeps polling | Terminal-state trigger missing |
| Handler runs, toast shows, page doesn't navigate | Redirect header missing |
| Form submits, server runs, JS post-response ignored | Dispatcher opt-in attribute missing |
| Double-click produces duplicate work | Dedup helper / in-flight slot |
| Toast shows mojibake | HTTP header charset |
| 405 from a clickable form | Wrong HTTP method on route |
| Floating overlay covers content | Overlay height + padding drift |
| Panic on rare path | Nil guard |
| Background work leak | Missing cleanup |
| Date wrong by 1 day | Timezone |
| Output missing references | Data-dir resolution |
| Search returns ghost | Index sync |
| Screen reader silent | ARIA missing |
| Mobile layout broken | Viewport test |
| Memory grows over time | Leak / race |
| Works in dev, fails in release | Hardcoded paths |

For stack-specific patterns and copy-paste greps, see
the addendum for the target stack.

## References

- [`code-changes.md`](code-changes.md) — cross-layer working
  contract
- [`laws.md`](laws.md) — non-negotiable laws
- The addendum for the target stack (`addenda/<stack>.md`)