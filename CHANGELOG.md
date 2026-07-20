# Changelog

All notable changes to agent-stack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [Unreleased]

### Added
- `docs/audit/pragmatic-tips-index-2026-07.md` (new) +
  `docs/audit/threat-models.md` (new) — two on-demand
  reference docs externalized from the spine. Tip index
  holds §6/§7/§9 of `core/pragmatic-principles.md` (the
  per-tip table + count summary + chapter cross-reference);
  threat-models holds the §Authoritative cross-references
  section of `core/bug-patterns.md` (MITRE CWE / OWASP
  mapping table + 6 source citations).
- `addenda/go-htmx-bug-catalog.md` (new, 900 lines) —
  Tier-2 companion to `addenda/go-htmx.md`. Carries the
  per-layer bug catalog §1–§6, Security (govulncheck
  workflow), and Mutation testing (go-mutesting workflow).
  Loaded on demand only; the Tier-1 addendum is what
  agents load by default for Go-adopter sessions.

### Changed
- `core/pragmatic-principles.md` (1226 → 915 lines,
  −311 / Tier-1 load) — §6/§7/§9 externalized to
  `docs/audit/pragmatic-tips-index-2026-07.md`. Spine
  now contains §1–§5 only (principles + book-end
  checklists + cross-ref table + how-to-extend +
  companion references). Bottom-of-doc pointer explains
  when to load the externalized index.
- `addenda/go-htmx.md` (1339 → 463 lines, −876 /
  Tier-1 addendum load) — split into Tier-1 addendum
  (Stack laws + Framework quirks + Go testing recipes +
  HTMX guard tests + Adopting + References) + Tier-2
  companion catalog (see Added above). Per-session
  token savings for a Go-adopter session: ~5K tokens.
- `core/bug-patterns.md` (380 → 345 lines, −35) —
  §Authoritative cross-references externalized to
  `docs/audit/threat-models.md`. The §1.5 / §1.10 /
  etc. inline CWE / OWASP refs that map directly to
  per-pattern fix recipes stay where they are.
- `core/README.md` — Tier-0 table drops commit-and-branch
  (now Tier-1); Tier-2 section gains a paragraph explaining
  the multi-file addendum pattern.
- `core/commit-and-branch.md` — Tier-1 header declaration
  added ("Tier-1. Load before any commit ...").
- `core/docs-index-scheme.md` — §Retention (placeholder,
  no current enforcer) deleted. §Prompt-cache alignment
  trimmed 16 → 7 lines (kept the "why"; dropped the
  per-harness implementation guidance).
- `core/glossary-discipline.md` — §Relationships section
  (placeholder, no pattern) deleted.
- `core/adr-discipline.md` — §ADRs vs laws (restated
  core/laws.md "Promoting a rule to a law" content)
  deleted.
- `core/testing-philosophy.md` — §Relationship to TDD
  tightened from 14 → 9 lines. Named tdd.md
  §Anti-patterns as the named-violation list with a
  direct link.
- `addenda/README.md` — v1 addenda section split into
  two bullets (Tier-1 addendum + Tier-2 catalog), each
  carrying its tier + line count + contents.

### Notes
- Total per-session savings: ~6.5K tokens (~30% of the
  Tier-0 + Tier-1 footprint for a Go-adopter session).
- The substantive overlap between `core/tdd.md` (TDD
  process) and `core/testing-philosophy.md` (quality
  bar) is structural — they play distinct roles. Moved
  sections would have broken the RED-step context in
  tdd.md and orphaned the cross-references. Kept the
  structure; tightened only the section that asked for
  clarification.
- The framework is now closer to its claimed 2K-token
  Tier-0 ceiling. Tier-0 still ships 4 docs but they're
  the ones that actually cross-cut every session
  (session-protocol + laws + docs-index-scheme +
  glossary-discipline); commit-and-branch moved to
  task-time load.

