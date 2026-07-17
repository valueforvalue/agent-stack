#!/usr/bin/env bash
# dedupe-skills.sh - validate bundled skill packages and compare them with
# installed skill catalogs. Apply mode stays advisory to avoid deleting user
# files.

set -euo pipefail

DRY_RUN=1
APPLY=0
STRICT=0
PREFER="upstream"
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --apply) APPLY=1; DRY_RUN=0 ;;
    --strict) STRICT=1 ;;
    --prefer=*) PREFER="${arg#--prefer=}" ;;
    -h|--help)
      cat <<EOF
Usage: $0 [--dry-run | --apply] [--strict] [--prefer=framework|upstream|none]

Default policy: keep upstream unless framework-bundled is newer.
--strict exits 1 when overlap or checksum drift is found.
EOF
      exit 0
      ;;
    *) echo "error: unknown flag $arg" >&2; exit 2 ;;
  esac
done

case "$PREFER" in
  framework|upstream|none) ;;
  *) echo "error: --prefer must be framework, upstream, or none" >&2; exit 2 ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$FRAMEWORK_ROOT/skills/SKILLS.md"

if [[ ! -f "$MANIFEST" ]]; then
  echo "error: manifest not found at $MANIFEST" >&2
  exit 1
fi

PYTHON=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
fi

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

package_checksum() {
  local package_dir="$1"
  if [[ -z "$PYTHON" ]]; then
    return 2
  fi
  "$PYTHON" - "$package_dir" <<'PY'
from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])
ignored_names = {".agent-stack-owned", ".DS_Store"}
hash_value = hashlib.sha256()
files = sorted(
    path for path in root.rglob("*")
    if path.is_file()
    and "__pycache__" not in path.parts
    and path.name not in ignored_names
    and path.suffix != ".pyc"
)
for path in files:
    relative = path.relative_to(root).as_posix().encode()
    data = path.read_bytes().replace(b"\r\n", b"\n")
    hash_value.update(relative + b"\0" + data + b"\0")
print(hash_value.hexdigest())
PY
}

skill_version() {
  local skill_md="$1"
  local version
  version=$(awk -F: '/^[[:space:]]*version:/ {print $2; exit}' "$skill_md" | tr -d "\"'[:space:]")
  printf '%s' "${version:-unknown}"
}

version_gt() {
  local left="$1"
  local right="$2"
  [[ "$left" =~ ^[0-9]+([.][0-9]+){1,2}$ ]] || return 1
  [[ "$right" =~ ^[0-9]+([.][0-9]+){1,2}$ ]] || return 1
  [[ "$left" != "$right" ]] || return 1
  [[ "$(printf '%s\n%s\n' "$left" "$right" | sort -V | tail -1)" == "$left" ]]
}

# Later locations override earlier ones, matching prior script behavior.
declare -A INSTALLED=()
declare -A INSTALLED_VERSION=()
for dir in \
  "$HOME/.pi/agent/skills" \
  "$HOME/.agents/skills" \
  "./.pi/skills" \
  "./.agents/skills"; do
  if [[ -d "$dir" ]]; then
    while IFS= read -r -d '' skill_md; do
      name=$(basename "$(dirname "$skill_md")")
      INSTALLED["$name"]="$skill_md"
      INSTALLED_VERSION["$name"]="$(skill_version "$skill_md")"
    done < <(find "$dir" -mindepth 2 -maxdepth 2 -type f -name SKILL.md -print0)
  fi
done

declare -a BUNDLED_NAMES=()
declare -A BUNDLED_SOURCE
declare -A BUNDLED_VERSION
declare -A BUNDLED_CHECKSUM
declare -A BUNDLED_SUPERSEDES

in_table=0
while IFS= read -r line; do
  if [[ "$line" == *"| Name | Source | Version | Checksum | Supersedes | Load when |"* ]]; then
    in_table=1
    continue
  fi
  if [[ "$in_table" == "1" && "$line" == "|"*"|---"* ]]; then
    continue
  fi
  if [[ "$in_table" == "1" && "$line" != "|"* ]]; then
    in_table=0
    continue
  fi
  if [[ "$in_table" == "1" ]]; then
    cleaned=$(echo "$line" | sed 's/`//g')
    IFS='|' read -r _ name source version checksum supersedes loadwhen _ <<<"$cleaned"
    name="$(trim "$name")"
    [[ -n "$name" && "$name" != "---" ]] || continue
    BUNDLED_NAMES+=("$name")
    BUNDLED_SOURCE["$name"]="$(trim "$source")"
    BUNDLED_VERSION["$name"]="$(trim "$version")"
    BUNDLED_CHECKSUM["$name"]="$(trim "$checksum")"
    BUNDLED_SUPERSEDES["$name"]="$(trim "$supersedes")"
  fi
