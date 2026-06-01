from utils import read_stdin_json, load_config, current_repo, hook_output, codegraph_status, git_dirty_files

inp = read_stdin_json()
cwd = inp.get("cwd") or "."
workspace, config = load_config(cwd)
if not workspace or not config.get("codegraph", {}).get("enabled", True):
    raise SystemExit(0)

repo = current_repo(workspace, config, cwd)
if not repo:
    raise SystemExit(0)

status = codegraph_status(cwd, limit=80)
dirty = git_dirty_files(cwd)
file_path = (inp.get("tool_input") or {}).get("file_path", "")
context = "\n".join([
    "# AI Ops post-edit CodeGraph context",
    f"edited_file: {file_path}",
    f"repo: {repo.get('name')}",
    "",
    "## git dirty files",
    "\n".join(f"- {x}" for x in dirty) if dirty else "none",
    "",
    "## codegraph status",
    status,
    "",
    "Next: run task verification commands and update Feishu evidence before Stop.",
])
hook_output("PostToolUse", context)
