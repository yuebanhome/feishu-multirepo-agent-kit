#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from utils import load_config, run_adapter, preflight_path, state_dir, current_repo, codegraph_status

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parents[1])).resolve()


def cmd_init(args):
    workspace = Path(args.workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / ".aiops" / "state" / "preflight").mkdir(parents=True, exist_ok=True)
    config_path = workspace / ".aiops.json"
    if not config_path.exists() or args.force:
        shutil.copyfile(PLUGIN_ROOT / "templates" / "aiops.json", config_path)
        print(f"created {config_path}")
    else:
        print(f"exists {config_path}")
    claude_path = workspace / "CLAUDE.md"
    if not claude_path.exists() or args.force:
        shutil.copyfile(PLUGIN_ROOT / "templates" / "CLAUDE.md", claude_path)
        print(f"created {claude_path}")
    tasks_path = workspace / ".aiops" / "state" / "tasks.json"
    if not tasks_path.exists() or args.force:
        shutil.copyfile(PLUGIN_ROOT / "templates" / "tasks.demo.json", tasks_path)
        print(f"created {tasks_path}")


def cmd_doctor(args):
    workspace, config = load_config(args.cwd)
    if not workspace:
        print("FAIL: .aiops.json not found")
        return 1
    print(f"workspace: {workspace}")
    print(f"config: {workspace / '.aiops.json'}")
    print("repos:")
    for r in config.get("repos", []):
        path = workspace / r.get("path", r.get("name", ""))
        exists = path.exists()
        cg = (path / ".codegraph").exists()
        print(f"- {r.get('name')}: exists={exists} codegraph={cg} participates={r.get('participates')} path={path}")
    print("codegraph:")
    print(codegraph_status(args.cwd or str(workspace), limit=40))
    return 0


def cmd_task(args):
    workspace, config = load_config(args.cwd)
    if not workspace:
        print(".aiops.json not found", file=sys.stderr); return 2
    if args.action == "get":
        print(json.dumps(run_adapter(workspace, config, ["task-get", args.task_id]), ensure_ascii=False, indent=2))
    elif args.action == "list":
        extra = ["task-list"]
        if args.status: extra += ["--status", args.status]
        print(json.dumps(run_adapter(workspace, config, extra), ensure_ascii=False, indent=2))
    return 0


def cmd_claim(args):
    workspace, config = load_config(args.cwd)
    if not workspace:
        print(".aiops.json not found", file=sys.stderr); return 2
    owner = args.owner
    repo = args.repo
    branch = args.branch or f"feat/{args.task_id}"
    print(json.dumps(run_adapter(workspace, config, ["task-claim", args.task_id, owner, repo, branch]), ensure_ascii=False, indent=2))
    return 0


def cmd_update(args):
    workspace, config = load_config(args.cwd)
    if not workspace:
        print(".aiops.json not found", file=sys.stderr); return 2
    cmd = ["task-update", args.task_id]
    if args.status: cmd += ["--status", args.status]
    if args.evidence: cmd += ["--evidence", args.evidence]
    if args.pr_url: cmd += ["--pr-url", args.pr_url]
    print(json.dumps(run_adapter(workspace, config, cmd), ensure_ascii=False, indent=2))
    return 0


def cmd_preflight(args):
    workspace, config = load_config(args.cwd)
    if not workspace:
        print(".aiops.json not found", file=sys.stderr); return 2
    session_id = os.environ.get("CLAUDE_SESSION_ID") or args.session_id or "manual"
    marker = preflight_path(workspace, session_id, args.task_id)
    marker.write_text("ok\n", encoding="utf-8")
    print(f"created {marker}")
    return 0


def cmd_codegraph_index_all(args):
    workspace, config = load_config(args.cwd)
    if not workspace:
        print(".aiops.json not found", file=sys.stderr); return 2
    for r in config.get("repos", []):
        if not r.get("participates"):
            continue
        if r.get("status") == "empty" and not config.get("codegraph", {}).get("init_empty_repos", False):
            print(f"skip empty repo {r.get('name')}")
            continue
        path = workspace / r.get("path", r.get("name", ""))
        if not path.exists():
            print(f"skip missing repo {r.get('name')}: {path}")
            continue
        print(f"indexing {r.get('name')} at {path}")
        subprocess.run(["codegraph", "init", "-i"], cwd=str(path), check=False)
    return 0


def main():
    parser = argparse.ArgumentParser(prog="aiops")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--workspace", default=".")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("doctor")
    p.add_argument("--cwd", default=os.getcwd())
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("task")
    p.add_argument("action", choices=["get", "list"])
    p.add_argument("task_id", nargs="?")
    p.add_argument("--status")
    p.add_argument("--cwd", default=os.getcwd())
    p.set_defaults(func=cmd_task)

    p = sub.add_parser("claim")
    p.add_argument("task_id")
    p.add_argument("--owner", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--branch")
    p.add_argument("--cwd", default=os.getcwd())
    p.set_defaults(func=cmd_claim)

    p = sub.add_parser("update")
    p.add_argument("task_id")
    p.add_argument("--status")
    p.add_argument("--evidence")
    p.add_argument("--pr-url")
    p.add_argument("--cwd", default=os.getcwd())
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("preflight-ok")
    p.add_argument("task_id")
    p.add_argument("--session-id")
    p.add_argument("--cwd", default=os.getcwd())
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("codegraph-index-all")
    p.add_argument("--cwd", default=os.getcwd())
    p.set_defaults(func=cmd_codegraph_index_all)

    args = parser.parse_args()
    raise SystemExit(args.func(args) or 0)

if __name__ == "__main__":
    main()
