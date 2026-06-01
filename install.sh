#!/usr/bin/env bash
set -euo pipefail

SCOPE="user"
WORKSPACE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)
      SCOPE="$2"; shift 2 ;;
    --workspace)
      WORKSPACE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: ./install.sh [--workspace /path/to/multirepo] [--scope user|project|local]"
      exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Validating marketplace"
if command -v claude >/dev/null 2>&1; then
  claude plugin validate "$KIT_DIR" || true
  claude plugin validate "$KIT_DIR/plugins/feishu-multirepo" || true

  echo "==> Registering marketplace: $KIT_DIR"
  claude plugin marketplace add "$KIT_DIR" --scope "$SCOPE"

  echo "==> Installing plugin: feishu-multirepo@aiops-agent-kit"
  claude plugin install "feishu-multirepo@aiops-agent-kit" --scope "$SCOPE"
else
  echo "WARN: claude CLI not found. Install Claude Code first, then run:" >&2
  echo "  claude plugin marketplace add $KIT_DIR --scope $SCOPE" >&2
  echo "  claude plugin install feishu-multirepo@aiops-agent-kit --scope $SCOPE" >&2
fi

if [[ -n "$WORKSPACE" ]]; then
  mkdir -p "$WORKSPACE/.aiops/state/preflight"
  if [[ ! -f "$WORKSPACE/.aiops.json" ]]; then
    cp "$KIT_DIR/plugins/feishu-multirepo/templates/aiops.json" "$WORKSPACE/.aiops.json"
    echo "==> Created $WORKSPACE/.aiops.json"
  else
    echo "==> $WORKSPACE/.aiops.json already exists; not overwriting"
  fi

  if [[ ! -f "$WORKSPACE/CLAUDE.md" ]]; then
    cp "$KIT_DIR/plugins/feishu-multirepo/templates/CLAUDE.md" "$WORKSPACE/CLAUDE.md"
    echo "==> Created $WORKSPACE/CLAUDE.md"
  else
    echo "==> $WORKSPACE/CLAUDE.md already exists; not overwriting"
  fi

  if [[ ! -f "$WORKSPACE/.aiops/state/tasks.json" ]]; then
    cp "$KIT_DIR/plugins/feishu-multirepo/templates/tasks.demo.json" "$WORKSPACE/.aiops/state/tasks.json"
    echo "==> Created demo task store at $WORKSPACE/.aiops/state/tasks.json"
  fi
fi

echo "==> Done"