done < "$MANIFEST"

if [[ ${#BUNDLED_NAMES[@]} -eq 0 ]]; then
  echo "error: no manifest rows parsed from $MANIFEST" >&2
  exit 1
fi

echo "=== Bundled package validation ==="
checksum_errors=0
for name in "${BUNDLED_NAMES[@]}"; do
  expected="${BUNDLED_CHECKSUM[$name]}"
  package_dir="$FRAMEWORK_ROOT/skills/$name"
  if [[ "$expected" == "-" ]]; then
    if [[ -f "$package_dir/SKILL.md" ]]; then
      echo "  $name: UNPINNED (body exists but checksum is '-')"
      checksum_errors=$((checksum_errors + 1))
    else
      echo "  $name: planned (body not shipped)"
    fi
    continue
  fi
  if [[ ! -f "$package_dir/SKILL.md" ]]; then
    echo "  $name: MISSING package for checksum $expected"
    checksum_errors=$((checksum_errors + 1))
    continue
  fi
  if ! actual=$(package_checksum "$package_dir"); then
    echo "  $name: ERROR (Python required for package checksum)"
    checksum_errors=$((checksum_errors + 1))
  elif [[ "$actual" == "$expected" ]]; then
    echo "  $name: OK ($actual)"
  else
    echo "  $name: CHECKSUM DRIFT"
    echo "    expected: $expected"
    echo "    actual:   $actual"
    checksum_errors=$((checksum_errors + 1))
  fi
done

echo
echo "=== Installed skills (catalog) ==="
if [[ ${#INSTALLED[@]} -eq 0 ]]; then
  echo "  (none found)"
else
  for name in "${!INSTALLED[@]}"; do
    echo "  $name (v${INSTALLED_VERSION[$name]}) → ${INSTALLED[$name]}"
  done | sort
fi

echo
echo "=== Overlap and supersedes report ==="
overlap_count=0
declare -a OVERLAP_ROWS=()
for name in "${BUNDLED_NAMES[@]}"; do
  declare -A candidates=()
  supersedes="${BUNDLED_SUPERSEDES[$name]}"
  if [[ "$supersedes" != "(none yet)" && "$supersedes" != "(none)" && -n "$supersedes" ]]; then
    IFS=',' read -ra aliases <<<"$supersedes"
    for alias in "${aliases[@]}"; do
      alias="$(trim "$alias")"
      alias="${alias#upstream:}"
      [[ -n "$alias" ]] || continue
      if [[ "$alias" != "$name" ]]; then
        candidates["$alias"]="supersedes"
      fi
    done
  fi
  candidates["$name"]="direct"

  for installed_name in "${!candidates[@]}"; do
    [[ -n "${INSTALLED[$installed_name]:-}" ]] || continue
    relation="${candidates[$installed_name]}"
    framework_version="${BUNDLED_VERSION[$name]}"
    installed_version="${INSTALLED_VERSION[$installed_name]}"
    recommendation="keep-both"
    reason="version unavailable"

    if [[ "$PREFER" == "framework" ]]; then
      recommendation="keep-framework"
      reason="explicit policy"
    elif [[ "$PREFER" == "none" ]]; then
      recommendation="keep-upstream"
      reason="explicit policy"
    elif version_gt "$framework_version" "$installed_version"; then
      recommendation="keep-framework"
      reason="framework v$framework_version is newer than installed v$installed_version"
    elif [[ "$installed_version" != "unknown" ]]; then
      recommendation="keep-upstream"
      reason="installed v$installed_version is not older than framework v$framework_version"
    fi

    OVERLAP_ROWS+=("  $name ← $installed_name [$relation]: $recommendation ($reason)")
    overlap_count=$((overlap_count + 1))
  done
  unset candidates
done

if [[ $overlap_count -eq 0 ]]; then
  echo "  (no direct or superseded-name overlaps)"
else
  printf '%s\n' "${OVERLAP_ROWS[@]}"
fi

if [[ "$APPLY" == "1" ]]; then
  echo
  echo "=== Applying policy ==="
  if [[ $overlap_count -eq 0 ]]; then
    echo "  (nothing to resolve)"
  else
    printf '%s\n' "${OVERLAP_ROWS[@]}" | sed 's/^/  [advisory] /'
    echo "  Manual removal required; script never deletes user skill packages."
  fi
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo
  echo "(dry run - no changes applied)"
fi

if [[ $checksum_errors -gt 0 ]]; then
  echo "error: $checksum_errors bundled package checksum error(s)" >&2
  exit 1
fi
if [[ "$STRICT" == "1" && $overlap_count -gt 0 ]]; then
  echo "error: $overlap_count skill overlap(s) found in strict mode" >&2
  exit 1
fi
