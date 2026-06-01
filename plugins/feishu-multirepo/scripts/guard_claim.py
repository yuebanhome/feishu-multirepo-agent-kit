from utils import (
    read_stdin_json, load_config, current_repo, get_task, rel_to_repo,
    path_allowed, path_forbidden, block_with_stderr, preflight_path, hook_output
)
import os

inp = read_stdin_json()
cwd = inp.get("cwd") or "."
workspace, config = load_config(cwd)
if not workspace:
    block_with_stderr("AI Ops blocked edit: .aiops.json not found. Run aiops init at workspace root.")

policy = config.get("policy", {})
if not policy.get("require_claim_for_edits", True):
    raise SystemExit(0)

task_id = os.environ.get("FEISHU_TASK_ID") or os.environ.get("AIOPS_TASK_ID")
if not task_id:
    block_with_stderr("AI Ops blocked edit: FEISHU_TASK_ID/AIOPS_TASK_ID is missing. Claim a Feishu task before editing.")

try:
    task = get_task(workspace, config, task_id)
except Exception as exc:
    block_with_stderr(f"AI Ops blocked edit: cannot load task {task_id}: {exc}")

status = task.get("status")
if status not in {"claimed", "in_progress"}:
    block_with_stderr(f"AI Ops blocked edit: task {task_id} status is {status}, expected claimed/in_progress.")

owner = task.get("owner", "")
owner_prefix = policy.get("agent_owner_prefix", "agent:")
if policy.get("block_human_owned_tasks", True) and not owner.startswith(owner_prefix):
    block_with_stderr(f"AI Ops blocked edit: task {task_id} is owned by human or non-agent owner: {owner!r}.")

repo = current_repo(workspace, config, cwd)
if not repo:
    block_with_stderr("AI Ops blocked edit: current directory is not inside a configured repo.")

if repo.get("name") != task.get("primary_repo"):
    block_with_stderr(f"AI Ops blocked edit: current repo {repo.get('name')} != task.primary_repo {task.get('primary_repo')}.")

# Check file path. MultiEdit has file_path too in current Claude Code; if absent, block conservatively.
tool_input = inp.get("tool_input") or {}
file_path = tool_input.get("file_path") or tool_input.get("path")
if not file_path:
    block_with_stderr("AI Ops blocked edit: cannot determine edited file path from tool input.")
rel = rel_to_repo(repo, file_path)

if path_forbidden(rel, task.get("forbidden_paths", [])):
    block_with_stderr(f"AI Ops blocked edit: {rel} matches task.forbidden_paths.")

if policy.get("require_allowed_paths", True) and not path_allowed(rel, task.get("allowed_paths", [])):
    block_with_stderr(f"AI Ops blocked edit: {rel} is not inside task.allowed_paths for {task_id}.")

if policy.get("require_codegraph_preflight", True):
    session_id = inp.get("session_id") or os.environ.get("CLAUDE_SESSION_ID") or "manual"
    marker = preflight_path(workspace, session_id, task_id)
    if not marker.exists() and os.environ.get("AIOPS_CODEGRAPH_PREFLIGHT") != "1":
        block_with_stderr(
            "AI Ops blocked edit: CodeGraph preflight marker is missing.\n"
            f"Run CodeGraph context/search/callers/callees/impact for {task_id}, then run:\n"
            f"  aiops preflight-ok {task_id}\n"
            "For emergency bypass only, set AIOPS_CODEGRAPH_PREFLIGHT=1."
        )

hook_output("PreToolUse", f"AI Ops guard passed for {task_id}. Edit path: {rel}", permissionDecision="allow", permissionDecisionReason="Task claim, repo, path, and CodeGraph preflight passed.")
