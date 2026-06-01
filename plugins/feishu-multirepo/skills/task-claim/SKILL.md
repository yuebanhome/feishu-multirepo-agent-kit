---
description: Claim a Feishu task atomically for human or agent owner and prepare branch/worktree.
---

# task-claim

你正在运行 Feishu-first Multi-Repo Agent Kit 的 `task-claim` workflow。

通用规则：

1. 先读取 workspace 的 `.aiops.json`。
2. 飞书是唯一 PRD/任务池 source of truth。
3. 已有仓库的结构判断必须基于 CodeGraph。
4. 没有 claim 的任务不允许写代码。
5. 每个开发任务只能有一个 primary_repo。
6. 跨仓库任务必须通过 depends_on 串联。
7. 输出必须包含可回写飞书的结构化摘要。

## Workflow-specific procedure


- 解析参数中的 TASK_ID。
- 读取任务，检查 status=ready 且 depends_on 已完成。
- 执行 `aiops claim TASK_ID --owner agent:<repo> --repo <repo> --branch feat/TASK_ID`。
- 如果 owner 已经是 human 或其他人，停止。

## Required final answer

必须输出：

- What I read
- What I decided
- Feishu updates needed/done
- CodeGraph evidence used
- Risks / blockers
- Next task IDs
