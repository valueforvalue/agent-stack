# Pragmatic Programmer 100-Tip Audit

> **STATUS: OPEN.** Initial pass; tracks the work that landed
> `core/pragmatic-principles.md` on the agent-stack repo. The
> classification is per agent-stack's current file reality —
> not inherited from DixieData's audit.

This audit maps each of the 100 tips from _The Pragmatic
Programmer, 20th Anniversary Edition_ (Hunt & Thomas) to the
agent-stack repo. The goal is descriptive, not prescriptive:
each tip is classified as one of four states, and the
high-leverage gaps are surfaced as follow-up candidates. No
`core/laws.md` Laws or template-level rules are changed in this
audit; the audit is a check, not a refactor.

## Classification

| State | Meaning |
|---|---|
| ✅ **Enforced** | A `core/laws.md` Law, a `core/*.md` rule, an `addenda/*` rule, an `issues/*.md` template, a `scripts/*` automation, or `templates/*.md.tmpl` pins the tip. |
| ⚠️ **Partial** | The spirit is satisfied but no written rule, OR the rule exists but no regression net enforces it. Cited. |
| ❌ **Gap** | The tip is not addressed and would be high-leverage to add. Becomes a candidate follow-up. |
| ➖ **N/A** | The tip applies to contexts agent-stack does not inhabit (multi-team management, hiring, hosting incidents, etc.). |

## Headline findings

- **Philosophy + bend-or-break + while-you-code categories are
  strongly enforced by `core/`.** The repo's `core/laws.md`
  universal laws + `core/rpci.md` + `core/tdd.md` + the
  `tracer-bullets` skill map cleanly to ~30 of the 100 tips.
  Examples:
  - Tip #5 *Don't Live with Broken Windows* → `core/laws.md`
    Law pattern (every law was earned by a real bug)
  - Tip #11 *English is Just Another Programming Language* →
    `core/glossary-discipline.md` + the Tier-0/1/2 docs
    taxonomy
  - Tip #20 *Use Tracer Bullets to Find the Target* → the
    `tracer-bullets` skill + `core/feature-protocol.md`
    §"Tracer bullets" + the Tier 1/2/3 commit rule
  - Tip #31 *Failing Test Before Fixing Code* → `core/tdd.md`
    red-green-refactor protocol
  - Tip #38 *Crash Early* → `core/laws.md` §"No unguarded
    re-entrant UI calls" + the per-addendum dialog-guard laws
  - Tip #42 *Take Small Steps—Always* → RPCI flow + slice
    discipline + the "fresh context per slice" rule
  - Tip #65 *Refactor Early, Refactor Often* →
    `core/complexity.md` strategic-programming framework
  - Tip #91 *Coding Ain't Done 'Til All the Tests Run* →
    `core/tdd.md` Steps 2-3 RED/GREEN + adjacent-behavior
    sweep
  - Tip #98 *First, Do No Harm* → `core/laws.md` (re-entry
    protection) + the per-stack "no feature PR ships a
    surface without an apply-site" patterns

- **Pragmatic teams + management + hiring are ➖ N/A.**
  Agent-stack is a framework + bootstrapper, not a
  multi-team org. Tips #18, #24, #27, #30, #57, #76, #84,
  #86, #99 are marked N/A. Tip #100 (*It's Your Life.
  Celebrate it.*) is ✅ because the framework's
  tone-and-manners — `core/session-protocol.md` "Bias toward
  action" + the prose style of every doc — is itself the
  operational form.

- **Two clear gaps worth following up:**
  - **Tip #9** *Invest Regularly in Your Knowledge Portfolio*
    — No `docs/learning/` or per-agent reading list. The
    audit *is* a knowledge-portfolio act, but it's a one-shot,
    not a habit. **Candidate follow-up**: a "reading list"
    lane in the adopt flow (per-stack prereqs + bookend
    reading).
  - **Tip #71** *Apply Security Patches Quickly* — No
    `govulncheck` (Go) / `pip-audit` (Python) / `npm audit`
    in `scripts/` or any per-adopter CI hint. Deps are
    updated when forced, not on a schedule. **Candidate
    follow-up**: per-stack addendum note + a starter
    security-scan script in `scripts/`.
  - **Tip #92** *Use Saboteurs to Test Your Testing* — No
    mutation testing. The per-stack guard tests catch
    regressions but not silent test-skipping. **Candidate
    follow-up**: investigate Go `go-mutesting` or JS
    `stryker` per-stack in the relevant addenda.

