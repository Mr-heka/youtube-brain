#!/usr/bin/env bash
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$#" -ne 1 ]; then
  echo 'Usage: smoke.sh /explicit/test-target' >&2
  exit 2
fi
if [ ! -d "$1" ] || [ -L "$1" ]; then
  echo 'Test target must be an existing, non-symlink directory.' >&2
  exit 2
fi
TARGET_ROOT="$(cd "$1" && pwd -P)"
PYTHON="${PYTHON_BIN:-python3}"
"$PYTHON" -c 'import sys, yaml; assert sys.version_info >= (3, 11), sys.version'
SMOKE_TMP="$(mktemp -d "$TARGET_ROOT/topic-brain-smoke.XXXXXX")"
trap 'rm -rf "$SMOKE_TMP"' EXIT INT TERM
PYTHONDONTWRITEBYTECODE=1 \
TMPDIR="$SMOKE_TMP" \
"$PYTHON" -B "$SKILL_DIR/tests/run_offline.py" "$SKILL_DIR/tests"
