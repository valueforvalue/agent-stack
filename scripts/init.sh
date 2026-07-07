#!/usr/bin/env bash
# init.sh — bootstrap a target repo with the agent-stack
# framework. Interactive question flow, idempotent.
#
# Usage:
#   bash scripts/init.sh /path/to/target/repo
#   bash scripts/init.sh /path/to/target/repo --dry-run
#   bash scripts/init.sh /path/to/target/repo --uninit
#
# The script asks 6 questions:
#   1. Stack (drives which addendum is included)
#   2. Branch model (single-branch vs three-branch)
#   3. Include issues scaffolding (GH labels + templates)
#   4. Which addendum(s) to include
#   5. Which bundled skills to include (copies bodies to target)
#   6. README tone (terse vs polished)
#
# After the questions, the script:
#   - Copies the framework's `core/` to `target/docs/agents/`
#   - Copies selected `addenda/*.md` to `target/docs/agents/addenda/`
#   - Optionally copies `issues/` to `target/docs/agents/issues/`
#   - Optionally copies `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`
#   - Optionally copies selected bundled skill bodies to `target/.pi/skills/` (or `.agents/skills/`)
#   - Writes `target/FRAMEWORK_BOOTSTRAP.md` with a session-start checklist
#   - Optionally appends to `target/AGENTS.md`, `target/CONTEXT.md`, `target/CHANGELOG.md`
#
# Idempotent: re-running only adds what's missing.

set -euo pipefail

# ---------- locate script + framework root ---------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------- flag parsing ----------------------------------------------------
DRY_RUN=0
UNINIT=0
TARGET=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --uninit) UNINIT=1 ;;
    -h|--help)
      cat <<EOF
Usage: $0 <target-repo-path> [--dry-run] [--uninit]

  --dry-run   Preview the bootstrap without making changes
  --uninit    Reverse a bootstrap (remove framework files from target)
EOF
      exit 0
      ;;
    -*) echo "Unknown flag: $arg" >&2; exit 2 ;;
    *) TARGET="$arg" ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "error: target repo path required" >&2
  echo "Usage: $0 <target-repo-path>" >&2
  exit 2
fi

# ---------- helper: ask a question -----------------------------------------
ask() {
  local prompt="$1"
  local default="$2"
  local answer
  if [[ -t 0 ]]; then
    # TTY: read from stdin
    read -r -p "$prompt [$default]: " answer || answer=""
    echo "${answer:-$default}"
  else
    # Non-TTY: use the default
    echo "$default"
  fi
}

ask_yn() {
  local prompt="$1"
  local default="$2"
  local answer
  if [[ -t 0 ]]; then
    read -r -p "$prompt [y/n, default $default]: " answer || answer=""
    case "${answer:-$default}" in
      y|Y|yes|YES) echo "yes" ;;
      *) echo "no" ;;
    esac
  else
    echo "$default"
  fi
}

# ---------- helper: copy file with idempotency check -----------------------
copy_if_missing() {
  local src="$1"
  local dst="$2"
  if [[ -f "$dst" ]]; then
    echo "  [skip] $dst (already exists)"
    return 0   # 0 = no-op (file exists); callers don't need to gate
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [would copy] $src → $dst"
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  [copied] $dst"
  fi
  return 0
}

copy_dir_if_missing() {
  local src="$1"
  local dst="$2"
  if [[ -d "$dst" ]]; then
    echo "  [skip] $dst (already exists)"
    return 0
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [would copy dir] $src → $dst"
  else
    mkdir -p "$dst"
    cp -r "$src"/. "$dst"/
    echo "  [copied dir] $dst"
  fi
  return 0
}

# ---------- verify target --------------------------------------------------
if [[ ! -d "$TARGET" ]]; then
  echo "error: target directory $TARGET does not exist" >&2
  exit 2
fi
TARGET="$(cd "$TARGET" && pwd)"

