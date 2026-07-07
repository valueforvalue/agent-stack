# SKILLS.md — Agent Skill Manifest

The agent-stack bundles a curated subset of agent skills
under `skills/`. This file is the manifest: every skill
listed here with its provenance, version, checksum, and
the dedupe contract.

## Manifest contract

Each entry has:

- **name** — the skill's canonical name (matches the
  directory name under `skills/`)
- **source** — where the skill body originated
  (`framework-bundled`, `upstream:<catalog>`, or
  `upstream:<github-repo>`)
- **version** — semver of the bundled body
- **checksum** — sha256 of the SKILL.md body at this
  manifest version
- **supersedes** — optional list of upstream skill names
  this skill replaces (when the framework version is the
  preferred one)
- **load-when** — short description of when the agent
  should load this skill

`scripts/dedupe-skills.sh` reads this manifest, walks the
user's installed skill catalog (`~/.pi/agent/skills/`,
`~/.agents/skills/`, project `.pi/skills/`, project
`.agents/skills/`), reports overlaps, and exits 0 (or 1 with
`--strict`).

## v0.1.0 manifest (Slice 2 will fill bodies)

| Name | Source | Version | Supersedes | Load when |
|---|---|---|---|---|
| `tdd` | `framework-bundled` | `0.1.0` | (none yet) | Any feature or bug fix |
| `rpci` | `framework-bundled` | `0.1.0` | (none yet) | Non-trivial work (3+ files or design questions) |
| `diagnose` | `framework-bundled` | `0.1.0` | `upstream:diagnose`, `upstream:systematic-debugging`, `upstream:diagnosing-bugs` | Hard bug or performance regression |
| `tracer-bullets` | `framework-bundled` | `0.1.0` | `upstream:tracer-bullets` | Building multi-layer features |
| `find-skills` | `framework-bundled` | `0.1.0` | `upstream:find-skills` | User asks "is there a skill for X" |
| `grilling` | `framework-bundled` | `0.1.0` | `upstream:grilling` | User invokes "grill me on this plan" |
| `bulk-read` | `framework-bundled` | `0.1.0` | `upstream:bulk-read` | User asks to read all files in a folder |
| `learn-from-mistakes` | `framework-bundled` | `0.1.0` | `upstream:learn-from-mistakes` | Workspace has a MISTAKES.md file |
| `lock-requirements` | `framework-bundled` | `0.1.0` | `upstream:lock-requirements` | Feature request with overloaded terms |
| `codebase-design` | `framework-bundled` | `0.1.0` | `upstream:codebase-design` | Designing a module's interface |
| `deep-module-engineer` | `framework-bundled` | `0.1.0` | `upstream:deep-module-engineer` | Refactoring module boundaries |
| `scope-boundary-gate` | `framework-bundled` | `0.1.0` | `upstream:scope-boundary-gate` | Work risks scope creep |
| `design-an-interface` | `framework-bundled` | `0.1.0` | `upstream:design-an-interface` | Comparing interface options |
| `frontend-design` | `framework-bundled` | `0.1.0` | `upstream:frontend-design` | Building a new page or full layout |
| `domain-modeling` | `framework-bundled` | `0.1.0` | `upstream:domain-modeling` | Building / sharpening the glossary |
| `isolate-test-scope` | `framework-bundled` | `0.1.0` | `upstream:isolate-test-scope` | Test runtimes are high |
| `verify-generation-state` | `framework-bundled` | `0.1.0` | `upstream:verify-generation-state` | Editing generated assets |
| `write-a-skill` | `framework-bundled` | `0.1.0` | `upstream:write-a-skill` | User wants to author a skill |

## Dedupe contract

`scripts/dedupe-skills.sh` reports:

- For each entry in this manifest, whether the user has
  the listed `source` installed and at what version.
- For each upstream skill named in `supersedes`, whether
  the user has that skill installed and at what version.
- A recommendation per pair:
  - `keep-framework` — framework-bundled version is newer
  - `keep-upstream` — upstream version is newer (default)
  - `keep-both` — divergent bodies, user must choose
  - `drop-both` — neither is referenced by the user

The default behavior: **keep upstream unless
framework-bundled is newer** (per the resolved Q-E from
`PLAN.md`). The user can flip with
`--prefer=framework|upstream|none`.

## Adding a new bundled skill

1. Create `skills/<name>/SKILL.md`. The body must follow
   the standard SKILL.md format (see the upstream
   `write-a-skill` skill for the canonical shape).
2. Add an entry to this manifest with version, checksum,
   supersedes, and load-when.
3. Run `bash scripts/dedupe-skills.sh --dry-run` to verify
   the manifest parses cleanly.

## Promoting an upstream skill to bundled

When the framework adopts an upstream skill:

1. Copy the skill body into `skills/<name>/SKILL.md` with
   a header attributing the source.
2. Add the upstream catalog name to `source` (e.g.
   `upstream:pi-aftc-toolset`).
3. Add the upstream skill name to `supersedes` (the
   framework-bundled version supersedes the upstream).
4. Bump the version in the manifest.

## References

- `dedupe-skills.sh` — the dedupe contract implementation
- `../core/session-protocol.md` — when to load skills
- The upstream skill catalog (varies by agent harness)