#!/usr/bin/env bash
# Legacy harness wrapper for msm-explain.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL="$SCRIPT_DIR/../../msm-explain/harness/run.sh"

ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      ARGS+=(--skill msm-explain)
      shift 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

exec "$CANONICAL" "${ARGS[@]}"
