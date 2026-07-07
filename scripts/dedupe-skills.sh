#!/usr/bin/env bash
# dedupe-skills.sh — compare the agent-stack bundled skills
# against the user's installed skill catalog, report overlap,
# and (with --apply) prune according to the preferred policy.
#
# The default policy is "keep upstream unless framework-bundled
# is newer", per the resolved Q-E from PLAN.md. Override with:
#   --prefer=framework    # always prefer bundled
#   --prefer=upstream     # always prefer upstream (default)
#   --prefer=none         # drop framework-bundled (let upstream win)
#
# Usage:
#   bash scripts/dedupe-skills.sh --dry-run
#   bash scripts/dedupe-skills.sh --apply --prefer=upstream

set -euo pipefail

# ---------- flag parsing ----------------------------------------------------
DRY_RUN=1
APPLY=0
PREFER="upstream"
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --apply) APPLY=1; DRY_RUN=0 ;;
    --prefer=*) PREFER="${arg#--prefer=}" ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--dry-run | --apply] [--prefer=framework|upstream|none]

Default policy: keep upstream unless framework-bundled is newer.
EOF
      exit 0
      ;;
  esac
done

case "$PREFER" in
  framework|upstream|none) ;;
  *) echo "error: --prefer must be framework, upstream, or none" >&2; exit 2 ;;
esac

# ---------- locate manifest -------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$SCRIPT_DIR/../skills/SKILLS.md"

if [[ ! -f "$MANIFEST" ]]; then
  echo "error: manifest not found at $MANIFEST" >&2
  exit 1
fi

# ---------- locate installed skill dirs -------------------------------------
# Walk known skill locations and collect (name → path) entries.
declare -A INSTALLED
for dir in \
  "$HOME/.pi/agent/skills" \
  "$HOME/.agents/skills" \
  "./.pi/skills" \
  "./.agents/skills"; do
  if [[ -d "$dir" ]]; then
    while IFS= read -r skill_md; do
      name=$(basename "$(dirname "$skill_md")")
      INSTALLED["$name"]="$skill_md"
    done < <(find "$dir" -mindepth 2 -maxdepth 2 -type f -name SKILL.md)
  fi
done

# ---------- parse manifest --------------------------------------------------
# This is a lightweight parser — it doesn't understand every
# markdown construct, but the manifest is small and structured.
# For each entry we extract name + source + version + supersedes.
declare -a BUNDLED_NAMES=()
declare -A BUNDLED_VERSION
declare -A BUNDLED_SUPERSEDES

in_table=0
while IFS= read -r line; do
  # Detect the start of the v0.1.0 manifest table
  if [[ "$line" == *"| Name | Source |"* ]]; then
    in_table=1
    continue
  fi
  # Skip the table header separator
  if [[ "$in_table" == "1" && "$line" == "|"*"| ---"* ]]; then
    continue
  fi
  # End of table on first non-pipe line
  if [[ "$in_table" == "1" && "$line" != "|"* ]]; then
    in_table=0
    continue
  fi
  if [[ "$in_table" == "1" ]]; then
    # Parse "| `name` | source | version | supersedes | load-when |"
    # Strip backticks, then awk-split by '|'.
    cleaned=$(echo "$line" | sed 's/`//g')
    fields=$(echo "$cleaned" | awk -F'|' '{print $2"|"$3"|"$4"|"$5"|"$6}' | sed 's/^ *//;s/ *$//')
    IFS='|' read -r name source version supersedes loadwhen <<<"$fields"
    # Trim all fields to remove leading/trailing whitespace
    name="${name#"${name%%[![:space:]]*}"}"; name="${name%"${name##*[![:space:]]}"}"
    source="${source#"${source%%[![:space:]]*}"}"; source="${source%"${source##*[![:space:]]}"}"
    version="${version#"${version%%[![:space:]]*}"}"; version="${version%"${version##*[![:space:]]}"}"
    supersedes="${supersedes#"${supersedes%%[![:space:]]*}"}"; supersedes="${supersedes%"${supersedes##*[![:space:]]}"}"
    # Skip separator row (all fields are dashes)
    if [[ "$name" == "---" || -z "$name" ]]; then
      continue
    fi
    BUNDLED_NAMES+=("$name")
    BUNDLED_VERSION["$name"]="$version"
    BUNDLED_SUPERSEDES["$name"]="$supersedes"
  fi
done < "$MANIFEST"

# ---------- report overlap --------------------------------------------------
echo "=== Bundled skills (manifest) ==="
for name in "${BUNDLED_NAMES[@]}"; do
  echo "  $name (v${BUNDLED_VERSION[$name]})"
done
echo

echo "=== Installed skills (catalog) ==="
if [[ ${#INSTALLED[@]} -eq 0 ]]; then
  echo "  (none found in \$HOME/.pi/agent/skills, \$HOME/.agents/skills, ./.pi/skills, ./.agents/skills)"
else
  for name in "${!INSTALLED[@]}"; do
    echo "  $name → ${INSTALLED[$name]}"
  done
fi
echo

echo "=== Overlap report ==="
overlap_count=0
for name in "${BUNDLED_NAMES[@]}"; do
  if [[ -n "${INSTALLED[$name]:-}" ]]; then
    echo "  $name: BOTH bundled and installed"
    overlap_count=$((overlap_count + 1))
  fi
done
if [[ $overlap_count -eq 0 ]]; then
  echo "  (no direct name overlaps)"
fi
echo

echo "=== Recommendation (policy: prefer=$PREFER) ==="
case "$PREFER" in
  upstream)
    echo "  Default: keep upstream unless framework-bundled is newer."
    echo "  For each overlap, the bundled skill wins only if its version is higher"
    echo "  than the installed version (compare with: cat installed/SKILL.md | head -5)."
    ;;
  framework)
    echo "  Default: keep framework-bundled over upstream."
    echo "  For each overlap, the bundled skill always wins."
    ;;
  none)
    echo "  Default: drop framework-bundled; let upstream win."
    echo "  For each overlap, the installed skill always wins."
    ;;
esac

if [[ "$APPLY" == "1" ]]; then
  echo
  echo "=== Applying policy ==="
  for name in "${BUNDLED_NAMES[@]}"; do
    if [[ -n "${INSTALLED[$name]:-}" ]]; then
      case "$PREFER" in
        upstream)
          echo "  [would keep upstream] $name (manual version comparison required)"
          ;;
        framework|none)
          echo "  [would drop one of the two] $name (run manually: rm -rf the loser)"
          ;;
      esac
    fi
  done
  echo
  echo "(Apply mode is intentionally advisory — manual removal prevents accidents.)"
fi

[[ "$DRY_RUN" == "1" ]] && echo && echo "(dry run — no changes applied)"