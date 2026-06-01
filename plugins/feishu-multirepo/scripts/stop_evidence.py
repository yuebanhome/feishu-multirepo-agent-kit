from utils import read_stdin_json, load_config, get_task, git_dirty_files, codegraph_status
import os, json, sys

inp = read_stdin_json()
cwd = inp.get("cwd") or "."
workspace, config = load_config(cwd)
if not workspace:
    raise SystemExit(0)
policy = config.get("policy", {})
if not policy.get("stop_requires_evidence", True):
    raise SystemExit(0)

task_id = os.environ.get("FEISHU_TASK_ID") or os.environ.get("AIOPS_TASK_ID")
if not task_id:
    raise SystemExit(0)

reasons = []
try:
    task = get_task(workspace, config, task_id)
except Exception as exc:
    reasons.append(f"cannot load task {task_id}: {exc}")
else:
    if task.get("status") in {"claimed", "in_progress"}:
        reasons.append(f"task {task_id} is still {task.get('status')}; update status or explain blocked state in Feishu")
    if not task.get("evidence"):
        reasons.append(f"task {task_id} is missing evidence")
    if policy.get("stop_requires_pr_url_when_dirty", False) and git_dirty_files(cwd) and not task.get("pr_url"):
        reasons.append(f"task {task_id} has dirty files but no pr_url")

if config.get("codegraph", {}).get("enabled", True):
    st = codegraph_status(cwd, limit=40)
    if "Pending sync" in st or "pending" in st.lower():
        reasons.append("CodeGraph appears to have pending sync; resolve before stopping")

if reasons:
    print(json.dumps({"decision": "block", "reason": "AI Ops Stop gate:\n- " + "\n- ".join(reasons)}, ensure_ascii=False))
    raise SystemExit(0)
