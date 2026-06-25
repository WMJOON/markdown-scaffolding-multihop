#!/usr/bin/env bash
# Legacy harness wrapper for msm-record-archive.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL="$SCRIPT_DIR/../../msm-record-archive/harness/run.sh"

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      ARGS+=(--skill msm-record-archive)
      shift 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

exec "$CANONICAL" "${ARGS[@]}"