# ---------- uninit flow ----------------------------------------------------
if [[ "$UNINIT" == "1" ]]; then
  echo "Removing agent-stack framework files from $TARGET..."
  for path in \
    "$TARGET/docs/agents" \
    "$TARGET/.github/ISSUE_TEMPLATE/bug.yml" \
    "$TARGET/.github/ISSUE_TEMPLATE/feature.yml" \
    "$TARGET/.github/PULL_REQUEST_TEMPLATE.md" \
    "$TARGET/FRAMEWORK_BOOTSTRAP.md"; do
    if [[ -e "$path" ]]; then
      if [[ "$DRY_RUN" == "1" ]]; then
        echo "  [would remove] $path"
      else
        rm -rf "$path"
        echo "  [removed] $path"
      fi
    fi
  done
  echo "Uninit complete."
  exit 0
fi

# ---------- intro ----------------------------------------------------------
cat <<EOF
agent-stack bootstrap
=====================

Target: $TARGET
Framework: $FRAMEWORK_ROOT

This script will bootstrap the target repo with the agent-stack
framework. The script is idempotent — re-running only adds what's
missing.

EOF

# ---------- 6 questions ----------------------------------------------------
echo "Question 1/6: Stack"
echo "  Drives which addendum is included by default."
echo "  Options: go-htmx, react, python, none"
Q1_STACK=$(ask "Stack" "go-htmx")

echo
echo "Question 2/6: Branch model"
echo "  Options: single-branch, three-branch"
Q2_BRANCH=$(ask "Branch model" "single-branch")

echo
echo "Question 3/6: Include issues scaffolding?"
echo "  Copies GitHub label spec, bug + feature templates, PR template,"
echo "  and triage workflow docs. Also runs sync-labels.sh if you say yes."
Q3_ISSUES=$(ask_yn "Include issues scaffolding" "yes")

echo
echo "Question 4/6: Which addenda to include?"
echo "  Comma-separated list. Available: go-htmx, react, python"
echo "  Default: stack from Q1 (or none if Q1 was none)"
Q4_DEFAULT="$Q1_STACK"
[[ "$Q4_DEFAULT" == "none" ]] && Q4_DEFAULT=""
Q4_ADDENDA=$(ask "Addenda" "$Q4_DEFAULT")

echo
echo "Question 5/6: Which bundled skills to include?"
echo "  Comma-separated list of skill names from SKILLS.md manifest."
echo "  Default: none. Slice 2 of PLAN.md ships skill bodies; until"
echo "  then, selecting a skill name will emit a warning and copy nothing."
echo "  See skills/SKILLS.md for the manifest and dedupe-skills.sh"
echo "  to detect overlap with your installed skill catalog."
Q5_SKILLS=$(ask "Bundled skills" "none")

echo
echo "Question 6/6: README tone for FRAMEWORK_BOOTSTRAP.md?"
echo "  Options: terse, polished"
Q6_TONE=$(ask "README tone" "terse")

echo
echo "Summary:"
echo "  Stack:        $Q1_STACK"
echo "  Branch:       $Q2_BRANCH"
echo "  Issues:       $Q3_ISSUES"
echo "  Addenda:      $Q4_ADDENDA"
echo "  Skills:       $Q5_SKILLS"
echo "  README tone:  $Q6_TONE"
echo
if [[ -t 0 ]]; then
  read -r -p "Proceed? [y/N]: " proceed || proceed="n"
  [[ "$proceed" =~ ^[yY] ]] || { echo "Aborted."; exit 1; }
fi

# ---------- 1. Copy core/ ---------------------------------------------------
echo
echo "[1/6] Copying core/ to $TARGET/docs/agents/"
copy_dir_if_missing "$FRAMEWORK_ROOT/core" "$TARGET/docs/agents"

