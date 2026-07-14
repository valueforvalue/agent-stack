#!/usr/bin/env bash
# check-mutations.sh — framework-level template for per-adopter
# mutation-test automation. Tip #92 (Use Saboteurs to Test
# Your Testing).
#
# Mutation testing **deliberately breaks your code in small
# ways** (e.g. flip `>` to `>=`, swap `&&` to `||`,
# replace `+` with `-`) and checks whether your test suite
# catches the break. A test suite that doesn't catch a
# mutation is a test suite with blind spots.
#
# Per-stack pickers:
#
#   Go:     go-mutesting (https://github.com/avito-tech/go-mutesting)
#   Node:   stryker (https://stryker-mutator.io/)
#   Python: mutmut (https://mutmut.readthedocs.io/)
#   Rust:   cargo-mutants (https://github.com/sourcefrog/cargo-mutants)
#   Ruby:   mutant (https://github.com/mbj/mutant)
#
# One tool per stack, same picker-rule as check-security.sh.
#
# Usage:
#   bash scripts/check-mutations.sh                   # default scope
#   bash scripts/check-mutations.sh go ./internal/db  # explicit
#   bash scripts/check-mutations.sh --dry-run         # see what runs
#
# Mutation testing is *expensive* in CI (minutes per file
# mutated; thousands of mutations in a typical package).
# The framework rule: run on every PR against the
# touched package(s); weekly cron for the whole repo.
# Don't run *every commit*; the cost outweighs the
# marginal catch rate.
#
# Adopters: copy this template to `scripts/check-mutations.sh`
# in the target repo, uncomment the picker's `case` for the
# stack(s) you ship, and wire into a CI job that runs on
# `pull_request: paths:` filtered to the touched dirs + a
# weekly cron for the full repo.

set -euo pipefail

DRY_RUN=0
STACK=""
SCOPE=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<EOF
Usage: bash scripts/check-mutations.sh [--dry-run] [<stack> <scope>]

Stacks:
  go       go-mutesting
  node     stryker
  python   mutmut
  rust     cargo-mutants
  ruby     mutant

Mutation testing is expensive in CI. Run on touched-package
PR gates + weekly cron for the full repo. See
\`addenda/go-htmx.md\` §'Mutation testing' for the
worked Go example.

Examples:
  bash scripts/check-mutations.sh go ./internal/db
  bash scripts/check-mutations.sh --dry-run
EOF
      exit 0
      ;;
    -*) echo "Unknown flag: $arg" >&2; exit 2 ;;
    *)
      if [[ -z "$STACK" ]]; then
        STACK="$arg"
      elif [[ -z "$SCOPE" ]]; then
        SCOPE="$arg"
      else
        echo "Unexpected positional arg: $arg" >&2
        exit 2
      fi
      ;;
  esac
done

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "  [dry-run] $(printf '%q ' "$@")"
  else
    "$@"
  fi
}

# ---------- auto-detect stack --------------------------------------------
if [[ -z "$STACK" ]]; then
  if [[ -f "go.mod" ]]; then STACK="go"
  elif [[ -f "package.json" ]]; then STACK="node"
  elif [[ -f "pyproject.toml" || -f "requirements.txt" ]]; then STACK="python"
  elif [[ -f "Cargo.toml" ]]; then STACK="rust"
  elif [[ -f "Gemfile" ]]; then STACK="ruby"
  else
    echo "error: no stack auto-detected; pass <stack> explicitly" >&2
    exit 2
  fi
  echo "auto-detected stack: $STACK"
fi

# ---------- picker --------------------------------------------------------
case "$STACK" in
  go)
    : "${SCOPE:=./...}"
    # go-mutesting reads `./...` and applies each mutator to
    # each function. The default mutator set covers ~10
    # operator-level flips; project-level mutators cover
    # domain-specific swaps. Config lives in
    # `.mutesting.yaml`.
    #
    # Per-package invocation so a PR can mutate only the
    # touched packages:
    run go-mutesting "$SCOPE" --config .mutesting.yaml
    ;;
  node)
    # Stryker reads `stryker.conf.json`. The full-scope
    # mutation is `npm run mutate`; per-PR can scope via
    # --mutate patterns.
    run npx stryker run
    ;;
  python)
    # mutmut reads `setup.cfg` / `mutmut.ini` for the
    # `paths = src/...` config. First run applies all
    # mutations; subsequent runs apply only new ones
    # (incremental).
    run python -m mutmut run --paths-to-mutate "$SCOPE"
    ;;
  rust)
    # cargo-mutants reads `Cargo.toml` automatically. Output
    # is a JSON summary of which mutants survived.
    : "${SCOPE:=.}"
    run cargo mutants --package "$SCOPE"
    ;;
  ruby)
    # mutant reads `Gemfile` automatically. Per-PR scope via
    # `--mutation-coverage` config.
    run bundle exec mutant --use rspec
    ;;
  *)
    echo "error: unknown stack '$STACK' (supported: go node python rust ruby)" >&2
    exit 2
    ;;
esac
