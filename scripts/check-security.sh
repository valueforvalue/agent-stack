#!/usr/bin/env bash
# check-security.sh — template for per-adopter security-scan automation.
#
# Tip #71 (Apply Security Patches Quickly) is operationalized at
# framework level by this script. Each adopting repo extends it
# with the stack-specific scanner invocation:
#
#   Go:     govulncheck ./...
#   Node:   npm audit --audit-level=high
#   Python: pip-audit --strict
#   Rust:   cargo audit
#   Ruby:   bundle-audit check --update
#
# The picker rule: each stack ships one scanner that's "official"
# (maintained by the language's foundation) or "ubiquitous"
# (adopted by the vast majority of CI for that stack). Don't
# choose any other — the long tail of scanners is unevenly
# maintained and you'll carry the upgrade cost forever.
#
# Usage:
#   bash scripts/check-security.sh                       # default picker
#   bash scripts/check-security.sh go ./internal/...     # explicit stack + scope
#   bash scripts/check-security.sh --dry-run             # see what would run
#
# The script is intentionally short; per-stack decisions
# belong in `addenda/<stack>.md` 'Security' sections, NOT
# in this template. The template's job is to enforce:
#   - One scanner per stack (no copy-paste of multiple)
#   - A non-zero exit code when the scanner flags something
#   - A reproducible invocation (no editor-style env state)
#   - Output that CI can ingest (prefer JSON where the
#     scanner offers it)
#
# Adopters: copy this template to `scripts/check-security.sh`
# in the target repo, uncomment the picker's `case` for the
# stack(s) you ship, and wire the script into a CI job that
# runs on every PR + weekly.

set -euo pipefail

# ---------- flag parsing ----------------------------------------------------
DRY_RUN=0
STACK=""
SCOPE=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help)
      cat <<EOF
Usage: bash scripts/check-security.sh [--dry-run] [<stack> <scope>]

Stacks:
  go       govulncheck
  node     npm audit
  python   pip-audit
  rust     cargo audit
  ruby     bundle-audit

Examples:
  bash scripts/check-security.sh go ./internal/...
  bash scripts/check-security.sh node
  bash scripts/check-security.sh --dry-run
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

# ---------- auto-detect stack if not passed --------------------------------
if [[ -z "$STACK" ]]; then
  if [[ -f "go.mod" ]]; then
    STACK="go"
  elif [[ -f "package.json" ]]; then
    STACK="node"
  elif [[ -f "pyproject.toml" || -f "requirements.txt" || -f "setup.py" ]]; then
    STACK="python"
  elif [[ -f "Cargo.toml" ]]; then
    STACK="rust"
  elif [[ -f "Gemfile" ]]; then
    STACK="ruby"
  else
    echo "error: no stack auto-detected; pass <stack> explicitly" >&2
    exit 2
  fi
  echo "auto-detected stack: $STACK"
fi

# ---------- picker per stack ------------------------------------------------
# Reference: https://github.com/govulncheck (Go), https://docs.npmjs.com/cli/commands/npm-audit
# (Node), https://pypi.org/project/pip-audit/ (Python), https://github.com/rustsec/rustsec
# (Rust), https://github.com/rubysec/bundler-audit (Ruby).
case "$STACK" in
  go)
    # govulncheck is the official Go scanner (maintained by the
    # Go security team). `go install` once per dev box:
    #   go install golang.org/x/vuln/cmd/govulncheck@latest
    # JSON mode is the CI-ingestible output.
    : "${SCOPE:=./...}"
    run govulncheck -mode=json "$SCOPE"
    ;;
  node)
    # npm audit is bundled with npm; no install needed.
    # --audit-level=high = only block on high/critical (the
    # medium/low noise overwhelms a PR gate; weekly cron
    # picks them up separately).
    run npm audit --audit-level=high --json
    ;;
  python)
    # pip-audit is the PyPA-endorsed scanner. `pip install`
    # once per env:
    #   pip install pip-audit
    # --strict = non-zero exit on any finding.
    : "${SCOPE:=.}"
    run python -m pip_audit --strict "$SCOPE"
    ;;
  rust)
    # cargo audit is the RustSec-team scanner. `cargo install`:
    #   cargo install cargo-audit --locked
    run cargo audit --json
    ;;
  ruby)
    # bundle-audit is the Ruby community standard. `gem install`:
    #   gem install bundler-audit
    run bundle-audit check --update
    ;;
  *)
    echo "error: unknown stack '$STACK' (supported: go node python rust ruby)" >&2
    exit 2
    ;;
esac