# ---------- 2. Copy addenda -------------------------------------------------
echo
echo "[2/6] Copying selected addenda"
if [[ -n "$Q4_ADDENDA" && "$Q4_ADDENDA" != "none" ]]; then
  IFS=',' read -ra ADDENDA_LIST <<<"$Q4_ADDENDA"
  for addendum in "${ADDENDA_LIST[@]}"; do
    addendum="$(echo "$addendum" | sed 's/^ *//;s/ *$//')"
    src="$FRAMEWORK_ROOT/addenda/${addendum}.md"
    if [[ -f "$src" ]]; then
      copy_if_missing "$src" "$TARGET/docs/agents/addenda/${addendum}.md"
    else
      echo "  [warn] addendum $addendum not found at $src"
    fi
  done
else
  echo "  (no addenda selected)"
fi

# ---------- 3. Copy issues scaffolding --------------------------------------
echo
echo "[3/6] Issues scaffolding"
if [[ "$Q3_ISSUES" == "yes" ]]; then
  copy_if_missing "$FRAMEWORK_ROOT/issues/README.md" "$TARGET/docs/agents/issues/README.md"
  copy_if_missing "$FRAMEWORK_ROOT/issues/label-taxonomy.md" "$TARGET/docs/agents/issues/label-taxonomy.md"
  copy_if_missing "$FRAMEWORK_ROOT/issues/bug-template.md" "$TARGET/docs/agents/issues/bug-template.md"
  copy_if_missing "$FRAMEWORK_ROOT/issues/feature-template.md" "$TARGET/docs/agents/issues/feature-template.md"
  copy_if_missing "$FRAMEWORK_ROOT/issues/triage-workflow.md" "$TARGET/docs/agents/issues/triage-workflow.md"

  # GitHub-side templates
  copy_if_missing "$FRAMEWORK_ROOT/templates/.github/ISSUE_TEMPLATE/bug.yml" "$TARGET/.github/ISSUE_TEMPLATE/bug.yml"
  copy_if_missing "$FRAMEWORK_ROOT/templates/.github/ISSUE_TEMPLATE/feature.yml" "$TARGET/.github/ISSUE_TEMPLATE/feature.yml"
  copy_if_missing "$FRAMEWORK_ROOT/templates/.github/PULL_REQUEST_TEMPLATE.md" "$TARGET/.github/PULL_REQUEST_TEMPLATE.md"

  echo
  echo "  Tip: run scripts/sync-labels.sh to apply the label taxonomy."
fi

# ---------- 4. Copy boilerplate --------------------------------------------
echo
echo "[4/6] Boilerplate"
copy_if_missing "$FRAMEWORK_ROOT/templates/AGENTS.md.tmpl" "$TARGET/AGENTS.md"
copy_if_missing "$FRAMEWORK_ROOT/templates/CONTEXT.md.tmpl" "$TARGET/CONTEXT.md"
copy_if_missing "$FRAMEWORK_ROOT/templates/CHANGELOG.md.tmpl" "$TARGET/CHANGELOG.md"
copy_if_missing "$FRAMEWORK_ROOT/templates/CONTRIBUTING.md.tmpl" "$TARGET/CONTRIBUTING.md"

# ---------- 5. Copy bundled skills -----------------------------------------
echo
echo "[5/6] Bundled skills"
if [[ -n "$Q5_SKILLS" && "$Q5_SKILLS" != "none" ]]; then
  IFS=',' read -ra SKILLS_LIST <<<"$Q5_SKILLS"
  for skill in "${SKILLS_LIST[@]}"; do
    skill="$(echo "$skill" | sed 's/^ *//;s/ *$//')"
    src="$FRAMEWORK_ROOT/skills/${skill}/SKILL.md"
    if [[ -f "$src" ]]; then
      copy_if_missing "$src" "$TARGET/.pi/skills/${skill}/SKILL.md"
    else
      echo "  [warn] skill body $skill not shipped in v0.1.0 (Slice 2 of PLAN.md will add it)"
      echo "         manifest entry: skills/SKILLS.md ($skill)"
      echo "         skipping — re-run init.sh after upgrading to a Slice 2 release"
    fi
  done
else
  echo "  (no skills selected; you can copy them later)"
fi

