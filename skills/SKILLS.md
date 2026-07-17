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
- **checksum** — sha256 of the complete bundled package at this
  manifest version. Hash sorted relative paths and LF-normalized file
  bytes using same algorithm as `scripts/dedupe-skills.sh`. Use `-` for
  planned entries whose body has not shipped yet.
- **supersedes** — optional list of upstream skill names
  this skill replaces (when the framework version is the
  preferred one)
- **load-when** — short description of when the agent
  should load this skill

`scripts/dedupe-skills.sh` validates each shipped package checksum,
walks the user's installed skill catalog (`~/.pi/agent/skills/`,
`~/.agents/skills/`, project `.pi/skills/`, project
`.agents/skills/`), and reports direct-name plus `supersedes`
overlaps. It exits 1 on checksum drift, or on overlap when run with
`--strict`.

## v0.1.0 manifest

| Name | Source | Version | Checksum | Supersedes | Load when |
|---|---|---|---|---|---|
| `tdd` | `framework-bundled` | `0.1.0` | `-` | (none yet) | Any feature or bug fix |
| `rpci` | `framework-bundled` | `0.1.0` | `-` | (none yet) | Non-trivial work (3+ files or design questions) |
| `diagnose` | `framework-bundled` | `0.1.0` | `-` | `upstream:diagnose`, `upstream:systematic-debugging`, `upstream:diagnosing-bugs` | Hard bug or performance regression |
| `tracer-bullets` | `framework-bundled` | `0.1.0` | `-` | `upstream:tracer-bullets` | Building multi-layer features |
| `find-skills` | `framework-bundled` | `0.1.0` | `-` | `upstream:find-skills` | User asks "is there a skill for X" |
| `grilling` | `framework-bundled` | `0.1.0` | `-` | `upstream:grilling` | User invokes "grill me on this plan" |
| `bulk-read` | `framework-bundled` | `0.1.0` | `-` | `upstream:bulk-read` | User asks to read all files in a folder |
| `learn-from-mistakes` | `framework-bundled` | `0.1.0` | `-` | `upstream:learn-from-mistakes` | Workspace has a MISTAKES.md file |
| `lock-requirements` | `framework-bundled` | `0.1.0` | `-` | `upstream:lock-requirements` | Feature request with overloaded terms |
| `codebase-design` | `framework-bundled` | `0.1.0` | `-` | `upstream:codebase-design` | Designing a module's interface |
| `deep-module-engineer` | `framework-bundled` | `0.1.0` | `-` | `upstream:deep-module-engineer` | Refactoring module boundaries |
| `scope-boundary-gate` | `framework-bundled` | `0.1.0` | `-` | `upstream:scope-boundary-gate` | Work risks scope creep |
| `design-an-interface` | `framework-bundled` | `0.1.0` | `-` | `upstream:design-an-interface` | Comparing interface options |
| `frontend-design` | `framework-bundled` | `0.1.0` | `-` | `upstream:frontend-design` | Building a new page or full layout |
| `domain-modeling` | `framework-bundled` | `0.1.0` | `-` | `upstream:domain-modeling` | Building / sharpening the glossary |
| `isolate-test-scope` | `framework-bundled` | `0.1.0` | `-` | `upstream:isolate-test-scope` | Test runtimes are high |
| `verify-generation-state` | `framework-bundled` | `0.1.0` | `-` | `upstream:verify-generation-state` | Editing generated assets |
| `write-a-skill` | `framework-bundled` | `0.1.0` | `-` | `upstream:write-a-skill` | User wants to author a skill |
| `pragmatic-programmer` | `framework-bundled` | `2.0.0` | `daf559117f165762ea93815805f2fb904fff890790456ea0badb7bd509546104` | `upstream:pragmatic-programmer` | Best practices, craftsmanship, DRY, technical debt, reversibility, estimation, or build-vs-buy decisions |
| `consensus-hunter` | `framework-bundled` | `0.1.0` | `d3fbc4561ce99493221b653f3f156b0dda05d13d73a486c60d975ae41e5c49ce` | (none yet) | Pre-commit / pre-merge structured risk scan; complements `bug-hunter` with a faster read-only phase producing persisted per-function risk scores |

## Dedupe contract

`scripts/dedupe-skills.sh` reports:

- Whether every shipped package matches its manifest checksum.
- Every exact installed-name overlap.
- Every installed skill named by a bundled row's `supersedes` field.
- A recommendation per pair:
  - `keep-framework` - framework-bundled version is newer or policy explicitly prefers it
  - `keep-upstream` - installed version is not older or policy explicitly prefers it
  - `keep-both` - version evidence is unavailable, so user must choose

The default behavior: keep upstream unless framework-bundled is newer.
The user can override with `--prefer=framework|upstream|none`.
`--apply` remains advisory and never deletes user files.

`scripts/init.sh` writes `.agent-stack-owned` inside skill packages it
creates. That marker permits idempotent additions and selective
`--uninit`; uninit removes whole marked package, including local edits.
Pre-existing packages are never marked or removed.

## Adding a new bundled skill

1. Create `skills/<name>/SKILL.md`. The body must follow
   the standard SKILL.md format (see the upstream
   `write-a-skill` skill for the canonical shape).
2. Add an entry to this manifest with version, checksum,
   supersedes, and load-when.
3. Run `bash scripts/dedupe-skills.sh --dry-run` to verify
   the manifest parses cleanly.

## Promoting or adapting an upstream skill

When framework adopts upstream skill:

1. Decide ownership. Use `source: upstream:<catalog>` for a verbatim or
   lightly attributed port. Use `source: framework-bundled` for a
   framework-owned workflow that only adapts upstream ideas.
2. Preserve upstream license and provenance in bundled package.
3. Add upstream catalog name to `supersedes`.
4. Give behavioral divergence a new framework semver rather than
   presenting it as byte-compatible upstream release.
5. Compute package checksum and run dedupe plus bootstrap regression
   tests.

## References

- `dedupe-skills.sh` — the dedupe contract implementation
- `../core/session-protocol.md` — when to load skills
- The upstream skill catalog (varies by agent harness)