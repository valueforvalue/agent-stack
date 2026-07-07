#!/usr/bin/env bash
# backfill-labels.sh — apply Area + Priority labels to existing
# open issues by parsing titles + bodies. Idempotent: re-running
# on an already-labelled issue set is a no-op for matching labels.
#
# Strategy:
#   1. List open issues.
#   2. For each issue, scan title + body for keyword hits.
#   3. Apply the highest-confidence Area + Priority label(s).
#
# The keyword map is intentionally conservative — when in doubt,
# skip. A maintainer can apply labels manually for the rest.
#
# Usage:
#   bash scripts/backfill-labels.sh                 # current dir's repo
#   bash scripts/backfill-labels.sh --dry-run       # preview
#   bash scripts/backfill-labels.sh --repo owner/repo

set -euo pipefail

DRY_RUN=0
REPO=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --repo=*) REPO="${arg#--repo=}" ;;
    --repo) shift; REPO="$1" ;;
    -h|--help)
      echo "Usage: $0 [--dry-run] [--repo owner/repo]"
      exit 0
      ;;
  esac
done

gh_args=()
[[ -n "$REPO" ]] && gh_args+=("--repo" "$REPO")

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not found in PATH" >&2
  exit 1
fi

# ---------- keyword → area --------------------------------------------------
# Format: area|regex (case-insensitive)
AREA_KEYWORDS=(
  "area:backend|handler|service|middleware|internal/|endpoint|api"
  "area:frontend|frontend/|app\.js|app\.css|stylesheet|component|jsx|\.tsx"
  "area:cli|subcommand|cli-|--flag"
  "area:db|migration|schema|sqlite|sql|FTS5|table|column"
  "area:export|export|pdf|jpg|json|csv|ical"
  "area:import|import|ddbak|ddshare|restore"
  "area:docs|README|CHANGELOG|ADR|glossary|CONTEXT\.md|agents/"
  "area:build|build|ci|workflow|Makefile|compile|package"
)

# ---------- keyword → priority ----------------------------------------------
PRIORITY_KEYWORDS_HIGH=(
  "crash|panic|OS\.Exit|data loss|data-loss|lost data|regression|blocker"
  "fatal|SIGSEGV|nil pointer|nil-pointer|access denied"
)

# ---------- fetch issues ----------------------------------------------------
mapfile -t ISSUES < <(
  gh issue list --state open --limit 500 --json number,title,body,labels \
    "${gh_args[@]}" \
    --jq '.[] | "\(.number)|\(.title)|\(.body)"'
)

if [[ ${#ISSUES[@]} -eq 0 ]]; then
  echo "No open issues found."
  exit 0
fi

echo "Scanning ${#ISSUES[@]} open issues..."

applied=0
skipped=0

for line in "${ISSUES[@]}"; do
  IFS='|' read -r num title body <<<"$line"

  # Concatenate searchable text
  text="$title $body"

  # Determine candidate area
  candidate_area=""
  for entry in "${AREA_KEYWORDS[@]}"; do
    IFS='|' read -r area regex <<<"$entry"
    if echo "$text" | grep -iE -q "$regex"; then
      candidate_area="$area"
      break   # first match wins
    fi
  done

  # Determine candidate priority
  candidate_priority=""
  for regex in "${PRIORITY_KEYWORDS_HIGH[@]}"; do
    if echo "$text" | grep -iE -q "$regex"; then
      candidate_priority="priority:high"
      break
    fi
  done

  # Check existing labels to avoid re-applying
  existing_labels=$(gh issue view "$num" --json labels "${gh_args[@]}" \
    --jq '.labels[].name')

  to_apply=()
  if [[ -n "$candidate_area" ]] && ! grep -qx "$candidate_area" <<<"$existing_labels"; then
    to_apply+=("$candidate_area")
  fi
  if [[ -n "$candidate_priority" ]] && ! grep -qx "$candidate_priority" <<<"$existing_labels"; then
    to_apply+=("$candidate_priority")
  fi

  if [[ ${#to_apply[@]} -eq 0 ]]; then
    skipped=$((skipped + 1))
    continue
  fi

  add_args=()
  for lbl in "${to_apply[@]}"; do
    add_args+=("--add-label" "$lbl")
  done

  if [[ "$DRY_RUN" == "1" ]]; then
    printf '  [#%s] %s — would add: %s\n' "$num" "$title" "${to_apply[*]}"
  else
    gh issue edit "$num" "${add_args[@]}" "${gh_args[@]}" >/dev/null
    printf '  [#%s] added: %s\n' "$num" "${to_apply[*]}"
  fi
  applied=$((applied + 1))
done

echo
echo "Summary: $applied updated, $skipped skipped (already labelled or no keyword match)"
[[ "$DRY_RUN" == "1" ]] && echo "(dry run — no changes applied)"