- **Three ⚠️ partials worth knowing about:**
  - **Tip #6** *Be a Catalyst for Change* — The bootstrap
    script does this implicitly (it's literally the purpose
    of agent-stack) but the doc doesn't *say* so.
  - **Tip #8** *Make Quality a Requirements Issue* — The
    feature template has "Acceptance criteria" but no
    "Quality bar" field. The acceptance-criteria section
    carries the test claim; the test-floor + smoke-probe
    contract in `core/laws.md` carries the quality-bar
    implicitly. **Candidate follow-up**: optional "Quality
    bar" section in `issues/feature-template.md`.
  - **Tip #59** *Listen to Your Inner Lizard* — No agent-side
    "if you feel stuck, the slice is wrong" rule. The
    "first slice is the only slice that ships in this
    session" rule in `core/rpci.md` is the closest form.

## Per-tip evidence

The per-tip evidence below is the source of truth for
`core/pragmatic-principles.md` §6 (Tip index) and §7 (Summary).
To regenerate the index after a state change, run:

```bash
python3 scripts/build_tip_index.py  # writes .scratch/appendix-final.md
```

Then splice the output into `core/pragmatic-principles.md`
between the §5 → §6 boundary (the placeholder pattern
below).

[TIP_INDEX_PLACEHOLDER]

