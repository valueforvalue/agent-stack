# Pragmatic Principles — A Field Guide

> **Audience:** every agent that lands on a slice. Load this doc
> when designing a new feature, refactoring, reviewing a PR, or
> debugging a recurring class of bug.

This is the agent-stack port of DixieData's
`docs/agents/pragmatic-principles.md`. The principle spine comes
from _The Pragmatic Programmer, 20th Anniversary Edition_ (Hunt &
Thomas). The "When you might violate" lists are populated from
the adopting repo's own evidence — see the last section for how
to grow this doc.

## What this doc is

A **guide**, not a law set. The principles below come from
_The Pragmatic Programmer_. They are the *why* behind the
repo's existing rules: the architecture forbidden-import test
enforces **orthogonality**; the
[`complexity.md`](complexity.md) deep-module rule enforces
**decoupling**; the
[`feature-protocol.md`](feature-protocol.md) slice discipline
enforces **tracer bullets**; the
[`commit-and-branch.md`](commit-and-branch.md) commit-shape
rules enforce **DRY at the diff level**.

The laws in [`laws.md`](laws.md) §"Laws (non-negotiable)" are
*earned by a real bug* and are not negotiable. The principles
here are *guides* — they tell you what to think about, and they
name the *known cases* where the repo legitimately violates a
principle temporarily. The agent's job is to know the principle,
know the violation pattern, and **warn + cite** before violating
it (see §"The warn + cite protocol" below).

This is a **field guide**: it tells you what to do, when to do
it, and what to do when the rule doesn't fit. It is not a
textbook. For the book-length treatment, see Hunt & Thomas.

## The warn + cite protocol

When a slice is about to **violate a principle documented here**,
the slice plan MUST name the violation explicitly. The user
signs off as part of the Plan approval gate (per
[`rpci.md`](rpci.md) §C — Critique). A documented violation is
**not a bug** — it's a *known and intentional* exception. An
**undocumented** violation is a bug. That distinction is the
whole point of the protocol.

The "Principle warnings" block in the slice plan template (see
[`feature-protocol.md`](feature-protocol.md) §"Slice plan
template") captures four pieces of information:

1. **Name the principle** in the slice Plan (the "Principle
   warnings" block).
2. **Cite the operational form** being violated (e.g. "the
   deep-module rule in `complexity.md`", "the
   forbidden-import test").
3. **State the rationale** for the temporary violation (the
   *why* — what makes this case an exception).
4. **State the cleanup plan** (when + how the violation gets
   resolved — usually a follow-up issue filed in the same slice
   commit).
5. **Land the rationale + cleanup plan verbatim in the commit
   message and the CHANGELOG bullet** so the next agent sees
   the documented violation when reading the work.

The user signs off on the violation as part of the Plan approval
gate. Violations without a documented rationale + cleanup plan
are not mergeable. This is the **enforcement mechanism** for
principles-as-guides: not a CI check (not everything is a law),
but a review-gate check (the human sees the warning before the
violation lands).

## When the principles don't fit

Three patterns where the principles *legitimately* need a local
override:

- **Bridges / adapter code** — every concrete stack has
  adapters that absorb the shape of the world (HTMX attribute
  strings, WebView2 dialog semantics, OS path quirks). DRY is
  enforced by these adapters; DRY is *not* enforced inside the
  adapters (the adapter is the one place where the duplicated
  shape gets collapsed).
- **Tier 1 vs Tier 2 surface** — the per-component byte-stability
  rule in adoptions that pin primitive rendered output. This is
  *imposed duplication* (per DRY §1.1) on purpose: snapshot tests
  pin the duplication so a future refactor can verify the
  primitive swap is safe.
- **Temporary divergence** — a slice that needs to ship faster
  than the principled refactor would allow. The cleanup plan
  documents the divergence; the follow-up issue does the refactor.
  This is **not** an excuse for permanent divergence — every
  temporary violation has a deadline (the cleanup plan), and the
  follow-up issue tracks the deadline.

---

## §1 — The principles

Each entry: 1-sentence definition (from the book), the *why*
(what it saves you from), the repo's operational form (which
agent-stack doc enforces the principle), and a "When you might
violate" section listing the *known* cases where the repo
legitimately breaks the principle. New violation cases found in
the wild are added to the "when you might violate" list — they
are warnings, not errors.

### §1.1 — DRY (Don't Repeat Yourself) — Tip #15

> "Every piece of knowledge must have a single, unambiguous,
> authoritative representation within a system."

**The why:** every duplicated representation is a place where a
future change has to be made in N places. Miss one and the system
silently diverges. The cost of a single-source change is O(1);
the cost of an N-place change is O(N) and grows with the system.

**Repo operational form:**
- The adopting repo's glossary (`CONTEXT.md` or
  `docs/GLOSSARY.md`) — single source for every domain term.
- The stack's URL registry (typed builder; e.g.
  `internal/routebuilder` in Go + HTMX).
- The stack's DOM surface-ID registry (e.g. `internal/uiids`).
- The adopting repo's component / primitive design system (when
  one exists).
- [`glossary-discipline.md`](glossary-discipline.md) — the
  maintenance pattern.

**When you might violate (known cases — fill in as adopting
repo observes them):**
- _Tier 1 vs Tier 2 surface_ — a new component primitive has to
  coexist with the literal class strings it will replace for one
  slice. The follow-up issue documents the swap.
- _Bridge code_ — see "When the principles don't fit" above.

### §1.2 — Orthogonality — Tip #17

> "Two or more things are orthogonal if changes in one do not
> affect any of the others." Also called *cohesion*.

**The why:** a change to module A should not silently require a
change to module B. Non-orthogonal systems make every change
expensive, and the cost grows with the system.

**Repo operational form:**
- The adopting repo's architecture / forbidden-import test.
- [`complexity.md`](complexity.md) — the deep-module rule. DTOs
  at the seam, not persistence structs.

**When you might violate:**
- _Bridge code_ — couples layers on purpose.
- _Cross-cutting concerns_ — logging, tracing, theming are
  *designed* to be cross-cutting. They violate strict
  orthogonality; they earn it by being the smallest possible
  cross-cutting surface.

