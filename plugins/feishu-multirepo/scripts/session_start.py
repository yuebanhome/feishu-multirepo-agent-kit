from utils import read_stdin_json, load_config, current_repo, hook_output, codegraph_status
from pathlib import Path

inp = read_stdin_json()
cwd = inp.get("cwd") or "."
workspace, config = load_config(cwd)
if not workspace:
    hook_output("SessionStart", "AI Ops: no .aiops.json found. Run `aiops init` at the multi-repo workspace root.")
    raise SystemExit(0)

repo = current_repo(workspace, config, cwd)
lines = [
    "# AI Ops workspace context",
    f"workspace: {workspace}",
    f"workspace_name: {config.get('workspace_name', '')}",
    "",
    "## Repos",
]
for r in config.get("repos", []):
    lines.append(f"- {r.get('name')}: path={r.get('path')} role={r.get('role')} participates={r.get('participates')} status={r.get('status')}")

if repo:
    lines.extend(["", "## Current repo", f"name: {repo.get('name')}", f"role: {repo.get('role')}", f"participates: {repo.get('participates')}"])
    if config.get("codegraph", {}).get("enabled", True):
        lines.extend(["", "## CodeGraph status", codegraph_status(cwd)])
else:
    lines.extend(["", "## Current repo", "No configured repo detected from cwd."])

lines.extend([
    "",
    "## Hard rules",
    "- Feishu task claim is required before Edit/Write/MultiEdit.",
    "- Use CodeGraph before editing existing repos.",
    "- Keep edits inside task.allowed_paths.",
])

hook_output("SessionStart", "\n".join(lines), sessionTitle=f"aiops:{config.get('workspace_name','workspace')}")
