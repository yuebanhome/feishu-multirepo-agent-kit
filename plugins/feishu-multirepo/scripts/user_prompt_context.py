from utils import read_stdin_json, load_config, task_id_from_prompt, get_task, hook_output
import json

inp = read_stdin_json()
prompt = inp.get("prompt", "")
task_id = task_id_from_prompt(prompt)
if not task_id:
    raise SystemExit(0)

workspace, config = load_config(inp.get("cwd"))
if not workspace:
    hook_output("UserPromptSubmit", f"AI Ops: task id {task_id} detected, but no .aiops.json found.")
    raise SystemExit(0)

try:
    task = get_task(workspace, config, task_id)
except Exception as exc:
    hook_output("UserPromptSubmit", f"AI Ops: failed to load task {task_id}: {exc}")
    raise SystemExit(0)

lines = [
    f"# Feishu task context: {task_id}",
    f"title: {task.get('title', '')}",
    f"status: {task.get('status', '')}",
    f"owner: {task.get('owner', '')}",
    f"primary_repo: {task.get('primary_repo', '')}",
    f"related_repos: {', '.join(task.get('related_repos', []))}",
    f"allowed_paths: {', '.join(task.get('allowed_paths', []))}",
    f"forbidden_paths: {', '.join(task.get('forbidden_paths', []))}",
    f"depends_on: {', '.join(task.get('depends_on', []))}",
    f"codegraph_seeds: {', '.join(task.get('codegraph_seeds', []))}",
    "",
    "## Acceptance criteria",
]
for x in task.get("acceptance_criteria", []):
    lines.append(f"- {x}")
lines.append("")
lines.append("## Verification")
for x in task.get("verification", []):
    lines.append(f"- {x}")
lines.extend([
    "",
    "## Execution rule",
    "Before editing: confirm claim, run CodeGraph context/search/impact, then run `aiops preflight-ok " + task_id + "`.",
])

hook_output("UserPromptSubmit", "\n".join(lines), sessionTitle=f"{task_id}:{task.get('title','task')[:40]}")
