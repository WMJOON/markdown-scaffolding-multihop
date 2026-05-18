#!/usr/bin/env bash
set -euo pipefail

SKILL=""
TIER="L0"
MODE="validate-only"
TARGET="."
DOMAIN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      SKILL="${2:-}"
      shift 2
      ;;
    --tier)
      TIER="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --domain)
      DOMAIN="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$SKILL" != "" && "$SKILL" != "msm-repository-setup" ]]; then
  echo "Unsupported skill: $SKILL" >&2
  exit 2
fi

if [[ "$TIER" != "L0" ]]; then
  echo "Only L0 is supported by the setup stub" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARGS=(--target "$TARGET")

case "$MODE" in
  dry-run)
    ARGS+=(--dry-run)
    ;;
  validate-only)
    ARGS+=(--validate-only)
    ;;
  apply)
    ARGS+=(--apply --yes)
    ;;
  *)
    echo "Unsupported mode: $MODE" >&2
    exit 2
    ;;
esac

if [[ -n "$DOMAIN" ]]; then
  ARGS+=(--domain "$DOMAIN")
fi

python3 "$SCRIPT_DIR/scripts/msm_init.py" "${ARGS[@]}"

