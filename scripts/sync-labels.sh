#!/usr/bin/env bash
# sync-labels.sh — apply the agent-stack label taxonomy to a
# target repo via the `gh` CLI. Idempotent: re-running on an
# already-labelled repo only adds or updates; it never drops.
#
# Usage:
#   bash scripts/sync-labels.sh                  # apply to current dir's repo
#   bash scripts/sync-labels.sh --dry-run        # preview
#   bash scripts/sync-labels.sh --repo owner/repo

set -euo pipefail

# ---------- label spec -------------------------------------------------------
# Format: name|color|description
LABELS=(
  # Type
  "bug|d73a4a|Something isn't working"
  "enhancement|a2eeef|New feature or request"
  "documentation|0075ca|Improvements or additions to documentation"

  # Status
  "needs-triage|fbca04|Maintainer needs to evaluate this issue"
  "needs-info|cccccc|Waiting on reporter for more information"
  "ready-for-agent|0e8a16|Fully specified, ready for an AFK agent"
  "ready-for-human|1d76db|Requires human implementation"
  "wontfix|ffffff|Will not be actioned"

  # Priority
  "priority:high|b60205|Known regression, lost-data bug, or active user blocker"
  "priority:medium|fbca04|Default. Bugs with workarounds, features on the backlog"
  "priority:low|cccccc|Speculative, nice-to-have, or research-only"

  # Cohort (default set; extend per-repo)
  "audit-fallout|d4c5f9|Issue discovered by a full audit sweep"

  # Meta
  "blocked|b60205|Held by another issue"
  "deferred|cccccc|Held until a future trigger fires"
  "duplicate|cccccc|This issue already exists"
  "good first issue|7057ff|Small enough for a newcomer to pick up"
  "help wanted|008672|Maintainer is actively looking for someone to pick this up"
  "invalid|e4e669|Not a real issue"
  "question|d876e3|Reporter is asking, not filing"
)

# ---------- flag parsing ----------------------------------------------------
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
    *) echo "Unknown flag: $arg" >&2; exit 2 ;;
  esac
done

gh_args=()
if [[ -n "$REPO" ]]; then
  gh_args+=("--repo" "$REPO")
fi

# ---------- check gh is available ------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not found in PATH" >&2
  exit 1
fi

# ---------- apply labels ----------------------------------------------------
created=0
updated=0
unchanged=0

for entry in "${LABELS[@]}"; do
  IFS='|' read -r name color description <<<"$entry"

  # Check if the label already exists.
  existing=$(gh label list "${gh_args[@]}" --json name,color,description \
    --jq ".[] | select(.name == \"$name\") | \"\(.color)|\(.description)\"" \
    2>/dev/null || true)

  if [[ -z "$existing" ]]; then
    if [[ "$DRY_RUN" == "1" ]]; then
      printf '  [would create] %s (%s) — %s\n' "$name" "$color" "$description"
    else
      gh label create "$name" --color "$color" --description "$description" "${gh_args[@]}" >/dev/null
      printf '  [created] %s\n' "$name"
    fi
    created=$((created + 1))
  else
    IFS='|' read -r ex_color ex_desc <<<"$existing"
    if [[ "$ex_color" == "$color" && "$ex_desc" == "$description" ]]; then
      unchanged=$((unchanged + 1))
    else
      if [[ "$DRY_RUN" == "1" ]]; then
        printf '  [would update] %s\n' "$name"
      else
        gh label edit "$name" --color "$color" --description "$description" "${gh_args[@]}" >/dev/null
        printf '  [updated] %s\n' "$name"
      fi
      updated=$((updated + 1))
    fi
  fi
done

echo
echo "Summary: $created created, $updated updated, $unchanged unchanged"
[[ "$DRY_RUN" == "1" ]] && echo "(dry run — no changes applied)"