# Changelog

All notable changes to agent-stack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [Unreleased]

### Added
- `core/` — stack-agnostic rules (session protocol, commit &
  branch policy, RPCI flow, TDD discipline, feature protocol,
  cross-layer contract, laws, docs-index scheme, glossary
  discipline, bug-pattern catalog with per-layer stubs).
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