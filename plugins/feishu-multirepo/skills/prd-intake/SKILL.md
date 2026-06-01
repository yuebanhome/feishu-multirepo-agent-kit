---
description: Read Feishu PRD, produce Product Brief, user stories, non-goals, acceptance criteria, open questions, and update Feishu.
---

# prd-intake

你正在运行 Feishu-first Multi-Repo Agent Kit 的 `prd-intake` workflow。

通用规则：

1. 先读取 workspace 的 `.aiops.json`。
2. 飞书是唯一 PRD/任务池 source of truth。
3. 已有仓库的结构判断必须基于 CodeGraph。
4. 没有 claim 的任务不允许写代码。
5. 每个开发任务只能有一个 primary_repo。
6. 跨仓库任务必须通过 depends_on 串联。
7. 输出必须包含可回写飞书的结构化摘要。

## Workflow-specific procedure


- 使用 Product Agent。
- 读取 PRD：`aiops` 或飞书 adapter 的 `prd-get`。
- 提取背景、目标、用户、场景、非目标、验收标准、开放问题。
- 不要创建 ready 开发任务；这里只形成 Product Brief 和任务规划线索。
- 回写飞书 PRD 的 Agent Summary / Open Questions 区。

## Required final answer

必须输出：

- What I read
- What I decided
- Feishu updates needed/done
- CodeGraph evidence used
- Risks / blockers
- Next task IDs
