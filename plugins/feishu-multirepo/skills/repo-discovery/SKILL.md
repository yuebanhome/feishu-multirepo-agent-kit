---
description: Use CodeGraph to scan all configured repos, classify participating repos, identify empty repos, and produce repo participation matrix.
---

# repo-discovery

你正在运行 Feishu-first Multi-Repo Agent Kit 的 `repo-discovery` workflow。

通用规则：

1. 先读取 workspace 的 `.aiops.json`。
2. 飞书是唯一 PRD/任务池 source of truth。
3. 已有仓库的结构判断必须基于 CodeGraph。
4. 没有 claim 的任务不允许写代码。
5. 每个开发任务只能有一个 primary_repo。
6. 跨仓库任务必须通过 depends_on 串联。
7. 输出必须包含可回写飞书的结构化摘要。

## Workflow-specific procedure


- 使用 CodeGraph Agent 和 CTO Agent。
- 对 `.aiops.json` 中所有 repo 分类：participates、existing、empty、unrelated。
- 对 existing repo 检查 `.codegraph/` 和 `codegraph status`。
- 空仓库只生成 bootstrap assessment。
- 输出 Repo Participation Matrix 和 CodeGraph Seeds。

## Required final answer

必须输出：

- What I read
- What I decided
- Feishu updates needed/done
- CodeGraph evidence used
- Risks / blockers
- Next task IDs
