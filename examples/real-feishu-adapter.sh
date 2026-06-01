#!/usr/bin/env bash
set -euo pipefail

# Replace this with your real Feishu CLI commands.
# Contract expected by plugin scripts:
#   adapter task-get PX-123
#   adapter task-list --status ready
#   adapter task-claim PX-123 agent:repo-b repo-b feat/PX-123
#   adapter task-update PX-123 --status review --evidence evidence --pr-url url
#   adapter task-comment PX-123 message
#   adapter prd-get PRD-2026-001

CMD="$1"; shift || true

case "$CMD" in
  task-get)
    TASK_ID="$1"
    feishu task get --id "$TASK_ID" --json
    ;;
  task-list)
    feishu task list "$@" --json
    ;;
  task-claim)
    TASK_ID="$1"; OWNER="$2"; REPO="$3"; BRANCH="$4"
    feishu task claim --id "$TASK_ID" --owner "$OWNER" --repo "$REPO" --branch "$BRANCH" --json
    ;;
  task-update)
    TASK_ID="$1"; shift
    feishu task update --id "$TASK_ID" "$@" --json
    ;;
  task-comment)
    TASK_ID="$1"; shift
    feishu task comment --id "$TASK_ID" --message "$*" --json
    ;;
  prd-get)
    PRD_ID="$1"
    feishu prd get --id "$PRD_ID" --json
    ;;
  *)
    echo "unknown adapter command: $CMD" >&2
    exit 2
    ;;
esac
