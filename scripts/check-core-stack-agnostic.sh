#!/usr/bin/env bash
# check-core-stack-agnostic.sh — verify that `core/` is stack-agnostic.
#
# The core/ directory carries the rules every adopting repo loads
# at session start. Stack-specific patterns belong in addenda/.
# If a stack-specific symbol leaks into core/, the framework has
# broken its own contract — adopters on other stacks would inherit
# patterns that don't apply to them.
#
# This script greps core/ for vendor-specific tokens (header names,
# binary names, file extensions, specific issue trackers, etc.)
# and exits non-zero on any hit. Generic words like "template"
# or framework names appearing in *meta* rules (e.g. README's
# "patterns that name HTMX, React, Django...") are permitted.
#
# Usage:
#   bash scripts/check-core-stack-agnostic.sh
#   bash scripts/check-core-stack-agnostic.sh --allow=go-htmx

set -euo pipefail

# ---------- flag parsing ----------------------------------------------------
ALLOW=""
for arg in "$@"; do
  case "$arg" in
    --allow=*) ALLOW="${arg#--allow=}" ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--allow=go-htmx|react|python|...]

Default: strict — any vendor-specific token in core/ fails.
--allow=<addendum>: permit tokens belonging to that addendum
                    (use during addendum development).
EOF
      exit 0
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORE_DIR="$FRAMEWORK_ROOT/core"

if [[ ! -d "$CORE_DIR" ]]; then
  echo "error: core/ not found at $CORE_DIR" >&2
  exit 2
fi

# ---------- forbidden tokens -------------------------------------------------
# Vendor-specific / app-specific / runtime-specific tokens.
# These are exact strings; greps are literal (-F).
# Generic words (template, route, view, JSX, React as a *rule*
# example) are NOT listed here — only specific tokens that
# betray provenance or stack lock-in.
case "$ALLOW" in
  "")
    FORBIDDEN=(
      # Specific binary names
      "Wails"
      "WebView2"
      "Chrome_WidgetWin"
      # Specific header / directive names
      "X-DixieData-Redirect"
      "X-DixieData-Toast"
      # Specific dispatcher / attribute names (NOT the bare 'hx-' prefix
      # since 'hx-get' is cited in core/code-changes.md as a generic
      # example of an attribute-name convention)
      "dispatchDixieDataForm"
      # Source-repo / app-specific identifiers
      "DixieData"
      "DixieData.exe"
      ".ddbak"
      # Specific HTML attribute strings cited as if they were
      # the canonical example (NOT generic attribute names)
      "data-dixie-submit"
    )
    ;;
  *)
    echo "(allowing tokens from addendum: $ALLOW)"
    FORBIDDEN=()
    ;;
esac

# ---------- scan ------------------------------------------------------------
hits=0
for term in "${FORBIDDEN[@]}"; do
  if matches=$(grep -rIn -F -- "$term" "$CORE_DIR" 2>/dev/null); then
    if [[ -n "$matches" ]]; then
      echo "FORBIDDEN TOKEN in core/: '$term'"
      echo "$matches" | sed 's/^/  /'
      echo
      hits=$((hits + 1))
    fi
  fi
done

if [[ $hits -gt 0 ]]; then
  echo "FAIL: $hits forbidden token(s) found in core/."
  echo "  Stack-specific patterns belong in addenda/<stack>.md."
  echo "  Source-repo / app-specific tokens belong nowhere in this repo."
  exit 1
fi

echo "OK: core/ is stack-agnostic."
exit 0