from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TASK_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")


def read_stdin_json() -> Dict[str, Any]:
    data = sys.stdin.read()
    if not data.strip():
        return {}
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return {"_raw": data}


def expand_env(value: str) -> str:
    # Simple ${VAR} expansion for config commands.
    out = value
    for key, val in os.environ.items():
        out = out.replace("${" + key + "}", val)
    return out


def find_workspace(start: Optional[str] = None) -> Optional[Path]:
    candidates: List[Path] = []
    env_root = os.environ.get("AIOPS_WORKSPACE_ROOT")
    if env_root:
        candidates.append(Path(env_root).expanduser())
    if start:
        candidates.append(Path(start).expanduser())
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        candidates.append(Path(os.environ["CLAUDE_PROJECT_DIR"]).expanduser())
    candidates.append(Path.cwd())

    seen = set()
    for c in candidates:
        try:
            c = c.resolve()
        except Exception:
            continue
        for p in [c, *c.parents]:
            if str(p) in seen:
                continue
            seen.add(str(p))
            if (p / ".aiops.json").exists():
                return p
    return None


def load_config(cwd: Optional[str] = None) -> Tuple[Optional[Path], Dict[str, Any]]:
    root = find_workspace(cwd)
    if not root:
        return None, {}
    path = root / ".aiops.json"
    try:
        return root, json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return root, {"_error": f"Failed to load {path}: {exc}"}


def hook_output(event: str, context: str = "", **extra: Any) -> None:
    payload: Dict[str, Any] = {"hookSpecificOutput": {"hookEventName": event}}
    if context:
        payload["hookSpecificOutput"]["additionalContext"] = context
    payload["hookSpecificOutput"].update(extra)
    print(json.dumps(payload, ensure_ascii=False))


def block_with_stderr(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


def json_block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    sys.exit(0)


def task_id_from_prompt(prompt: str) -> Optional[str]:
    m = TASK_RE.search(prompt or "")
    return m.group(0) if m else None


def current_repo(workspace: Path, config: Dict[str, Any], cwd: str) -> Optional[Dict[str, Any]]:
    cwd_path = Path(cwd).expanduser().resolve()
    repos = config.get("repos", [])
    for repo in repos:
        repo_path = (workspace / repo.get("path", repo.get("name", ""))).resolve()
        try:
            cwd_path.relative_to(repo_path)
            return {**repo, "abs_path": str(repo_path)}
        except ValueError:
            continue
    # Fallback to git root basename.
    try:
        git_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
        name = Path(git_root).name
        for repo in repos:
            if repo.get("name") == name:
                return {**repo, "abs_path": git_root}
    except Exception:
        pass
    return None


def rel_to_repo(repo: Dict[str, Any], file_path: str) -> str:
    p = Path(file_path).expanduser()
    if not p.is_absolute():
        return file_path
    root = Path(repo.get("abs_path", ".")).resolve()
    try:
        return str(p.resolve().relative_to(root)).replace("\\", "/")
    except Exception:
        return str(p)


def path_allowed(rel_path: str, patterns: List[str]) -> bool:
    if not patterns:
        return False
    rel_path = rel_path.replace("\\", "/")
    for pat in patterns:
        if fnmatch.fnmatch(rel_path, pat):
            return True
    return False


def path_forbidden(rel_path: str, patterns: List[str]) -> bool:
    rel_path = rel_path.replace("\\", "/")
    for pat in patterns or []:
        if fnmatch.fnmatch(rel_path, pat):
            return True
    return False


def adapter_command(config: Dict[str, Any]) -> List[str]:
    cmd = config.get("feishu", {}).get("adapter_command") or os.environ.get("AIOPS_FEISHU_ADAPTER")
    if not cmd:
        raise RuntimeError("Missing feishu.adapter_command in .aiops.json or AIOPS_FEISHU_ADAPTER")
    if isinstance(cmd, str):
        return [expand_env(cmd)]
    return [expand_env(str(x)) for x in cmd]


def run_adapter(workspace: Path, config: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
    cmd = adapter_command(config) + args
    env = os.environ.copy()
    env["AIOPS_WORKSPACE_ROOT"] = str(workspace)
    env.setdefault("CLAUDE_PLUGIN_ROOT", os.environ.get("CLAUDE_PLUGIN_ROOT", str(Path(__file__).resolve().parents[1])))
    proc = subprocess.run(cmd, cwd=str(workspace), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"Adapter failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    out = proc.stdout.strip() or "{}"
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"text": out}


def get_task(workspace: Path, config: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    return run_adapter(workspace, config, ["task-get", task_id])


def state_dir(workspace: Path) -> Path:
    p = workspace / ".aiops" / "state"
    p.mkdir(parents=True, exist_ok=True)
    return p


def preflight_path(workspace: Path, session_id: str, task_id: str) -> Path:
    d = state_dir(workspace) / "preflight"
    d.mkdir(parents=True, exist_ok=True)
    safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "-", session_id or "manual")
    return d / f"{safe_session}.{task_id}.ok"


def git_dirty_files(cwd: str) -> List[str]:
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=cwd, text=True, stderr=subprocess.DEVNULL)
        return [x for x in out.splitlines() if x.strip()]
    except Exception:
        return []


def codegraph_status(cwd: str, limit: int = 80) -> str:
    try:
        out = subprocess.check_output(["codegraph", "status"], cwd=cwd, text=True, stderr=subprocess.STDOUT, timeout=20)
        lines = out.splitlines()[:limit]
        return "\n".join(lines)
    except FileNotFoundError:
        return "codegraph command not found. Install CodeGraph or disable codegraph.enabled in .aiops.json."
    except Exception as exc:
        return f"codegraph status unavailable: {exc}"