### §1.3 — Reversibility — Tip #18

> "No decision is cast in stone. Instead, consider each as being
> written in the sand at the beach, and plan for change."

**The why:** every decision has a chance of being wrong.
Decisions that are easy to reverse are cheap; decisions that
are hard to reverse are expensive. The expensive ones are the
ones that need the most scrutiny.

**Repo operational form:**
- The adopting repo's branching model (see
  [`commit-and-branch.md`](commit-and-branch.md) §"Branch
  policy" — single-branch default, three-branch for advanced
  cases).
- The adopting repo's URL + DOM-ID registries — every URL and
  DOM ID is a string in a registry, not a literal in source. A
  rename is a one-file change.
- For repos with a database: the migration reversibility
  catalogue (Reversible / Partially / Non-Reversible).

**When you might violate:**
- _Host runtime commitment_ — e.g. Wails v2.12.0, Electron, Tauri.
  A future major-version migration is the hardest reversibility
  problem in many repos. The mitigation is *named, local*
  workarounds that a future migration can find and remove.

### §1.4 — Tracer Bullets — Tip #20

> "Tracer bullets let you home in on your target by trying things
> and seeing how close they land." Small end-to-end vertical
> slices, NOT horizontal layers. Tracer code IS the skeleton of
> the final system — it is NOT a prototype.

**The why:** a tracer bullet proves the path is *wired*
end-to-end without building every layer in isolation. The first
bullet doesn't have to hit the target; the *feedback* is the
point.

**Repo operational form:**
- [`feature-protocol.md`](feature-protocol.md) §"Tracer bullets"
  — the rule.
- The `tracer-bullets` skill — auto-loaded by the agent harness.
- [`rpci.md`](rpci.md) §I — "the first slice is the only slice
  that runs in the same session." Slice 1 is always a tracer
  bullet.

**When you might violate:**
- _Documentation-only changes_ — no tracer needed for a doc
  commit. The review is the test.

### §1.5 — Design by Contract — Tip #37

> "A correct program is one that does no more and no less than
> it claims to do." Use **preconditions, postconditions,
> invariants**.

**The why:** contracts make the *boundary* between caller and
callee explicit. A caller that violates a precondition knows
immediately; a callee that violates a postcondition knows
immediately. The contract is the *test surface* — the unit test
is the runtime check.

**Repo operational form:**
- The doc-comment floor ([`laws.md`](laws.md) §"Doc comments on
  exported identifiers") — preconditions are documented for
  every exported identifier.
- The adopting repo's architecture test — package-level
  invariants.
- [`code-changes.md`](code-changes.md) — the cross-layer working
  contract.
- The adopting repo's smoke probes — behavioral postconditions
  for the HTTP surface.

### §1.6 — Dead Programs Tell No Lies (Crash Early) — Tip #38

> "A dead program normally does a lot less damage than a
> crippled one."

**The why:** a "crippled" program keeps running with corrupt
state. The damage compounds. A dead program stops, the user
notices, and the bug is found in 5 minutes instead of 5 hours.

**Repo operational form:**
- [`laws.md`](laws.md) §"No unguarded re-entrant UI calls" —
  refusing to start a second native dialog is *crashing early*
  (the UI thread is preserved).
- The stack's typed-attribute swap allowlist (e.g.
  `htmxattr.Mux`) — panics at render time on an invalid swap
  value. The panic is the *signal*.

**When you might violate:**
- _User-recoverable errors_ — a missing optional field is a
  *toast* (graceful degradation), not a crash.
- _Background jobs_ — a job worker that crashes leaves the job
  in an interrupted state. The user can re-run from the source
  page. The interrupted status is the *graceful* version of
  "crash early."

### §1.7 — Decoupling / Law of Demeter — Tip #44

> An object's method should call only methods belonging to
> itself, its parameters, objects it creates, or its directly
> held component objects. "Write shy code."

**The why:** chains like `a.b().c().d()` create hidden coupling.
A change to `b` propagates silently. The Law of Demeter says:
"if you want to talk to `d`, ask `a` to talk to `d` for you."

**Repo operational form:**
- [`complexity.md`](complexity.md) — the deep-module rule covers
  *package*-level decoupling.
- Most lints catch adjacent smells (`rangeValCopy` / `hugeParam`
  in Go) but not Demeter chains. Open audit gap by design.

**When you might violate:**
- _Error chains_ — `if err := a.B(); err != nil { return
  fmt.Errorf("b: %w", c(err)) }` is *not* a Demeter violation;
  the chain is *one* call.
- _Builder / fluent APIs_ — typed attribute builders use
  self-checking chains. The package owns the constraint, so
  the chain is *intentional*.

### §1.8 — Metaprogramming (abstractions in code, details in metadata) — Tip #79

> "Program for the general case, and put the specifics somewhere
> else — outside the compiled code base."

**The why:** code is expensive to change (rebuild, redeploy);
metadata is cheap (reload). The rule puts the *stable* part in
code and the *changeable* part in metadata.

**Repo operational form:**
- The adopting repo's URL + DOM-ID registries are metadata.
- Lint rule definitions are *data* that the linter consumes.
- Theme tokens are metadata; the templ / view components
  consume them.

**When you might violate:**
- _Performance-critical paths_ — when the metadata lookup is a
  hot path, a precomputed constant in code wins.
- _Type-checked metadata_ — when the metadata has invariants a
  string registry can't express, a typed enum / const wins.

### §1.9 — Temporal Coupling / Concurrency — Tip #57

> "Reduce any time-based dependencies." Design for concurrency
> so the system can be deployed flexibly and tested for thread
> safety.