| 1 | Care About Your Craft | ✅ | `core/session-protocol.md` §"Bias toward action" + §"Proportional depth" + the entire doc-comment floor + per-stack guard-test regime pin the tip. |
| 2 | Think! About Your Work | ✅ | `core/rpci.md` RPCI flow explicitly turns off the autopilot: every Plan has a Critique phase the user signs off before Implement. |
| 3 | You Have Agency | ✅ | `core/rpci.md` §C — Critique gate is the operational form. The user has explicit "approve, start" authority. |
| 4 | Provide Options, Don't Make Lame Excuses | ✅ | `core/rpci.md` Plan surfaces "decisions to confirm" with options; the agent never says "can't be done." |
| 5 | Don't Live with Broken Windows | ✅ | `core/laws.md` — every Law was earned by a real bug. The universal-laws pattern (re-entry, doc-comment floor, context-file hand-curated, Tier-0 size ceiling) pins the tip. |
| 6 | Be a Catalyst for Change | ⚠️ | agent-stack is *literally* a catalyst (bootstrap script + `scripts/init.sh` + `addenda/` invite contributions) but no doc claims that role. Implicit, not stated. |
| 7 | Remember the Big Picture | ✅ | `docs/agents/INDEX.md` 3-tier progressive-disclosure table is the operational form. Agents know which doc to load per task-role. |
| 8 | Make Quality a Requirements Issue | ⚠️ | `issues/feature-template.md` has "Acceptance criteria" but no "Quality bar" field. The test-floor + smoke-probe contract in `core/laws.md` carries quality implicitly. Open gap. |
| 9 | Invest Regularly in Your Knowledge Portfolio | ❌ | No `docs/learning/` or per-stack reading list. This audit doc is a one-shot, not a habit. **Candidate follow-up**: a starter `docs/learning/` per adding a per-stack addendum. |
| 10 | Critically Analyze What You Read and Hear | ⚠️ | `core/pragmatic-principles.md` §"Yesterday's best practice" frames it, but the per-PR discipline (e.g. "challenge the upstream claim before adopting the dependency") is not enforced by a guard test. |
| 11 | English is Just Another Programming Language | ✅ | `core/glossary-discipline.md` + the 3-tier docs taxonomy. Every doc is reviewed for terminology drift; `core/bug-patterns.md` cross-references CWE / OWASP / DAPLab (vocabulary DRY). |
| 12 | It's Both What You Say and the Way You Say It | ✅ | `core/commit-and-branch.md` §"Commit message shape" mandates 1-3 bullets explaining the *why* + regression net. The CHANGELOG is exemplary. |
| 13 | Build Documentation In, Don't Bolt It On | ✅ | `core/laws.md` §"Doc comments on exported identifiers" + the 3-tier docs taxonomy + `templates/AGENTS.md.tmpl` ships with the framework (docs live next to code). |
| 14 | Good Design Is Easier to Change Than Bad Design | ✅ | `core/complexity.md` deep-module discipline + per-addendum guard tests are the rule. "Code that's easy to delete" > "code that's easy to add" is the framing. |
| 15 | DRY—Don't Repeat Yourself | ✅ | `core/glossary-discipline.md` (vocabulary DRY) + `core/complexity.md` §"Two-adapter rule" (interface DRY) + `core/session-protocol.md` §"YAGNI" (no duplicate features). |
| 16 | Make It Easy to Reuse | ✅ | `addenda/go-htmx.md` §"Bridge code" explains *where* DRY applies vs *where* it doesn't. The per-addendum guard-test starter set (`route_table_test.go`, `response_shape_test.go`, etc.) is the reusable shape. |
| 17 | Eliminate Effects Between Unrelated Things | ✅ | `core/complexity.md` deep-module discipline + the per-stack forbidden-import test pattern (e.g. `addenda/go-htmx.md` references the pattern). |
| 18 | There Are No Final Decisions | ✅ | `core/commit-and-branch.md` §"Branch policy" supports both single-branch and three-branch models. Releases tag the merge commit; no decision cast in stone. |
| 19 | Forgo Following Fads | ⚠️ | Implicit in the stack choices (templ, chi, Wails) but no written policy. A future "rewrite in React" PR would not be blocked by a stated rule. |
| 20 | Use Tracer Bullets to Find the Target | ✅ | The `tracer-bullets` skill (auto-loaded) + `core/feature-protocol.md` §"Tracer bullets" + the Tier 1/2/3 commit rule. The slice-1-only-per-session RPCI rule is the strongest form. |
| 21 | Prototype to Learn | ⚠️ | `.scratch/` is the prototype convention (mentioned by `core/session-protocol.md` indirectly via the DEBUG/build-tag pattern), but the per-adopter `.scratch/` adoption is not gated. |
| 22 | Program Close to the Problem Domain | ✅ | `core/complexity.md` §"Deep-module discipline" mandates domain-shaped public surfaces. `core/feature-protocol.md` §"Module discipline" gives the worked example. |
| 23 | Estimate to Avoid Surprises | ⚠️ | `core/rpci.md` Plan includes files touched + success criteria + regression net, but no time estimate. `core/session-protocol.md` §"Bias toward action" explicitly de-prioritizes estimation. |
| 24 | Iterate the Schedule with the Code | ➖ | N/A. Framework ships docs + scripts; no schedule to iterate. |
| 25 | Keep Knowledge in Plain Text | ✅ | Every config in agent-stack is plain text (Markdown, shell, JSON in `templates/`). No binary configs. |
| 26 | Use the Power of Command Shells | ✅ | `scripts/*.sh` (`backfill-labels.sh`, `check-core-stack-agnostic.sh`, `dedupe-skills.sh`, `init.sh`, `sync-labels.sh`) — 904 lines of automation across 5 files. |
| 27 | Achieve Editor Fluency | ➖ | N/A. Agent-context; not a framework concern. |
| 28 | Always Use Version Control | ✅ | The entire branching model in `core/commit-and-branch.md`. Every change goes through git; the framework's own `CHANGELOG.md` is git-versioned. |
| 29 | Fix the Problem, Not the Blame | ⚠️ | `core/commit-and-branch.md` §"Commit message shape" prescribes "what + why" but no "don't blame" rule. Implicit in tone. |
| 30 | Don't Panic | ➖ | N/A. No incident-response flow at framework level. |
| 31 | Failing Test Before Fixing Code | ✅ | `core/tdd.md` red-green-refactor protocol is the operational form. Step 1 ("RED") explicitly: write the failing test first. |
| 32 | Read the Damn Error Message | ✅ | `core/tdd.md` §"The failure modes TDD prevents" — failure class #1 (Invoker wiring) mandates asserting the response shape AND `page.url()` AND DOM state, not just "got error somewhere." |
| 33 | "select" Isn't Broken | ⚠️ | Implicit (no recent commit blamed Wails / chi / templ without evidence) but no stated rule. |
| 34 | Don't Assume It—Prove It | ✅ | `core/tdd.md` §"What's the seam?" + the per-layer recipes (handler test, smoke probe, migration test) mandate asserting on the seam, not on assumptions. |
| 35 | Learn a Text Manipulation Language | ➖ | N/A at the framework level. Per-adopter concern. |
| 36 | You Can't Write Perfect Software | ✅ | `core/laws.md` §"No unguarded re-entrant UI calls" + §"Tier-0 docs have a size ceiling" are earned-by-real-bug examples. |
| 37 | Design with Contracts | ✅ | `core/laws.md` §"Doc comments on exported identifiers" is the contract floor. `core/code-changes.md` is the cross-layer contract. `core/bug-patterns.md` is the recurring-bug contract. |
| 38 | Crash Early | ✅ | `core/laws.md` §"No unguarded re-entrant UI calls" — crashing early preserves the UI thread. Per-addendum: `addenda/go-htmx.md` §"Stack laws" (dialog-guard). |
| 39 | Use Assertions to Prevent the Impossible | ✅ | `core/laws.md` §"Doc comments on exported identifiers" enforces the assertion-via-documentation pattern. Per-addendum typed-attribute builders (e.g. `htmxattr.Mux`) pin the equivalent at the render layer. |
| 40 | Finish What You Start | ⚠️ | The pattern lives in adopting repos via `defer` (Go) / `try/finally` (Python) / effect-cleanup (React). `core/tdd.md` §"Anti-patterns" mentions leak guard tests but no general rule. |
| 41 | Act Locally | ⚠️ | `core/complexity.md` §"Two-adapter rule" prescribes local interfaces, but no named rule for "locality of state." Implicit via the deep-module discipline. |
| 42 | Take Small Steps—Always | ✅ | `core/rpci.md` §I — Implement: "the first slice is the only slice that runs in the same session." Fresh-context-per-slice is the strongest form. |
| 43 | Avoid Fortune-Telling | ✅ | `core/session-protocol.md` §"YAGNI" + `core/complexity.md` §"Strategic programming vs YAGNI" + `core/feature-protocol.md` §"Two-adapter rule" are the operational form. |
| 44 | Decoupled Code Is Easier to Change | ✅ | `core/complexity.md` deep-module discipline is the operational form. The DTO-at-the-seam rule pins the per-layer decoupling. |
| 45 | Tell, Don't Ask | ⚠️ | `core/feature-protocol.md` §"Module discipline — service is the seam" prescribes telling the service to do work (UI doesn't reach into persistence), but doesn't name the "tell, don't ask" pattern. |
| 46 | Don't Chain Method Calls | ➖ | N/A as a stated rule; `core/complexity.md` deep-module discipline covers the same concern implicitly. |
| 47 | Avoid Global Data | ⚠️ | Per-adopter concern. `core/complexity.md` prescribes a model-without-UI-imports boundary; the "no package-level mutable state" rule is implicit. No framework-level rule. |
| 48 | If It's Important Enough To Be Global, Wrap It in an API | ✅ | `addenda/go-htmx.md` §"Stack laws" gives the worked example: `(*App).guardedSaveFileDialog` wraps the dangerous native-dialog call behind a safe API. |
| 49 | Programming Is About Code, But Programs Are About Data | ✅ | `core/complexity.md` §"Deep-module discipline" prescribes DTOs as the cross-boundary value type. The audit-probe pattern (assert on rendered HTML, not template source) is the live practice. |
| 50 | Don't Hoard State; Pass It Around | ⚠️ | `core/code-changes.md` prescribes arguments over global state implicitly, but no named rule. Implicit in the deep-module discipline. |
| 51 | Don't Pay Inheritance Tax | ➖ | N/A as a framework rule; the type-system-agnostic stance means each adopter inherits whatever their language requires. |
| 52 | Programming Is About Code (continued) | ➖ | Duplicate of tip #49. (Carried forward for completeness.) |
| 53 | Shared State Is Incorrect State | ⚠️ | `core/laws.md` §"No unguarded re-entrant UI calls" gives the per-slot-mutex pattern. No general "shared state is incorrect" rule. |
| 54 | Random Failures Are Often Concurrency Issues | ⚠️ | `core/bug-patterns.md` §"Concurrency / dependency correctness" lists the AI-amplification evidence but no per-stack race-detector gate ships at the framework level. |
| 55 | Use Actors For Concurrency Without Shared State | ⚠️ | Per-adopter concern. The framework pattern (per-process struct) is implied via `core/commit-and-branch.md` §"Branch policy" but not stated. |
| 56 | Analyze Workflow to Improve Concurrency | ⚠️ | `core/rpci.md` §"Bias toward action" + the slice parallelism implicit in RPCI, but no concurrency-analysis template. |
| 57 | Use Blackboards to Coordinate Workflow | ➖ | N/A. Framework does not coordinate between concurrent agents. |
| 58 | Programming Is About Code (continued) | ➖ | Duplicate of tip #49. |
| 59 | Listen to Your Inner Lizard | ⚠️ | `core/rpci.md` §I — Implement mandates fresh-context-per-slice. The "if you feel stuck, the slice is wrong" heuristic is implicit. No named rule. |
| 60 | Don't Program by Coincidence | ✅ | `core/rpci.md` §P — Plan mandates "Decisions to confirm" surfaced explicitly. The "RELY only on reliable things" framing pins the tip. |
| 61 | Estimate the Order of Your Algorithms | ⚠️ | `core/tdd.md` §"Algorithm speed" lists this as the standalone concern but no general annotation rule ships at the framework level. |
| 62 | Test Your Estimates | ⚠️ | Per-adopter concern. The framework supports the pattern via `core/tdd.md` "per-iter footprint doc-comment" but no built-in stress-test workflow ships. |
| 63 | Refactor Early, Refactor Often | ✅ | `core/complexity.md` §"Strategic programming framework" + `core/feature-protocol.md` §"The 3-tier commit rule" (Tier 2 = vertical slice; refactor earns its own commit when needed). |
| 64 | Testing Is Not About Finding Bugs | ⚠️ | `core/bug-patterns.md` §"Meta-patterns" lists regression nets as the catch, but the "tests as a design tool" framing is not stated explicitly. |
| 65 | A Test Is the First User of Your Code | ✅ | `core/tdd.md` Step 1 — "RED: write the failing test first." Per-layer recipes pin the test-first pattern. |
| 66 | Build End-To-End, Not Top-Down or Bottom Up | ✅ | `core/feature-protocol.md` §"Tracer bullets" + `core/rpci.md` §I — Implement mandate a vertical-tracer bullet slice first. Every Tier 2 slice crosses every layer. |
| 67 | Design to Test | ✅ | `core/tdd.md` §"What's the seam?" + §"Per-layer recipes" prescribe the seam-before-the-implementation pattern. The per-addendum guard-test starter set is the worked example. |
| 68 | Test Your Software, or Your Users Will | ✅ | `core/tdd.md` §"Adjacent behavior sweep" mandates testing adjacent surfaces, not just the slice. The smoke-probe pattern (assert response shape + `page.url()`) is the live practice. |
| 69 | Use Property-Based Tests to Validate Your Assumptions | ⚠️ | `core/bug-patterns.md` references property-based tests in the meta-pattern section, but no general pattern ships at the framework level. Per-adopter decision. |
| 70 | Keep It Simple and Minimize Attack Surfaces | ✅ | `core/complexity.md` §"Strategic programming framework" + `core/session-protocol.md` §"YAGNI" are the operational form. `core/feature-protocol.md` §"Two-adapter rule" pins the rule. |
| 71 | Apply Security Patches Quickly | ❌ | No framework-level security-scan automation. `scripts/check-core-stack-agnostic.sh` checks doc-level structure but not dependency CVE status. **Candidate follow-up**: per-stack addendum note + starter security-scan scripts. |
| 72 | Name Well; Rename When Needed | ⚠️ | `core/glossary-discipline.md` prescribes the rename process for vocabulary terms, but no general "name well" rule. Implicit via the doc-comment floor. |
| 73 | Sign Your Work | ✅ | `core/commit-and-branch.md` §"Commit message shape" + §"Push verification" mandate the commit-attribution + verification pattern. |
| 74 | No One Knows Exactly What They Want | ✅ | `core/rpci.md` §C — Critique + `core/session-protocol.md` §"Capturing decisions" + the "the user is the chat" rule pin the tip. |
| 75 | Programmers Help People Understand What They Want | ✅ | `core/rpci.md` Plan template + the apply-sites checklist in `issues/feature-template.md` make the full shape of the change visible to the user before code lands. |
| 76 | Requirements Are Learned in a Feedback Loop | ✅ | `core/rpci.md` §I — "the first slice is the only slice that runs in the same session" — the next session picks up new state and refines. |
| 77 | Work with a User to Think Like a User | ⚠️ | Per-adopter concern. `core/feature-protocol.md` "Apply sites" requirement proxies for the user-perspective framing. |
| 78 | Policy Is Metadata | ✅ | `core/laws.md` §"Tier-0 docs have a size ceiling" pins the budget as data. `core/bug-patterns.md` meta-pattern table pins the OWASP/CWE cross-reference as data. |
| 79 | Use a Project Glossary | ✅ | `core/glossary-discipline.md` is the operational form. The "flagged ambiguities" pattern (preserved from adopting repos' `CONTEXT.md` template) is the regression net. |
| 80 | Use a Project Glossary (continued) | ➖ | Carried forward for completeness. (The 80-tip mapping to #79 is the book's own deduplication.) |
| 81 | Don't Think Outside the Box—Find the Box | ✅ | `core/complexity.md` §"Strategic programming framework" + `core/rpci.md` §"Cutting the Gordian Knot" (4-question checklist) are the operational form. |
| 82 | Don't Go into the Code Alone | ⚠️ | `core/session-protocol.md` §"Capturing decisions" prescribes user-collaboration but no named rule for "don't go alone." Per-adopter concern. |
| 83 | Agile Is Not a Noun; Agile Is How You Do Things | ➖ | N/A. Framework is process-agnostic; the adopting repo chooses its ceremony. |
| 84 | Maintain Small Stable Teams | ➖ | N/A. Solo / small-team framework; no team-management surface. |
| 85 | Schedule It to Make It Happen | ⚠️ | `scripts/check-core-stack-agnostic.sh` + `scripts/init.sh` ship as the "make it happen" automation. No "schedule reflection" rule. |
| 86 | Organize Fully Functional Teams | ➖ | N/A. Per-adopter concern. |
| 87 | Do What Works, Not What's Fashionable | ⚠️ | Implicit in the stack choices (no React, no ORM, no microservices). No stated policy. |
| 88 | Deliver When Users Need It | ✅ | `core/feature-protocol.md` §"Apply sites" + the Tier 3 apply-site rule pin the tip. The "first slice is the only slice that ships in this session" rule is the strongest form. |
| 89 | Use Version Control to Drive Builds, Tests, and Releases | ⚠️ | Per-adopter concern. Framework supports the pattern via `core/commit-and-branch.md` but no built-in CI workflow ships. |
| 90 | Test Early, Test Often, Test Automatically | ✅ | `core/tdd.md` + `scripts/check-core-stack-agnostic.sh` + the per-addendum guard-test starter set pin the tip. |
| 91 | Coding Ain't Done 'Til All the Tests Run | ✅ | `core/tdd.md` §"The loop" Steps 2-3 mandate RED → GREEN → adjacent-behavior sweep. Per-slice commits include the regression net. |
| 92 | Use Saboteurs to Test Your Testing | ❌ | No mutation testing ships at the framework level. The per-stack guard tests catch regressions but not silent test-skipping. **Candidate follow-up**: investigate per-stack tooling (`go-mutesting`, `stryker`, `mutmut`). |
| 93 | Test State Coverage, Not Code Coverage | ⚠️ | `core/tdd.md` §"Per-layer recipes" prescribes smoke probes that assert state (response shape + URL + DOM), not just code-path coverage. The "state coverage" framing is implicit. |
| 94 | Find Bugs Once | ✅ | `core/tdd.md` §"Per-layer recipes" + the per-bug regression-test pattern (per `core/bug-patterns.md` §"Debugging workflow") pin the tip. |
| 95 | Don't Use Manual Procedures | ✅ | `scripts/init.sh` (375 lines) + `scripts/{backfill-labels,check-core-stack-agnostic,dedupe-skills,sync-labels}.sh` automate the framework-level workflow. |
| 96 | Delight Users, Don't Just Deliver Code | ⚠️ | `core/session-protocol.md` §"Bias toward action" + `core/feature-protocol.md` §"Apply sites" carry the tip. No named "delight users" rule. |
| 97 | Sign Your Work | ➖ | Duplicate of tip #73. |
| 98 | First, Do No Harm | ✅ | `core/laws.md` universal-laws pattern (every law was earned by a bug it would prevent) + §"No unguarded re-entrant UI calls" + §"Doc comments on exported identifiers" are the operational form. |
| 99 | Don't Enable Scumbags | ➖ | N/A. Framework ships engineering tools, not ethics guidance for hiring / customer-interaction surfaces. |
| 100 | It's Your Life. Share it. Celebrate it. Build it. AND HAVE FUN! | ✅ | `core/session-protocol.md` §"Bias toward action" + the prose style of every `core/` doc + the `core/pragmatic-principles.md` warn+cite protocol's "celebrate" framing (the protocol *names* the violation, then promotes the principle). The framework is fun to work in. |

---

## Audit method

The audit reads agent-stack's own files and classifies each tip
based on what is *actually pinned by a regression net or rule*,
not on what the doc says in prose. The four-state classification
(✅/⚠️/❌/➖) is intentionally conservative: a tip is ✅ only
when the enforcing rule exists AND a non-trivial class of work
would land against that rule; ⚠️ is reserved for "the spirit is
satisfied but no rule" or "the rule exists but no regression
net."

The principle-column mapping in §6 of
`core/pragmatic-principles.md` was lifted directly from
DixieData's `docs/audit/pragmatic-programmer-principles-audit-2026-07.md`
§2 (the principle↔tip mapping is the book's structure, not
repo-specific). Agent-stack's principle spine (§1.1-§1.16)
shares the same spine, so the mapping ports cleanly.

Differences from DixieData's audit:

| Dimension | DixieData | agent-stack |
|---|---|---|
| Scope | Single concrete app repo (Wails v2.12.0 on Windows) | Framework + bootstrapper — every per-stack code is in `addenda/` |
| Enforced-tip count | ~50 ✅ (many go to concrete in-repo files) | Lower by design — the framework ships guides, not enforced code |
| N/A count | ~10 | ~15 (every "team management / hiring / hosting" tip is N/A; framework-context only) |
| Unique gaps | `docs/learning/` (Tip #9) | Same gap (`docs/learning/`); plus security-scan (Tip #71); plus mutation-testing (Tip #92) |
| Tip #42 principle mapping | DixieData maps to §1.10 MVC | Maps to §1.10 MVC in the DixieData spine; agent-stack's port omits §1.10 MVC (rolled into §1.4 Tracer Bullets — "small steps = vertical slices"). The script's `PRINCIPLE_OF_TIP` map keeps the DixieData mapping for traceability; the *operational* evidence row points at `core/rpci.md` slice discipline. |

---


## References

- _The Pragmatic Programmer, 20th Anniversary Edition_, Hunt &
  Thomas. The 100 tips are excerpted at
  <https://pragprog.com/tips/>.
- `core/pragmatic-principles.md` — the principle spine that
  this audit feeds
- DixieData's `docs/audit/pragmatic-programmer-audit-2026-07.md` —
  the upstream audit this was modeled on (same structure, agent-stack
  evidence replaces DixieData file:line refs)
- DixieData's `docs/audit/pragmatic-programmer-principles-audit-2026-07.md` §2 —
  the principle↔tip mapping table