# ---------- 6. Write FRAMEWORK_BOOTSTRAP.md --------------------------------
echo
echo "[6/6] Writing FRAMEWORK_BOOTSTRAP.md"
BOOTSTRAP_PATH="$TARGET/FRAMEWORK_BOOTSTRAP.md"
if [[ -f "$BOOTSTRAP_PATH" ]]; then
  echo "  [skip] $BOOTSTRAP_PATH (already exists)"
else
  cat > "$BOOTSTRAP_PATH" <<EOF
# Framework Bootstrap — Session-Start Checklist

This repo adopted the [agent-stack](https://github.com/<your-org>/agent-stack)
framework on $(date -u +%Y-%m-%d). Read these docs at session start.

## Tier-0 — always loaded

These cross-cut every task. Load them once.

- [ ] [\`docs/agents/session-protocol.md\`](docs/agents/session-protocol.md) — agent session rules
- [ ] [\`docs/agents/laws.md\`](docs/agents/laws.md) — non-negotiable laws
- [ ] [\`docs/agents/commit-and-branch.md\`](docs/agents/commit-and-branch.md) — commit shape + branch policy
- [ ] [\`docs/agents/docs-index-scheme.md\`](docs/agents/docs-index-scheme.md) — 3-tier progressive disclosure
- [ ] [\`docs/agents/glossary-discipline.md\`](docs/agents/glossary-discipline.md) — glossary maintenance
- [ ] [\`AGENTS.md\`](AGENTS.md) — project-specific session notes
- [ ] [\`CONTEXT.md\`](CONTEXT.md) — project glossary

## Tier-1 — load by task role

Load only the ones that match your task.

- [ ] [\`docs/agents/rpci.md\`](docs/agents/rpci.md) — non-trivial work (3+ files or design questions)
- [ ] [\`docs/agents/tdd.md\`](docs/agents/tdd.md) — any feature or bug fix
- [ ] [\`docs/agents/feature-protocol.md\`](docs/agents/feature-protocol.md) — adding a feature
- [ ] [\`docs/agents/code-changes.md\`](docs/agents/code-changes.md) — cross-layer change
- [ ] [\`docs/agents/bug-patterns.md\`](docs/agents/bug-patterns.md) — hunting a bug or reviewing a fix

## Tier-2 — on demand

Per addendum. Load only the one that matches the target stack.

- [ ] [\`docs/agents/addenda/${Q1_STACK}.md\`](docs/agents/addenda/${Q1_STACK}.md) — ${Q1_STACK} stack patterns

## Issue framework

$(if [[ "$Q3_ISSUES" == "yes" ]]; then
  echo "Adopted. See [\`docs/agents/issues/\`](docs/agents/issues/) for the templates and triage workflow."
else
  echo "Not adopted. Re-run \`bash scripts/init.sh\` and answer yes to Q3 to include it."
fi)

## Bundled skills

$(if [[ -n "$Q5_SKILLS" && "$Q5_SKILLS" != "none" ]]; then
  echo "Selected: ${Q5_SKILLS}"
else
  echo "None selected. See [\`skills/SKILLS.md\`](../../agent-stack/skills/SKILLS.md) (or the bundled copy if applicable) and pick what you need."
fi)

## Branch model

${Q2_BRANCH}.

## Conventions in this repo

- Commit subjects follow Conventional Commits (\`feat:\`, \`fix:\`, etc.)
- CHANGELOG.md \`[Unreleased]\` block updated per slice
- Glossary (CONTEXT.md) updated whenever a new term is introduced
- Issue tracker uses 6-axis label taxonomy (see docs/agents/issues/label-taxonomy.md)
EOF
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [would write] $BOOTSTRAP_PATH"
  else
    echo "  [wrote] $BOOTSTRAP_PATH"
  fi
fi

echo
echo "Bootstrap complete."
echo
echo "Next steps:"
echo "  - Review FRAMEWORK_BOOTSTRAP.md"
echo "  - Fill in AGENTS.md and CONTEXT.md with project-specific content"
echo "  - Run scripts/sync-labels.sh (if you opted into issues scaffolding)"
echo "  - Run scripts/dedupe-skills.sh --dry-run to see skill overlap"