### Added (historical)
- `core/testing-philosophy.md` — port DixieData commit
  `8a0d3f1` (issue #626): the test-quality bar doc. Pairs
  with `core/tdd.md` (process) to define the bar for which
  tests earn their place. Principles: state coverage not
  line coverage (Tip #65), saboteur test (Tip #64), find
  bugs once (Tip #66), test your software (Tip #49), and
  the Go-specific carve-out (compiler/lint/stdlib already
  handle many guarantees). Includes the cut checklist, the
  table-driven consolidation rule, and the brittle-test
  mitigation. Cross-referenced from `core/tdd.md` (in
  References), `core/README.md` (tier-1 table),
  `core/pragmatic-principles.md` (§1.14 Code That's Easy
  to Test + §3 cross-ref table + §5 References), and
  `issues/feature-template.md` (new "Test quality bar"
  acceptance-criteria checkbox).
- `addenda/go-htmx.md` §'Go testing recipes' — Go-specific
  recipes that meet `core/testing-philosophy.md` bar:
  (1) `var _ Foo = bar` placement (package-level, not in
  Test func), (2) `//go:build diag` build-tag convention
  for diagnostic probes with `go test -tags=diag` invocation,
  (3) table-driven consolidation with a worked example +
  the "when NOT to consolidate" carve-out (HTMX guard tests
  own different invariants so stay separate),
  (4) mutation testing pointer to existing §'Mutation
  testing', (5) stdlib re-test anti-pattern with three
  concrete cut examples (sync.Map, strings.Contains,
  fmt.Sprintf), (6) brittle-test mitigation in Go
  (strings.Contains over ==, htmxattr.Mux allowlist over
  string literals, byte-stable primitives only). New
  section lands between §'Mutation testing' and §'References',
  grouped with the other testing-adjacent sections.
  `addenda/README.md` updated to mention Go testing recipes
  in the v1 addenda summary.

### Changed
- `scripts/init.sh` - default Q5 selection is now
  `pragmatic-programmer`; skill packages copy recursively so references
  and scripts arrive with `SKILL.md`. Existing unmanaged project skills
  are preserved, global name collisions warn, managed packages remain
  idempotent, and `--uninit` removes only agent-stack-owned skills.
- `scripts/test-pragmatic-bootstrap.sh` - scratch-target regression test
  covering default package copy, references, manifest checksums,
  idempotent re-bootstrap, and selective uninit.
- `skills/SKILLS.md` and `scripts/dedupe-skills.sh` - implement advertised
  complete-package checksum contract and effective `supersedes` overlap
  reporting. Planned unshipped rows use `-`; shipped packages validate
  against deterministic path-plus-LF-normalized-content SHA-256 values.
- `.gitattributes` - pin bundled skill packages and shell scripts to LF
  across platforms so bootstrap assets and checksums stay stable.
- `core/pragmatic-principles.md` — port DixieData commit
  `3c4fbc0` corrections: (1) §6 tip-index drift fix (rows 53-79 had
  +4-position title drift; 4 canonical tips were missing — #52
  Prefer Interfaces, #58 Random Failures, #80 Project Glossary, #97
  Sign Your Work; row #73 was mislabeled 'Sign Your Work' instead of
  canonical 'Apply Security Patches Quickly'). All 100 rows rebuilt
  against the canonical 20th Anniversary Edition tip list
  (https://pragprog.com/tips/). (2) Spine: added §1.17 Pragmatic
  Projects (Ch 9, anchor Tip #96) + §1.18 Before the Project (Ch 8,
  anchor Tip #75). Renamed §1.10 from 'It's Just a View (MVC)' to
  'Take Small Steps (Tracer Bullets + MVC seam)' so the spine title
  matches its anchor Tip #42. Header bumped 16 → 18 principles. §3
  cross-ref table updated. (3) §6 actionability upgrade: dropped the
  110-char evidence truncation; added 'When to consult this table'
  preamble (4 use cases); renamed column 'One-line evidence' →
  'Evidence / how to apply'; rewrote rows with imperative '*How to
  apply:*' / '*When violated:*' prose. Added §9 Book chapter → tip
  cross-reference appendix. §7 counts updated to 62 Enforced / 23
  Partial / 2 Gap / 13 N/A. All Dixie-specific citations re-translated
  to framework surfaces (CONTEXT.md → core/laws.md; internal/routebuilder
  → addenda/go-htmx.md §routebuilder; internal/uiids → addenda/go-htmx.md
  §uiids; internal/architecture/architecture_test.go → addenda/go-htmx.md
  HTMX-specific guard tests; etc.).
- `core/tdd.md` §Contract touch (new) — port DixieData
  commit `4edde6c` (#587): prospective DbC discipline for
  new or materially changed public seams. Five dimensions
  (preconditions, postconditions, failure modes, state
  effects, idempotency/concurrency); enforcement-site ranking
  (types → DB constraints → typed errors → architecture tests
  → behavior tests → developer-impossible-state panics);
  exported doc comments state the source-level contract, the
  RED test proves it. Ports DixieData-specific surface
  citations (Wails adapter, internal/architecture/architecture_test.go)
  to agent-stack framework equivalents (per-addendum adapters
  and architecture tests).
- `core/feature-protocol.md` — rewrite pre-flight TDD
  anchor bullet to "TDD + contract anchor"; add new
  "Contract touch" sibling to Acceptance criteria in the
  slice-plan rules. Points at `tdd.md` §Contract touch.
- `core/pragmatic-principles.md` — add §1.5 "Repo
  operational form" bullet pointing at `tdd.md`
  §Contract touch; add "Prospective contract-touch rule"
  paragraph (pragmatic DbC, not Meyer-style runtime
  contract); rewrite tip-index rows #37 (Design with
  Contracts) and #39 (Use Assertions to Prevent the
  Impossible) to point at the prospective rule and
  enforcement-site ranking.

### Added
- `skills/pragmatic-programmer/` - framework-native v2.0.0 hybrid skill,
  default-installed by bootstrap. Preserves wondelai v1.4.0 trigger,
  diagnostic, and progressive-disclosure ideas while routing principle
  authority to `core/pragmatic-principles.md`. Adds Consult, Assess, and
  Decide modes; evidence-weighted 10-point diagnostic with confidence;
  principle crosswalk; upstream provenance; and MIT attribution.
- `core/complexity.md` — principles doc pairing with `feature-protocol.md`
  §Module discipline and `session-protocol.md` Rule 3 (YAGNI). Reconciles
  the YAGNI ↔ Ousterhout tension with the net-complexity-gain test; covers
  tactical-vs-strategic programming, Hickey's decomplecting, the rule of
  three, mechanical-boundary enforcement, theory-as-deliverable (Naur),
  boring technology (McKinley), entropy budgeting (Lehman).
- `core/commit-and-branch.md` — close-on-merge discipline
  for adopting repos using GitHub Issues. New "Closing the
  issue when the work ships" section with three paths
  (commit-subject `(#N)`, commit-body `Closes #N`, periodic
  sweep) and four anti-patterns (trusting auto-close, parens
  breadcrumb, close-without-comment, ship-and-leave-open).
  Ports DixieData commit `9bd3eec`. Extends the
  Commit-message-shape rule with "Closing the issue is part
  of the slice, not a follow-up."
- `skills/consensus-hunter/` — multi-agent LLM bug-hunting skill, modelled
  on Craven's Bayesian submarine-search idea. Five evidence slices per run
  (static, history, tests, contract, spec) aggregated in logit space with
  per-agent weighting from held-out calibration. Ships with calibration
  harness (`lib/calibrate.py`), three-prior history fusion
  (`lib/prior.py`), schema (`lib/schema.py`), aggregator (`lib/aggregate.py`),
  presets, fixture examples, 33 invariant tests, and a calibration runner
  script. Validated against django @ 2020-06-01 with held-out labels from
  post-cutoff git history: Skill Score +0.24, precision@K +0.22 above
  base rate. See `skills/consensus-hunter/SKILL.md` for the design writeup.
- `.gitignore` — excludes `cal-targets/` (cloned calibration repos) and
  `.consensus-hunter/` (per-session calibration artifacts) so reproducible
  scratch state never lands in version control.
- `docs/run-on-your-codebase.md` — top-level adoption guide covering Tier 0
  (one-time scaffolding), Tier 1 (operational primitives pilot — including
  the LLM-driven calibration loop), and Tier 2 (per-PR scans + historical
  risk ledger). Operational, not design-rationale.
- `skills/consensus-hunter/OPERATIONS.md` — calibration methodology doc:
  time-aware replay protocol, the per-agent base-rate artifact (lesson
  learned from the dixiedata run), single-model 5-agent convergence,
  per-agent weight trust rules, walk-through for reproducing the
  dixiedata result. Required reading before running a calibration.

- `addenda/go-htmx.md` — Go + HTMX + templ + chi + Wails
  patterns, dialog-guard helper templates, routebuilder /
  htmxattr / uiids patterns, bug catalog §1–§6.
- `issues/` — GitHub issue framework: 6-axis label taxonomy,
  bug + feature templates, triage workflow.
- `scripts/init.sh` — interactive bootstrap for target repos
  (6 questions, idempotent, generates `FRAMEWORK_BOOTSTRAP.md`).
- `scripts/sync-labels.sh`, `scripts/backfill-labels.sh` — ported
  from real-world use, parameterised over label set.
- `scripts/dedupe-skills.sh` — reports bundled-skill overlap with
  installed upstream skill catalog; default keep upstream unless
  framework-bundled is newer.
- `scripts/check-core-stack-agnostic.sh` — regression test that
  fails CI on any vendor-specific token in `core/`. Enforces the
  core/addendum seam mechanically.
- `templates/` — boilerplate files (AGENTS.md, CONTEXT.md,
  CHANGELOG.md, CONTRIBUTING.md, GitHub issue + PR templates).
- `skills/SKILLS.md` — manifest with provenance + version +
  checksum contract. Skill bodies ship in Slice 2.

### Changed
- `core/session-protocol.md` Rule 3 — refined from a one-line YAGNI to
  "YAGNI for *features*, not for interfaces," with explicit pointer to
  `complexity.md` §1 (net-complexity-gain test) and to the
  `feature-protocol.md` two-adapter rule. Preserves grep-friendliness
  while making the YAGNI ↔ deep-modules distinction legible to agents.
- `core/README.md` — added `complexity.md` to the tier-1 "load by task"
  table; updated tier-0/1 hierarchy reference.
- `skills/SKILLS.md` — added `consensus-hunter` to v0.1.0 manifest with
  `framework-bundled` source and a load-when that distinguishes it from
  `bug-hunter` (parallel + numeric + persistent vs sequential + narrative
  + ephemeral).

### Fixed
- `core/bug-patterns.md`, `core/pragmatic-principles.md`, and
  `core/tdd.md` - restore stack-agnostic core guard after recent docs
  reintroduced desktop-runtime and source-repo examples. Examples now
  describe generic host bindings, embedded browser processes, audit
  cycles, and coverage scripts; `check-core-stack-agnostic.sh` passes.
- `templates/AGENTS.md.tmpl` and `templates/CONTRIBUTING.md.tmpl`
  referenced a non-existent `docs/agents/issue-tracker.md` and
  a `vendor/agent-stack/core/` path the init script doesn't
  produce. Re-pointed at the canonical `docs/agents/` layout.
- `core/laws.md`, `core/tdd.md`, `core/README.md` cited Wails /
  WebView2 / Chrome runtime specifics in stack-agnostic sections.
  Replaced with generic host-runtime references; the canonical
  crash history lives in `addenda/go-htmx.md`.
- `addenda/go-htmx.md` leaked source-repo-specific names
  (`X-DixieData-Redirect`, `dispatchDixieDataForm`,
  `DixieData.exe`, `.ddbak`, `data-dixie-submit`, etc.). All
  renamed to App-prefixed placeholder tokens.
- `core/laws.md`, `core/README.md`, `core/tdd.md` cleaned of
  source-repo names per the regression test.
- `scripts/init.sh` skill-copy warning now points at the Slice 2
  plan and explains the manifest-vs-bodies gap explicitly.
- `scripts/init.sh` helper functions now emit `[skip]` lines in
  real mode (not just dry-run), so re-runs are visibly
  idempotent.
- README, CHANGELOG, PLAN generalised from source-repo-specific
  phrasing to addendum-anchored phrasing.

### Notes

- Slice 1 of `PLAN.md`. Subsequent slices (skill bodies,
  additional addenda, docs site) are listed there as stubs.
- v0.1.0 audit net: `bash scripts/check-core-stack-agnostic.sh`
  exits 0; `bash scripts/init.sh <scratch>` + repeat is visibly
  idempotent; `--uninit` reverses cleanly.

### Added (v0.1.1 — research-backed upgrades)

Seven commits adopt findings from the 2024-2026 empirical
literature on LLM coding agents. Each adds inline
citations to its source.

- `core/bug-patterns.md` — 7 new AI-amplified categories
  (authorization/intent gap, hallucinated APIs,
  re-implementing stdlib, repeated code, silent error
  suppression, concurrency/dependency correctness,
  intent/business-logic mismatch) plus CWE/OWASP mapping
  table at the top. Sources: Tambon et al. 2024, DAPLab 9
  failure patterns, CodeRabbit AI vs Human report, OWASP
  Top 10:2025, MITRE CWE Top 25 (2025), OWASP LLM Top 10.
- `addenda/go-htmx.md` — 5 HTMX-specific guard tests
  (route-table integrity both directions, response-shape
  contract, swap-scope re-binding per HTMX #3300, OOB
  target integrity, route-order wildcard ordering).
  Sources: Innei/LobeHub migration field report, HTMX
  issue #3300.
- `core/laws.md` — two new universal laws: agent-context
  files hand-curated (ETH Zurich 2602.11988 + Princeton);
  Tier-0 docs have a size ceiling (Codex 32 KiB cap,
  Anthropic 20-30 line guidance).
- `core/docs-index-scheme.md` — formal 3-tier model with
  token budgets (<2K tier-0, ~5K tier-1/role, unbounded
  tier-2) and prompt-cache alignment.
- `core/rpci.md` — mandatory critique sub-step between
  GREEN and commit (deletion test + noise test + scope
  test). Skip only for one-line bug fixes.
- `core/feature-protocol.md` — slice-size rules:
  ≤50% context, <500 LOC diff, one observable behaviour,
  fresh context per slice. Sources: Pocock aihero.dev,
  Miller jeremydmiller.com, CodeRabbit PR audit.
- `core/subagent-pattern.md` — new tier-1 doc. When to
  delegate to subagent vs inline; manifest schema; the
  verifier-subagent pattern.
- `core/adr-discipline.md` — new tier-1 doc. Append-only
  ADRs modelled on Vercel ai + Living ADR pattern.
- `core/agent-memory.md` — new tier-1 doc. CHECKPOINT /
  REHydrate pattern; `agent-notes/` + `agent-checkpoints/`
  layout.
- `templates/AGENTS.md.tmpl` — rewritten per Roland Huss
  separation-of-concerns; 20-30 line ceiling; Claude Code
  `@import` convention.
- `templates/AGENT_NOTES.md.tmpl` — bootstrap template for
  the memory layout.
- `core/README.md` — index updated to list the new tier-1
  docs.

Regression net: `bash scripts/check-core-stack-agnostic.sh`
still exits 0; `bash scripts/init.sh /tmp/x --dry-run`
walks the interactive flow without errors.