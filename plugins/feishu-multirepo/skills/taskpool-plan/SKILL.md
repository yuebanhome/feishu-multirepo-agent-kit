---
description: Convert PRD, Product Brief, CTO design, and CodeGraph repo maps into Feishu task pool entries.
---

# taskpool-plan

你正在运行 Feishu-first Multi-Repo Agent Kit 的 `taskpool-plan` workflow。

通用规则：

1. 先读取 workspace 的 `.aiops.json`。
2. 飞书是唯一 PRD/任务池 source of truth。
3. 已有仓库的结构判断必须基于 CodeGraph。
4. 没有 claim 的任务不允许写代码。
5. 每个开发任务只能有一个 primary_repo。
6. 跨仓库任务必须通过 depends_on 串联。
7. 输出必须包含可回写飞书的结构化摘要。

## Workflow-specific procedure


- 使用 Task Planner Agent。
- 每个任务必须包含：task_id、title、status、primary_repo、related_repos、allowed_paths、forbidden_paths、depends_on、acceptance_criteria、verification、codegraph_seeds。
- 模糊任务保持 draft。
- 跨仓库任务拆成多个单仓库任务。
- 写入飞书任务池。

## Required final answer

必须输出：

- What I read
- What I decided
- Feishu updates needed/done
- CodeGraph evidence used
- Risks / blockers
- Next task IDs
