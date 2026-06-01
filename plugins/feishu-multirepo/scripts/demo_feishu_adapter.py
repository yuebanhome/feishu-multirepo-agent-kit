#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List


def root() -> Path:
    return Path(os.environ.get("AIOPS_WORKSPACE_ROOT", ".")).expanduser().resolve()


def store_path() -> Path:
    p = root() / ".aiops" / "state" / "tasks.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(json.dumps({"tasks": [], "prds": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def load() -> Dict[str, Any]:
    return json.loads(store_path().read_text(encoding="utf-8"))


def save(data: Dict[str, Any]) -> None:
    store_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_task(data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    for t in data.get("tasks", []):
        if t.get("task_id") == task_id:
            return t
    raise SystemExit(json.dumps({"error": f"task not found: {task_id}"}, ensure_ascii=False))


def main(argv: List[str]) -> None:
    if not argv:
        print(json.dumps({"error": "missing command"}, ensure_ascii=False)); raise SystemExit(2)
    cmd = argv[0]
    data = load()

    if cmd == "task-get":
        task = find_task(data, argv[1])
        print(json.dumps(task, ensure_ascii=False))
        return

    if cmd == "task-list":
        status = None
        if "--status" in argv:
            status = argv[argv.index("--status") + 1]
        tasks = data.get("tasks", [])
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        print(json.dumps({"tasks": tasks}, ensure_ascii=False))
        return

    if cmd == "task-claim":
        _, task_id, owner, repo, branch = argv[:5]
        task = find_task(data, task_id)
        if task.get("owner") and task.get("owner") != owner:
            print(json.dumps({"ok": False, "reason": f"already owned by {task.get('owner')}", "task": task}, ensure_ascii=False))
            raise SystemExit(3)
        if task.get("status") not in {"ready", "claimed", "in_progress"}:
            print(json.dumps({"ok": False, "reason": f"status not claimable: {task.get('status')}", "task": task}, ensure_ascii=False))
            raise SystemExit(3)
        task["status"] = "claimed"
        task["owner_type"] = "agent" if owner.startswith("agent:") else "human"
        task["owner"] = owner
        task["primary_repo"] = task.get("primary_repo") or repo
        task["branch"] = branch
        task["claim_lock"] = str(uuid.uuid4())
        task["claimed_at"] = int(time.time())
        save(data)
        print(json.dumps({"ok": True, "task": task}, ensure_ascii=False))
        return

    if cmd == "task-update":
        task_id = argv[1]
        task = find_task(data, task_id)
        i = 2
        while i < len(argv):
            if argv[i] == "--status":
                task["status"] = argv[i+1]; i += 2
            elif argv[i] == "--evidence":
                task["evidence"] = argv[i+1]; i += 2
            elif argv[i] == "--pr-url":
                task["pr_url"] = argv[i+1]; i += 2
            else:
                i += 1
        save(data)
        print(json.dumps({"ok": True, "task": task}, ensure_ascii=False))
        return

    if cmd == "task-comment":
        task_id = argv[1]
        message = " ".join(argv[2:])
        comments = root() / ".aiops" / "state" / "comments.jsonl"
        comments.parent.mkdir(parents=True, exist_ok=True)
        with comments.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"task_id": task_id, "message": message, "ts": int(time.time())}, ensure_ascii=False) + "\n")
        print(json.dumps({"ok": True}, ensure_ascii=False))
        return

    if cmd == "prd-get":
        prd_id = argv[1]
        for p in data.get("prds", []):
            if p.get("prd_id") == prd_id:
                print(json.dumps(p, ensure_ascii=False)); return
        print(json.dumps({"prd_id": prd_id, "title": "", "body": ""}, ensure_ascii=False)); return

    print(json.dumps({"error": f"unknown command: {cmd}"}, ensure_ascii=False))
    raise SystemExit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
