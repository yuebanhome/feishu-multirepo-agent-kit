from utils import read_stdin_json, load_config, current_repo, hook_output, git_dirty_files

inp = read_stdin_json()
cwd = inp.get("cwd") or "."
workspace, config = load_config(cwd)
if not workspace:
    raise SystemExit(0)
repo = current_repo(workspace, config, cwd)
if not repo:
    raise SystemExit(0)
dirty = git_dirty_files(cwd)
if not dirty:
    raise SystemExit(0)
context = "# AI Ops batch context\n" + "\n".join(f"- changed: {x}" for x in dirty) + "\nRun CodeGraph impact checks before continuing if core symbols changed."
hook_output("PostToolBatch", context)
