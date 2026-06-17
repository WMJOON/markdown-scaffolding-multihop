#!/usr/bin/env bash
# MSM v0.10.1 — install symlinks into ~/.{claude,codex,antigravity}/skills/
# Usage:
#   ./install.sh                Claude Code only (default)
#   ./install.sh --codex        Codex only
#   ./install.sh --antigravity  Antigravity only
#   ./install.sh --all          Claude Code + Codex + Antigravity
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"

MSM_SKILLS=(
  msm-orchestration
  msm-evidence
  msm-harness
  msm-maintain
  msm-ontology
  msm-repository-setup
)

# Parse args
TARGETS=()
for arg in "$@"; do
  case "$arg" in
    --codex)       TARGETS+=(codex) ;;
    --antigravity) TARGETS+=(antigravity) ;;
    --all)         TARGETS+=(claude codex antigravity) ;;
    *)             ;;
  esac
done
[[ ${#TARGETS[@]} -eq 0 ]] && TARGETS=(claude)

echo "MSM v0.10.1 Install"
echo "  Skills  : ${MSM_SKILLS[*]}"
echo "  Targets : ${TARGETS[*]}"
echo ""

link_skill() {
  local src="$1" dst="$2" label="$3"
  if [ -L "$dst" ]; then
    echo "  SKIP  $label  (already linked)"
  elif [ -e "$dst" ]; then
    echo "  SKIP  $label  (path exists — remove manually to re-link)"
  else
    ln -sf "$src" "$dst"
    echo "  LINK  $label"
  fi
}

for target in "${TARGETS[@]}"; do
  if [ "$target" == "antigravity" ]; then
    SKILLS_DST="${HOME}/.gemini/antigravity/skills"
  else
    SKILLS_DST="${HOME}/.${target}/skills"
  fi
  mkdir -p "$SKILLS_DST"
  echo "[$target]"
  for skill in "${MSM_SKILLS[@]}"; do
    link_skill "$SKILLS_SRC/$skill" "$SKILLS_DST/$skill" "$skill"
  done
  echo ""
done

echo "Done."
