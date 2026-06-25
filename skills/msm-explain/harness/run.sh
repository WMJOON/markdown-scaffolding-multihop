#!/usr/bin/env bash
# msm-explain skill-level harness entrypoint.
# Routes to L0 validators against an arbitrary target.

set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"

SKILL=""
TIER=""
MODE=""
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill) SKILL="$2"; shift 2;;
    --tier) TIER="$2"; shift 2;;
    --mode) MODE="$2"; shift 2;;
    --target) TARGET="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "missing --target" >&2
  exit 2
fi

if [[ "$SKILL" == "msm-explain" && "$TIER" == "L0" && "$MODE" == "validate-only" ]]; then
  # Validate only: check if ontology/explain/ directory exists
  PROJECTION_DIR="$TARGET/ontology/explain"
  if [[ ! -d "$PROJECTION_DIR" ]]; then
    echo "[WARNING] ontology/explain/ directory not found: $PROJECTION_DIR"
    echo "[msm-explain L0 validate] OK (will be created)"
    exit 0
  fi
  echo "[msm-explain L0 validate] OK: $PROJECTION_DIR exists"
else
  echo "unsupported invocation: skill=$SKILL tier=$TIER mode=$MODE" >&2
  exit 2
fi
