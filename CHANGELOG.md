# Changelog

All notable changes to agent-stack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [Unreleased]

### Changed
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