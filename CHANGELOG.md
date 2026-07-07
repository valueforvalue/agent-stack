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
  from DixieData, parameterized over label set.
- `scripts/dedupe-skills.sh` — reports bundled-skill overlap with
  installed upstream skill catalog; default keep upstream unless
  framework-bundled is newer.
- `templates/` — boilerplate files (AGENTS.md, CONTEXT.md,
  CHANGELOG.md, CONTRIBUTING.md, GitHub issue + PR templates).
- `skills/SKILLS.md` — manifest with provenance + version +
  checksum contract. Skill bodies ship in Slice 2.

### Notes

- Slice 1 of `PLAN.md`. Subsequent slices (skill bodies,
  additional addenda, docs site) are listed there as stubs.