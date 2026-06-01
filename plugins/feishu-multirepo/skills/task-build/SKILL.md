---
description: Implement a claimed task in one primary repo with CodeGraph preflight, TDD, verification, and evidence update.
---

# task-build

你正在运行 Feishu-first Multi-Repo Agent Kit 的 `task-build` workflow。

通用规则：

1. 先读取 workspace 的 `.aiops.json`。
2. 飞书是唯一 PRD/任务池 source of truth。
3. 已有仓库的结构判断必须基于 CodeGraph。
4. 没有 claim 的任务不允许写代码。
5. 每个开发任务只能有一个 primary_repo。
6. 跨仓库任务必须通过 depends_on 串联。
7. 输出必须包含可回写飞书的结构化摘要。

## Workflow-specific procedure


- 解析 TASK_ID。
- 读取飞书任务，确认 status 和 owner。
- 确认当前 repo 是 primary_repo。
- 用 CodeGraph 分析 codegraph_seeds：context/search/callers/callees/impact。
- 运行 `aiops preflight-ok TASK_ID`。
- 先写测试，再写实现，再跑 verification。
- 用 `aiops update TASK_ID --status review --evidence "..." --pr-url "..."` 回写。

## Required final answer

必须输出：

- What I read
- What I decided
- Feishu updates needed/done
- CodeGraph evidence used
- Risks / blockers
- Next task IDs