**The why:** a system with hidden time dependencies is hard to
test (you can't pause it), hard to reason about, and prone to
race conditions. Explicit concurrency makes the time dimension
*part of the API*.

**Repo operational form:**
- Per-process actor state (the Wails `App` struct, the Electron
  main process, Tauri main, etc.) — equivalent to an actor.
- The hungry-consumer model in background-job workers.
- The in-flight dedup pattern (LoadOrStore + defer Delete) is
  a per-slot mutex.

### §1.10 — It's Just a View (MVC) — Tip #42

> Separate the model from views of the model.

**The why:** a view that knows about the model is bound to one
view of that model. A model that doesn't know about any view
can be rendered any way. MVC decouples the two.

**Repo operational form:**
- The adopting repo's model layer (no UI imports).
- The view layer (templ / templates + frontend JS).
- The controller layer (HTTP handlers + framework bindings).
- A grey-box viewmodel layer between the model and the view.

### §1.11 — Program Deliberately — Tip #62

> "Rely only on reliable things. Beware of accidental complexity,
> and don't confuse a happy coincidence with a purposeful plan."

**The how-to-program-deliberately checklist (8 rules):**
1. Always be aware of what you are doing
2. Don't code blindfolded
3. Proceed from a plan
4. Rely only on reliable things
5. Document your assumptions
6. Test assumptions as well as code
7. Prioritize your effort
8. Don't be a slave to history

**The why:** every "it worked but I don't know why" moment is a
landmine. Program by coincidence is the *fastest* way to ship
a bug.

**Repo operational form:**
- Rules 1-4: [`rpci.md`](rpci.md) + [`tdd.md`](tdd.md) cover
  all four.
- Rule 5: doc-comment floor + "What assumptions does this PR
  make?" line in the slice plan (open audit gap).
- Rule 6: property-based tests, drift detectors.
- Rule 7: fresh-context-per-slice rule ([`rpci.md`](rpci.md)
  §I).
- Rule 8: refactor Early / refactor Often.

### §1.12 — Algorithm Speed (Big O) — Tip #63

> "Get a feel for how long things are likely to take before you
> write code."

**The why:** an O(n²) algorithm on a 10k-row table is a real
problem; the same algorithm on a 100-row table is not. The Big
O annotation tells the next reader *where* to look if the perf
budget breaks.

**Repo operational form:**
- The per-iter footprint doc-comment pattern (e.g.
  [`tdd.md`](tdd.md) — count of DB queries per operation +
  budget). The pattern documents the actual footprint.

### §1.13 — Refactoring — Tip #65

> "Just as you might weed and rearrange a garden, rewrite,
> rework, and re-architect code when it needs it. Fix the root
> of the problem."

**The when-to-refactor checklist (5 triggers):**
1. DRY violation
2. Non-orthogonal
3. Knowledge improved
4. Requirements evolve
5. Performance

**The how-to-refactor checklist (3 rules):**
1. Don't try to refactor and add functionality at the same time
2. Make sure you have good tests before you begin refactoring
3. Take short, deliberate steps

**Repo operational form:**
- The Tier 2 / Tier 3 commit rule ([`feature-protocol.md`](feature-protocol.md))
  — the "don't refactor and add functionality at the same
  time" rule is operationalized as the slice discipline.
- [`tdd.md`](tdd.md) — "have good tests before refactoring."

**When you might violate:**
- _Drive-by cleanup_ — a "while I'm here" cleanup in a feature
  commit violates rule 1. The Tier 2 / Tier 3 rule catches
  this; the drive-by belongs in a separate commit.
- _Refactor without tests_ — the red-green-refactor loop
  requires tests *first*. A refactor commit without coverage
  is a Tier 3 maintenance commit, not a Tier 2 vertical.

### §1.14 — Code That's Easy to Test — Tip #67

> "Build testability into the software from the very beginning."

**The 7 Aspects of Testing (Ch 8):**
1. Unit testing
2. Integration testing
3. Validation and verification
4. Resource exhaustion, errors, and recovery
5. Performance testing
6. Usability testing
7. Testing the tests themselves

**Repo operational form:**
- (1) Unit: every internal package has a `*_test.go` (or
  analog).
- (2) Integration: an HTTP-handler test harness + per-handler
  integration tests.
- (3) Validation: smoke probes driving the live binary.
- (4) Resource: goroutine leak tests (`zzz_goleak_test.go` or
  analog).
- (5) Performance: the per-iter footprint doc-comment pattern
  + a stress-test workflow.
- (6) Usability: the manual audit playbook (see
  `docs/agents/manual-audit-playbook.md`).
- (7) Test-the-tests: mutation testing is an open gap.

### §1.15 — Ubiquitous Automation — Tip #85

> "A shell script or batch file will execute the same
> instructions, in the same order, time after time."

**The why:** every manual procedure is a place where a future
operator will get it slightly different. Automation is the
*only* way to guarantee repeatability.

**Repo operational form:**
- The adopting repo's `scripts/` + `Makefile` / `package.json`
  targets + CI workflows.
- The agent-stack CLI surface: any documented CLI / make
  target should be enforced by a coverage check
  (DixieData's `cli-coverage.mjs` is the reference).

**When you might violate:**
- _One-time setup_ — a single `git mv` is fine by hand; a
  scripted equivalent adds complexity for no win.
- _Operator judgment_ — a "promote to stable" decision is
  *not* fully automatable (the human reviews the diff). The
  automation is the *enforcement* (`make promote-dry-run` as a
  CI gate), not the *decision*.

### §1.16 — It's All Writing (English as code) — Tip #13

> "Write documents as you would write code: honor the DRY
> principle, use metadata, MVC, automatic generation."

**The why:** docs that diverge from the code rot. Docs that
live in the same repo (versioned, reviewed, CI-checked) don't
rot as fast.

**Repo operational form:**
- `CONTEXT.md` is the project glossary (DRY for vocabulary).
- `docs/agents/INDEX.md` is the progressive-disclosure table
  (3-tier doc structure).
- The doc-comment floor ([`laws.md`](laws.md)) is the
  cross-layer contract: code and doc are versioned together.

---

## §2 — The 4 book-end checklists

The book has 4 checklists that the principle spine references
but which don't fit under any one principle. Each is a *test*
an agent should run before shipping.

### §2.1 — WISDOM Acrostic (Ch 1, Communicate)

When writing for the user (CHANGELOG, issue body, commit
message, ADR, README), use the WISDOM acrostic:

- **W**hat do you want them to learn?
- What **i**s their interest in what you've got to say?
- How **s**ophisticated are they?
- How much **d**etail do they want?
- Whom do you want to **o**wn the information?
- How can you **m**otivate them to listen to you?

**The why:** a CHANGELOG bullet aimed at the wrong audience
either bores an expert or loses a new contributor. The WISDOM
acrostic forces the writer to choose the audience before
choosing the words.

**When you might violate:** internal-only docs where the
audience is the agent (`.scratch/`, debug logs).

### §2.2 — Architectural Questions (Ch 7)

When designing a new module / service / feature, ask:

1. Are responsibilities well defined?
2. Are the collaborations well defined?
3. Is coupling minimized?
4. Can you identify potential duplication?
5. Are interface definitions and constraints acceptable?
6. Can modules access needed data — when needed?

**The why:** the 6 questions are the *test surface* for the
deep-module rule. A "no" on any one of them is a flag that the
design will fight back later.

**Repo operational form:** questions 1-4 are operationalized
by [`complexity.md`](complexity.md) §"Deep-module discipline".
Questions 5-6 depend on per-stack conventions in the relevant
addendum.

### §2.3 — Debugging Checklist (Ch 3)

When stuck on a bug, ask:

1. Is the problem being reported a direct result of the
   underlying bug, or merely a symptom?
2. Is the bug really in the compiler? Is it in the OS? Or is it
   in your code?
3. If you explained this problem in detail to a coworker, what
   would you say?
4. If the suspect code passes its unit tests, are the tests
   complete enough? What happens if you run the unit test with
   this data?
5. Do the conditions that caused this bug exist anywhere else
   in the system?

**The why:** the 5 questions are the *test surface* for the
"fix root cause, not symptom" pattern. A "no" on question 5 is
a flag for the "find bugs once" rule — the bug will recur.

**Repo operational form:** spirit is enforced by the
orphan-handler probe + the per-bug regression-test discipline
(per [`tdd.md`](tdd.md)). The 5-question checklist is not yet
in any tier-1 doc; this doc is the first place it lives.

### §2.4 — Cutting the Gordian Knot (Ch 7)

When solving an impossible problem, ask:

1. Is there an easier way?
2. Am I solving the right problem?
3. Why is this a problem?
4. What makes it hard?
5. Do I have to do it this way?
6. Does it have to be done at all?

**The why:** the 6 questions are the *test surface* for the
"find the box" rule. A "yes" on question 6 ("don't have to do
it at all") is the most valuable answer in software.

**When you might violate:** a user-stated requirement that *is*
required (a tax form, a regulatory export). The 6 questions
help the agent find a *cheaper* way; they don't help with a
*non-negotiable* way.

---

## §3 — Cross-reference: principle ↔ agent-stack doc

Some principles are *also* enforced as Laws (in
[`laws.md`](laws.md)). This is intentional: the principles are
the *why*; the Laws are the *earned-by-real-bug operational
form* of the principles. A principle may have multiple Laws
under it; a Law may pin a single operational form of a
principle.

| Principle | Agent-stack Doc(s) |
|---|---|
| DRY | [`glossary-discipline.md`](glossary-discipline.md) (vocabulary DRY); [`complexity.md`](complexity.md) §"Two-adapter rule" (interface DRY) |
| Orthogonality | [`complexity.md`](complexity.md) — the deep-module rule |
| Reversibility | [`commit-and-branch.md`](commit-and-branch.md) §"Branch policy" |
| Tracer Bullets | [`feature-protocol.md`](feature-protocol.md) — slice discipline |
| Design by Contract | [`laws.md`](laws.md) — doc-comment floor; [`code-changes.md`](code-changes.md) — cross-layer contract |
| Dead Programs | [`laws.md`](laws.md) §"No unguarded re-entrant UI calls"; per-addendum dialog-guard laws |
| Law of Demeter | [`complexity.md`](complexity.md) — deep-module rule at package level |
| Metaprogramming | Per-addendum: typed URL builder + DOM-ID registry |
| Temporal Coupling | [`laws.md`](laws.md) — re-entry protection (per-slot mutex) |
| MVC | [`complexity.md`](complexity.md) — viewmodel at the seam |
| Program Deliberately | [`rpci.md`](rpci.md) — RPCI flow; [`laws.md`](laws.md) — universal laws |
| Algorithm Speed | [`tdd.md`](tdd.md) — per-iter footprint doc-comment pattern |
| Refactoring | [`feature-protocol.md`](feature-protocol.md) — Tier 2 / Tier 3 commit rule |
| Code That's Easy to Test | [`tdd.md`](tdd.md) — RED/GREEN/REFACTOR |
| Ubiquitous Automation | Per-repo CI + scripts |
| It's All Writing | [`laws.md`](laws.md) — doc-comment floor; `docs/agents/INDEX.md` (this repo's tier table) |

The principle is the *why*; the doc is the *what*. Both are
useful. New contributors should read the principles (this
doc); the *reviewer* reads the Laws. The principle explains
why the Law exists; the Law tells you what to do without
re-deriving the why.

---

## §4 — How to extend this doc

When a new principle-violation pattern shows up in a PR review:

1. **File the violation in the slice commit's "Principle
   warnings" block** (per §"The warn + cite protocol" above).
2. **If the violation is the kind that will recur**, add a
   "When you might violate" bullet to the relevant principle
   section. The doc grows with the codebase.
3. **If the violation is the kind that should NOT recur**,
   file a follow-up issue for the cleanup, and add a "Known
   gap" bullet to the principle section. The doc + the issue
   track the violation together.

When a new principle is needed (e.g. a 17th principle emerges
from a new book or a new pattern in the codebase), add a new
§1.N section following the same template. The doc is
*additive*; a new section is one PR.

---

## §5 — References

- _The Pragmatic Programmer, 20th Anniversary Edition_, Hunt &
  Thomas. The 100 tips are excerpted at
  <https://pragprog.com/tips/>.
- The principle spine + 11 book-end checklists are summarized
  at
  <https://github.com/HugoMatilla/The-Pragmatic-Programmer#checklist>.
- The upstream doc this was ported from: DixieData's
  `docs/agents/pragmatic-principles.md` (commit `cca2183` for
  the original spine, commit `177c2dd` for the tip-index
  appendix).
- The cross-referenced agent-stack docs:
  - [`laws.md`](laws.md) — the earned-by-real-bug operational form
  - [`feature-protocol.md`](feature-protocol.md) — slice discipline + Tier 1-3 commit rule
  - [`rpci.md`](rpci.md) — RPCI flow
  - [`complexity.md`](complexity.md) — deep-module discipline
  - [`tdd.md`](tdd.md) — RED/GREEN/REFACTOR
  - [`code-changes.md`](code-changes.md) — cross-layer working contract
  - [`glossary-discipline.md`](glossary-discipline.md) — vocabulary DRY
  - [`bug-patterns.md`](bug-patterns.md) — per-layer bug catalog
  - [`commit-and-branch.md`](commit-and-branch.md) — branch policy
  - [`session-protocol.md`](session-protocol.md) — agent procedural rules

---

## §6 — Tip index (the 100 tips, by number)

This index is the **operational counterpart** to the principle
spine in §1. Each tip is a concrete behavior; the principle
is the *why* behind the behavior. The principle spine is what
an agent reads when designing a new feature; this index is what
an agent reads when checking whether a specific commit or
behavior is in compliance.

**State legend:**
- ✅ **Enforced** — a `core/laws.md` Law, a `core/*.md` rule, an
  `addenda/*` rule, an `issues/*.md` template, a `scripts/*`
  automation, or a `templates/*.md.tmpl` pins the tip.
- ⚠️ **Partial** — the spirit is satisfied but no written
  rule, OR the rule exists but no regression net enforces it.
  Cited.
- ❌ **Gap** — the tip is not addressed and would be
  high-leverage to add. Candidate follow-up.
- ➖ **N/A** — applies to contexts agent-stack does not
  inhabit (multi-team management, hiring, hosting incidents,
  scheduling iteration, etc.).

**Principle column** maps the tip to the §1.x section in this
doc that explains the *why*. Tips with a "philosophy /
technique" note are *attitudes* (Ch 1 of the book) or
*techniques* (Ch 3+), not principles per se — they inform
behavior but are not operationalized as a deep-module rule.

**One-line evidence** is truncated to ~110 chars. The full
evidence per tip lives in the source audit at
`docs/audit/pragmatic-programmer-audit-2026-07.md` (the
100-tip map retained as a primary audit artifact).

| # | Tip | State | Principle | One-line evidence |
|---|---|---|---|---|
| 1 | Care About Your Craft | ✅ | — (philosophy / technique, not a principle) | `core/session-protocol.md` §"Bias toward action" + §"Proportional depth" + the entire doc-comment floor + p... |
| 2 | Think! About Your Work | ✅ | — (philosophy / technique, not a principle) | `core/rpci.md` RPCI flow explicitly turns off the autopilot: every Plan has a Critique phase the user signs... |
| 3 | You Have Agency | ✅ | — (philosophy / technique, not a principle) | `core/rpci.md` §C — Critique gate is the operational form. The user has explicit "approve, start" authority. |
| 4 | Provide Options, Don't Make Lame Excuses | ✅ | — (philosophy / technique, not a principle) | `core/rpci.md` Plan surfaces "decisions to confirm" with options; the agent never says "can't be done." |
| 5 | Don't Live with Broken Windows | ✅ | — (philosophy / technique, not a principle) | `core/laws.md` — every Law was earned by a real bug. The universal-laws pattern (re-entry, doc-comment floo... |
| 6 | Be a Catalyst for Change | ⚠️ | — (philosophy / technique, not a principle) | agent-stack is *literally* a catalyst (bootstrap script + `scripts/init.sh` + `addenda/` invite contributio... |
| 7 | Remember the Big Picture | ✅ | — (philosophy / technique, not a principle) | `docs/agents/INDEX.md` 3-tier progressive-disclosure table is the operational form. Agents know which doc t... |
| 8 | Make Quality a Requirements Issue | ⚠️ | — (philosophy / technique, not a principle) | `issues/feature-template.md` has "Acceptance criteria" but no "Quality bar" field. The test-floor + smoke-p... |
| 9 | Invest Regularly in Your Knowledge Portfolio | ❌ | — (philosophy / technique, not a principle) | No `docs/learning/` or per-stack reading list. This audit doc is a one-shot, not a habit. **Candidate follo... |
| 10 | Critically Analyze What You Read and Hear | ⚠️ | §1.19 WISDOM | `core/pragmatic-principles.md` §"Yesterday's best practice" frames it, but the per-PR discipline (e.g. "cha... |
| 11 | English is Just Another Programming Language | ✅ | §1.16 It's All Writing | `core/glossary-discipline.md` + the 3-tier docs taxonomy. Every doc is reviewed for terminology drift; `cor... |
| 12 | It's Both What You Say and the Way You Say It | ✅ | §1.19 WISDOM | `core/commit-and-branch.md` §"Commit message shape" mandates 1-3 bullets explaining the *why* + regression ... |
| 13 | Build Documentation In, Don't Bolt It On | ✅ | §1.16 It's All Writing | `core/laws.md` §"Doc comments on exported identifiers" + the 3-tier docs taxonomy + `templates/AGENTS.md.tm... |
| 14 | Good Design Is Easier to Change Than Bad Design | ✅ | §1.3 Reversibility | `core/complexity.md` deep-module discipline + per-addendum guard tests are the rule. "Code that's easy to d... |
| 15 | DRY—Don't Repeat Yourself | ✅ | §1.1 DRY | `core/glossary-discipline.md` (vocabulary DRY) + `core/complexity.md` §"Two-adapter rule" (interface DRY) +... |
| 16 | Make It Easy to Reuse | ✅ | §1.1 DRY | `addenda/go-htmx.md` §"Bridge code" explains *where* DRY applies vs *where* it doesn't. The per-addendum gu... |
| 17 | Eliminate Effects Between Unrelated Things | ✅ | §1.2 Orthogonality | `core/complexity.md` deep-module discipline + the per-stack forbidden-import test pattern (e.g. `addenda/go... |
| 18 | There Are No Final Decisions | ✅ | §1.3 Reversibility | `core/commit-and-branch.md` §"Branch policy" supports both single-branch and three-branch models. Releases ... |
| 19 | Forgo Following Fads | ⚠️ | §1.3 Reversibility | Implicit in the stack choices (templ, chi, Wails) but no written policy. A future "rewrite in React" PR wou... |
| 20 | Use Tracer Bullets to Find the Target | ✅ | §1.4 Tracer Bullets | The `tracer-bullets` skill (auto-loaded) + `core/feature-protocol.md` §"Tracer bullets" + the Tier 1/2/3 co... |
| 21 | Prototype to Learn | ⚠️ | — (philosophy / technique, not a principle) | `.scratch/` is the prototype convention (mentioned by `core/session-protocol.md` indirectly via the DEBUG/b... |
| 22 | Program Close to the Problem Domain | ✅ | — (philosophy / technique, not a principle) | `core/complexity.md` §"Deep-module discipline" mandates domain-shaped public surfaces. `core/feature-protoc... |
| 23 | Estimate to Avoid Surprises | ⚠️ | — (philosophy / technique, not a principle) | `core/rpci.md` Plan includes files touched + success criteria + regression net, but no time estimate. `core... |
| 24 | Iterate the Schedule with the Code | ➖ | — (philosophy / technique, not a principle) | N/A. Framework ships docs + scripts; no schedule to iterate. |
| 25 | Keep Knowledge in Plain Text | ✅ | — (philosophy / technique, not a principle) | Every config in agent-stack is plain text (Markdown, shell, JSON in `templates/`). No binary configs. |
| 26 | Use the Power of Command Shells | ✅ | — (philosophy / technique, not a principle) | `scripts/*.sh` (`backfill-labels.sh`, `check-core-stack-agnostic.sh`, `dedupe-skills.sh`, `init.sh`, `sync-... |
| 27 | Achieve Editor Fluency | ➖ | — (philosophy / technique, not a principle) | N/A. Agent-context; not a framework concern. |
| 28 | Always Use Version Control | ✅ | — (philosophy / technique, not a principle) | The entire branching model in `core/commit-and-branch.md`. Every change goes through git; the framework's o... |
| 29 | Fix the Problem, Not the Blame | ⚠️ | — (philosophy / technique, not a principle) | `core/commit-and-branch.md` §"Commit message shape" prescribes "what + why" but no "don't blame" rule. Impl... |
| 30 | Don't Panic | ➖ | — (philosophy / technique, not a principle) | N/A. No incident-response flow at framework level. |
| 31 | Failing Test Before Fixing Code | ✅ | — (philosophy / technique, not a principle) | `core/tdd.md` red-green-refactor protocol is the operational form. Step 1 ("RED") explicitly: write the fai... |
| 32 | Read the Damn Error Message | ✅ | §1.6 Dead Programs | `core/tdd.md` §"The failure modes TDD prevents" — failure class #1 (Invoker wiring) mandates asserting the ... |
| 33 | "select" Isn't Broken | ⚠️ | §1.6 Dead Programs | Implicit (no recent commit blamed Wails / chi / templ without evidence) but no stated rule. |
| 34 | Don't Assume It—Prove It | ✅ | §1.6 Dead Programs | `core/tdd.md` §"What's the seam?" + the per-layer recipes (handler test, smoke probe, migration test) manda... |
| 35 | Learn a Text Manipulation Language | ➖ | — (philosophy / technique, not a principle) | N/A at the framework level. Per-adopter concern. |
| 36 | You Can't Write Perfect Software | ✅ | §1.5 Design by Contract | `core/laws.md` §"No unguarded re-entrant UI calls" + §"Tier-0 docs have a size ceiling" are earned-by-real-... |
| 37 | Design with Contracts | ✅ | §1.5 Design by Contract | `core/laws.md` §"Doc comments on exported identifiers" is the contract floor. `core/code-changes.md` is the... |
| 38 | Crash Early | ✅ | §1.5 Design by Contract | `core/laws.md` §"No unguarded re-entrant UI calls" — crashing early preserves the UI thread. Per-addendum: ... |
| 39 | Use Assertions to Prevent the Impossible | ✅ | §1.5 Design by Contract | `core/laws.md` §"Doc comments on exported identifiers" enforces the assertion-via-documentation pattern. Pe... |
| 40 | Finish What You Start | ⚠️ | — (philosophy / technique, not a principle) | The pattern lives in adopting repos via `defer` (Go) / `try/finally` (Python) / effect-cleanup (React). `co... |
| 41 | Act Locally | ⚠️ | — (philosophy / technique, not a principle) | `core/complexity.md` §"Two-adapter rule" prescribes local interfaces, but no named rule for "locality of st... |
| 42 | Take Small Steps—Always | ✅ | §1.10 MVC | `core/rpci.md` §I — Implement: "the first slice is the only slice that runs in the same session." Fresh-con... |
| 43 | Avoid Fortune-Telling | ✅ | — (philosophy / technique, not a principle) | `core/session-protocol.md` §"YAGNI" + `core/complexity.md` §"Strategic programming vs YAGNI" + `core/featur... |
| 44 | Decoupled Code Is Easier to Change | ✅ | §1.7 Law of Demeter | `core/complexity.md` deep-module discipline is the operational form. The DTO-at-the-seam rule pins the per-... |
| 45 | Tell, Don't Ask | ⚠️ | §1.7 Law of Demeter | `core/feature-protocol.md` §"Module discipline — service is the seam" prescribes telling the service to do ... |
| 46 | Don't Chain Method Calls | ➖ | §1.7 Law of Demeter | N/A as a stated rule; `core/complexity.md` deep-module discipline covers the same concern implicitly. |
| 47 | Avoid Global Data | ⚠️ | §1.2 Orthogonality | Per-adopter concern. `core/complexity.md` prescribes a model-without-UI-imports boundary; the "no package-l... |
| 48 | If It's Important Enough To Be Global, Wrap It in an API | ✅ | §1.2 Orthogonality | `addenda/go-htmx.md` §"Stack laws" gives the worked example: `(*App).guardedSaveFileDialog` wraps the dange... |
| 49 | Programming Is About Code, But Programs Are About Data | ✅ | §1.2 Orthogonality | `core/complexity.md` §"Deep-module discipline" prescribes DTOs as the cross-boundary value type. The audit-... |
| 50 | Don't Hoard State; Pass It Around | ⚠️ | §1.2 Orthogonality | `core/code-changes.md` prescribes arguments over global state implicitly, but no named rule. Implicit in th... |
| 51 | Don't Pay Inheritance Tax | ➖ | §1.2 Orthogonality | N/A as a framework rule; the type-system-agnostic stance means each adopter inherits whatever their languag... |
| 52 | Programming Is About Code (continued) | ➖ | — (philosophy / technique, not a principle) | Duplicate of tip #49. (Carried forward for completeness.) |
| 53 | Shared State Is Incorrect State | ⚠️ | §1.9 Temporal Coupling | `core/laws.md` §"No unguarded re-entrant UI calls" gives the per-slot-mutex pattern. No general "shared sta... |
| 54 | Random Failures Are Often Concurrency Issues | ⚠️ | §1.9 Temporal Coupling | `core/bug-patterns.md` §"Concurrency / dependency correctness" lists the AI-amplification evidence but no p... |
| 55 | Use Actors For Concurrency Without Shared State | ⚠️ | §1.9 Temporal Coupling | Per-adopter concern. The framework pattern (per-process struct) is implied via `core/commit-and-branch.md` ... |
| 56 | Analyze Workflow to Improve Concurrency | ⚠️ | §1.9 Temporal Coupling | `core/rpci.md` §"Bias toward action" + the slice parallelism implicit in RPCI, but no concurrency-analysis ... |
| 57 | Use Blackboards to Coordinate Workflow | ➖ | — (philosophy / technique, not a principle) | N/A. Framework does not coordinate between concurrent agents. |
| 58 | Programming Is About Code (continued) | ➖ | — (philosophy / technique, not a principle) | Duplicate of tip #49. |
| 59 | Listen to Your Inner Lizard | ⚠️ | — (philosophy / technique, not a principle) | `core/rpci.md` §I — Implement mandates fresh-context-per-slice. The "if you feel stuck, the slice is wrong"... |
| 60 | Don't Program by Coincidence | ✅ | §1.11 Program Deliberately | `core/rpci.md` §P — Plan mandates "Decisions to confirm" surfaced explicitly. The "RELY only on reliable th... |
| 61 | Estimate the Order of Your Algorithms | ⚠️ | §1.12 Algorithm Speed | `core/tdd.md` §"Algorithm speed" lists this as the standalone concern but no general annotation rule ships ... |
| 62 | Test Your Estimates | ⚠️ | §1.12 Algorithm Speed | Per-adopter concern. The framework supports the pattern via `core/tdd.md` "per-iter footprint doc-comment" ... |
| 63 | Refactor Early, Refactor Often | ✅ | §1.13 Refactoring | `core/complexity.md` §"Strategic programming framework" + `core/feature-protocol.md` §"The 3-tier commit ru... |
| 64 | Testing Is Not About Finding Bugs | ⚠️ | — (philosophy / technique, not a principle) | `core/bug-patterns.md` §"Meta-patterns" lists regression nets as the catch, but the "tests as a design tool... |
| 65 | A Test Is the First User of Your Code | ✅ | §1.13 Refactoring | `core/tdd.md` Step 1 — "RED: write the failing test first." Per-layer recipes pin the test-first pattern. |
| 66 | Build End-To-End, Not Top-Down or Bottom Up | ✅ | §1.4 Tracer Bullets | `core/feature-protocol.md` §"Tracer bullets" + `core/rpci.md` §I — Implement mandate a vertical-tracer bull... |
| 67 | Design to Test | ✅ | §1.14 Code That's Easy to Test | `core/tdd.md` §"What's the seam?" + §"Per-layer recipes" prescribe the seam-before-the-implementation patte... |
| 68 | Test Your Software, or Your Users Will | ✅ | §1.14 Code That's Easy to Test | `core/tdd.md` §"Adjacent behavior sweep" mandates testing adjacent surfaces, not just the slice. The smoke-... |
| 69 | Use Property-Based Tests to Validate Your Assumptions | ⚠️ | §1.14 Code That's Easy to Test | `core/bug-patterns.md` references property-based tests in the meta-pattern section, but no general pattern ... |
| 70 | Keep It Simple and Minimize Attack Surfaces | ✅ | §1.14 Code That's Easy to Test | `core/complexity.md` §"Strategic programming framework" + `core/session-protocol.md` §"YAGNI" are the opera... |
| 71 | Apply Security Patches Quickly | ❌ | — (philosophy / technique, not a principle) | No framework-level security-scan automation. `scripts/check-core-stack-agnostic.sh` checks doc-level struct... |
| 72 | Name Well; Rename When Needed | ⚠️ | §1.14 Code That's Easy to Test | `core/glossary-discipline.md` prescribes the rename process for vocabulary terms, but no general "name well... |
| 73 | Sign Your Work | ✅ | — (philosophy / technique, not a principle) | `core/commit-and-branch.md` §"Commit message shape" + §"Push verification" mandate the commit-attribution +... |
| 74 | No One Knows Exactly What They Want | ✅ | — (philosophy / technique, not a principle) | `core/rpci.md` §C — Critique + `core/session-protocol.md` §"Capturing decisions" + the "the user is the cha... |
| 75 | Programmers Help People Understand What They Want | ✅ | — (philosophy / technique, not a principle) | `core/rpci.md` Plan template + the apply-sites checklist in `issues/feature-template.md` make the full shap... |
| 76 | Requirements Are Learned in a Feedback Loop | ✅ | — (philosophy / technique, not a principle) | `core/rpci.md` §I — "the first slice is the only slice that runs in the same session" — the next session pi... |
| 77 | Work with a User to Think Like a User | ⚠️ | — (philosophy / technique, not a principle) | Per-adopter concern. `core/feature-protocol.md` "Apply sites" requirement proxies for the user-perspective ... |
| 78 | Policy Is Metadata | ✅ | §1.8 Metaprogramming | `core/laws.md` §"Tier-0 docs have a size ceiling" pins the budget as data. `core/bug-patterns.md` meta-patt... |
| 79 | Use a Project Glossary | ✅ | §1.8 Metaprogramming | `core/glossary-discipline.md` is the operational form. The "flagged ambiguities" pattern (preserved from ad... |
| 80 | Use a Project Glossary (continued) | ➖ | §1.8 Metaprogramming | Carried forward for completeness. (The 80-tip mapping to #79 is the book's own deduplication.) |
| 81 | Don't Think Outside the Box—Find the Box | ✅ | — (philosophy / technique, not a principle) | `core/complexity.md` §"Strategic programming framework" + `core/rpci.md` §"Cutting the Gordian Knot" (4-que... |
| 82 | Don't Go into the Code Alone | ⚠️ | — (philosophy / technique, not a principle) | `core/session-protocol.md` §"Capturing decisions" prescribes user-collaboration but no named rule for "don'... |
| 83 | Agile Is Not a Noun; Agile Is How You Do Things | ➖ | — (philosophy / technique, not a principle) | N/A. Framework is process-agnostic; the adopting repo chooses its ceremony. |
| 84 | Maintain Small Stable Teams | ➖ | — (philosophy / technique, not a principle) | N/A. Solo / small-team framework; no team-management surface. |
| 85 | Schedule It to Make It Happen | ⚠️ | §1.15 Ubiquitous Automation | `scripts/check-core-stack-agnostic.sh` + `scripts/init.sh` ship as the "make it happen" automation. No "sch... |
| 86 | Organize Fully Functional Teams | ➖ | — (philosophy / technique, not a principle) | N/A. Per-adopter concern. |
| 87 | Do What Works, Not What's Fashionable | ⚠️ | — (philosophy / technique, not a principle) | Implicit in the stack choices (no React, no ORM, no microservices). No stated policy. |
| 88 | Deliver When Users Need It | ✅ | — (philosophy / technique, not a principle) | `core/feature-protocol.md` §"Apply sites" + the Tier 3 apply-site rule pin the tip. The "first slice is the... |
| 89 | Use Version Control to Drive Builds, Tests, and Releases | ⚠️ | §1.15 Ubiquitous Automation | Per-adopter concern. Framework supports the pattern via `core/commit-and-branch.md` but no built-in CI work... |
| 90 | Test Early, Test Often, Test Automatically | ✅ | §1.15 Ubiquitous Automation | `core/tdd.md` + `scripts/check-core-stack-agnostic.sh` + the per-addendum guard-test starter set pin the tip. |
| 91 | Coding Ain't Done 'Til All the Tests Run | ✅ | §1.15 Ubiquitous Automation | `core/tdd.md` §"The loop" Steps 2-3 mandate RED → GREEN → adjacent-behavior sweep. Per-slice commits includ... |
| 92 | Use Saboteurs to Test Your Testing | ❌ | — (philosophy / technique, not a principle) | No mutation testing ships at the framework level. The per-stack guard tests catch regressions but not silen... |
| 93 | Test State Coverage, Not Code Coverage | ⚠️ | — (philosophy / technique, not a principle) | `core/tdd.md` §"Per-layer recipes" prescribes smoke probes that assert state (response shape + URL + DOM), ... |
| 94 | Find Bugs Once | ✅ | §1.15 Ubiquitous Automation | `core/tdd.md` §"Per-layer recipes" + the per-bug regression-test pattern (per `core/bug-patterns.md` §"Debu... |
| 95 | Don't Use Manual Procedures | ✅ | §1.15 Ubiquitous Automation | `scripts/init.sh` (375 lines) + `scripts/{backfill-labels,check-core-stack-agnostic,dedupe-skills,sync-labe... |
| 96 | Delight Users, Don't Just Deliver Code | ⚠️ | §1.17 Great Expectations | `core/session-protocol.md` §"Bias toward action" + `core/feature-protocol.md` §"Apply sites" carry the tip.... |
| 97 | Sign Your Work | ➖ | — (philosophy / technique, not a principle) | Duplicate of tip #73. |
| 98 | First, Do No Harm | ✅ | — (philosophy / technique, not a principle) | `core/laws.md` universal-laws pattern (every law was earned by a bug it would prevent) + §"No unguarded re-... |
| 99 | Don't Enable Scumbags | ➖ | — (philosophy / technique, not a principle) | N/A. Framework ships engineering tools, not ethics guidance for hiring / customer-interaction surfaces. |
| 100 | It's Your Life. Share it. Celebrate it. Build it. AND HAVE FUN! | ✅ | — (philosophy / technique, not a principle) | `core/session-protocol.md` §"Bias toward action" + the prose style of every `core/` doc + the `core/pragmat... |

## §7 — Summary: the 100 tips in numbers

| State | Count | What it means |
|---|---|---|
| ✅ Enforced | 52 | The repo is in compliance. The principle spine in §1 names the operational form. |
| ⚠️ Partial | 30 | The spirit is satisfied but no written rule, or no regression net. A future commit could regress without the agent noticing. |
| ❌ Gap | 3 | Not addressed. Each gap is a candidate follow-up. |
| ➖ N/A | 15 | Doesn't apply (multi-team management, hiring, hosting incidents, scheduling iteration). |

The 100-tip audit is a **check**, not a refactor. The
principle spine (§1) is the primary lens for future work; the
tip index (§6, this section) is the primary lens for checking
specific commits against the canonical book.

When a new tip is added to a future edition of the book,
append a row to this index. When a tip's state changes (a new
commit pushes a ⚠️ to ✅ or a ✅ to ⚠️), update the State
column. The index is the **summary**; the audit doc
(`docs/audit/pragmatic-programmer-audit-2026-07.md`) is the
per-tip *evidence*.

---

## §8 — References (see also §5)

- The companion audit doc: [`docs/audit/pragmatic-programmer-audit-2026-07.md`](../docs/audit/pragmatic-programmer-audit-2026-07.md) — the per-tip *evidence*.
- The regenerator: [`scripts/build_tip_index.py`](../scripts/build_tip_index.py) — reads the audit doc, writes `.scratch/appendix-final.md`. Run after every state change.
- DixieData's `docs/agents/pragmatic-principles.md` (commit `cca2183` for the original spine, commit `177c2dd` for the tip-index appendix) — the upstream this doc was ported from.
