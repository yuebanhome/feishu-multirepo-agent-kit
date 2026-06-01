---
description: Review task pool or PR for correctness, evidence, risks, boundaries, tests, and CodeGraph coverage.
---

# task-review

你正在运行 Feishu-first Multi-Repo Agent Kit 的 `task-review` workflow。

通用规则：

1. 先读取 workspace 的 `.aiops.json`。
2. 飞书是唯一 PRD/任务池 source of truth。
3. 已有仓库的结构判断必须基于 CodeGraph。
4. 没有 claim 的任务不允许写代码。
5. 每个开发任务只能有一个 primary_repo。
6. 跨仓库任务必须通过 depends_on 串联。
7. 输出必须包含可回写飞书的结构化摘要。

## Workflow-specific procedure


- 使用 Reviewer Agent。
- 审查任务/PR 是否满足 acceptance criteria、allowed_paths、verification、evidence。
- 检查有没有跨仓库契约遗漏。
- 输出 blocking issues 和 non-blocking suggestions。

## Required final answer

必须输出：

- What I read
- What I decided
- Feishu updates needed/done
- CodeGraph evidence used
- Risks / blockers
- Next task IDs
