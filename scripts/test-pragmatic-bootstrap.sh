#!/usr/bin/env bash
# test-pragmatic-bootstrap.sh - regression net for default pragmatic skill
# packaging, idempotency, manifest validation, and selective uninit.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SANDBOX="$(mktemp -d)"
TARGET="$SANDBOX/target"
TEST_HOME="$SANDBOX/home"
trap 'rm -rf "$SANDBOX"' EXIT
mkdir -p "$TARGET" "$TEST_HOME"

# Existing alternate project skill must trigger collision warning and survive
# bootstrap plus uninit.
mkdir -p "$TARGET/.agents/skills/pragmatic-programmer"
cat > "$TARGET/.agents/skills/pragmatic-programmer/SKILL.md" <<'EOF'
---
name: pragmatic-programmer
description: Existing alternate-location fixture.
---
EOF

HOME="$TEST_HOME" bash "$SCRIPT_DIR/dedupe-skills.sh" --strict \
  > "$SANDBOX/dedupe.out"
grep -q 'pragmatic-programmer: OK' "$SANDBOX/dedupe.out"

echo "[test] first bootstrap"
HOME="$TEST_HOME" bash "$SCRIPT_DIR/init.sh" "$TARGET" \
  > "$SANDBOX/first.out"

expected_files=(
  "SKILL.md"
  "UPSTREAM.md"
  "LICENSE.upstream"
  "references/diagnostic.md"
  "references/principle-crosswalk.md"
  ".agent-stack-owned"
)
for relative in "${expected_files[@]}"; do
  path="$TARGET/.pi/skills/pragmatic-programmer/$relative"
  if [[ ! -f "$path" ]]; then
    echo "FAIL: bootstrap missing $path" >&2
    exit 1
  fi
done

grep -q 'Selected: pragmatic-programmer' "$TARGET/FRAMEWORK_BOOTSTRAP.md"
grep -q '\[copied skill\].*pragmatic-programmer' "$SANDBOX/first.out"
grep -q '\[warn\] skill collision:.*\.agents/skills/pragmatic-programmer/SKILL.md' \
  "$SANDBOX/first.out"

echo "[test] idempotent bootstrap"
HOME="$TEST_HOME" bash "$SCRIPT_DIR/init.sh" "$TARGET" \
  > "$SANDBOX/second.out"
grep -q '\[skip\].*pragmatic-programmer/SKILL.md' "$SANDBOX/second.out"

# Uninit must not delete skill packages it did not create.
mkdir -p "$TARGET/.pi/skills/user-owned"
cat > "$TARGET/.pi/skills/user-owned/SKILL.md" <<'EOF'
---
name: user-owned
description: Fixture proving selective uninit.
---
EOF

echo "[test] selective uninit"
HOME="$TEST_HOME" bash "$SCRIPT_DIR/init.sh" "$TARGET" --uninit \
  > "$SANDBOX/uninit.out"

if [[ -d "$TARGET/.pi/skills/pragmatic-programmer" ]]; then
  echo "FAIL: managed pragmatic-programmer package survived uninit" >&2
  exit 1
fi
if [[ ! -f "$TARGET/.pi/skills/user-owned/SKILL.md" ]]; then
  echo "FAIL: uninit removed unmanaged user-owned skill" >&2
  exit 1
fi
if [[ ! -f "$TARGET/.agents/skills/pragmatic-programmer/SKILL.md" ]]; then
  echo "FAIL: uninit removed alternate-location skill" >&2
  exit 1
fi
if [[ -d "$TARGET/docs/agents" || -f "$TARGET/FRAMEWORK_BOOTSTRAP.md" ]]; then
  echo "FAIL: framework docs survived uninit" >&2
  exit 1
fi

echo "OK: pragmatic-programmer bootstrap integration"
