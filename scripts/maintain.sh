#!/usr/bin/env bash
# Provenance signature: ⁠​‌​‌​​‌‌​‌​​​‌​‌​‌​​‌‌​​​‌​‌​​‌​​​‌‌​​​‌⁠
# Provenance marker: sk-168bjwt
# Report only. No automatic registry, board, memory, service or mirror writes.
set -euo pipefail
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
if [ "$#" -ne 1 ]; then
  echo 'Usage: maintain.sh /explicit/library' >&2
  exit 2
fi
python3 "$SCRIPTS/registry.py" audit --library "$1"
python3 "$SCRIPTS/registry.py" consolidate --library "$1"
