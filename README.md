# Feishu Multi-Repo Agent Kit

一个可复用的 Claude Code workflow/plugin 仓库，用来把「飞书 PRD / 任务池 + 多仓库开发 + CodeGraph + Claude Code hooks + Agent 团队」固化成别人本地可安装的流程。

## 设计目标

- 飞书是 PRD、任务池、claim、evidence 的唯一 source of truth。
- CodeGraph 是代码结构、调用链、影响范围的事实层。
- Claude Code plugin 负责分发 skills、agents、hooks。
- workspace 初始化器负责接入每个人本地的六仓库、飞书 CLI、CodeGraph。
- hook 做硬约束：没有 claim 不能写代码；任务被真人领取不能写；写完要回写 evidence。

## 安装方式

### 本地测试安装

```bash
git clone <your-repo-url> feishu-multirepo-agent-kit
cd feishu-multirepo-agent-kit
./install.sh --workspace ~/dev/product-x --scope user
```

这会做三件事：

1. 注册当前 repo 为 Claude Code plugin marketplace。
2. 安装 `feishu-multirepo` 插件。
3. 在 workspace 根目录生成 `.aiops.json`、`.aiops/`、`CLAUDE.md`。

### 团队安装

发布到 GitHub 后，别人可以执行：

```bash
claude plugin marketplace add your-org/feishu-multirepo-agent-kit
claude plugin install feishu-multirepo@aiops-agent-kit --scope user
```

然后在多仓库父目录初始化：

```bash
cd ~/dev/product-x
aiops init
```

如果你的 shell 里没有 `aiops` 命令，可以用插件内脚本：

```bash
python3 ~/.claude/plugins/data/<plugin-id>/../scripts/aiops_cli.py init
```

实际使用时更推荐通过 Claude Code Bash tool 调用 `aiops`，因为插件的 `bin/` 会被加入 Claude Code Bash tool 的 PATH。

## Workspace 结构

```text
~/dev/product-x/
  .aiops.json
  .aiops/
    state/
      tasks.json
      comments.jsonl
      preflight/
  CLAUDE.md
  repo-a/
  repo-b/
  repo-c/
  repo-d/
  repo-e/
  repo-f/
```

`.aiops.json` 是本地配置，主要配置：

- 本地六个 repo 的路径和角色。
- 飞书 adapter 命令。
- CodeGraph 是否强制。
- claim owner 前缀和 hook 策略。

## Slash skills

安装后，Claude Code 中可以使用这些命令：

```text
/feishu-multirepo:prd-intake
/feishu-multirepo:repo-discovery
/feishu-multirepo:solution-design
/feishu-multirepo:taskpool-plan
/feishu-multirepo:task-claim
/feishu-multirepo:task-build
/feishu-multirepo:task-review
/feishu-multirepo:integration-review
/feishu-multirepo:release-closeout
```

## Agents

插件包含：

- `product-agent`
- `cto-agent`
- `codegraph-agent`
- `task-planner-agent`
- `task-guardian-agent`
- `repo-agent`
- `contract-agent`
- `reviewer-agent`
- `qa-agent`
- `release-agent`

## Hooks

默认启用：

- `SessionStart`：注入 workspace、repo、CodeGraph 状态。
- `UserPromptSubmit`：识别任务 ID 并从飞书任务池注入上下文。
- `PreToolUse: Edit|Write|MultiEdit`：没有 claim / 不在 allowed_paths / 没 CodeGraph preflight 就阻止写入。
- `PostToolUse: Edit|Write|MultiEdit`：写入后尝试 `codegraph status`，注入 affected context。
- `Stop`：没有 evidence、PR URL、任务状态更新时阻止结束。

## 飞书 Adapter 规范

你的真实飞书 CLI 只需要适配下面这组命令即可：

```bash
adapter task-get PX-123
adapter task-list --status ready
adapter task-claim PX-123 agent:repo-b repo-b feat/PX-123
adapter task-update PX-123 --status review --evidence evidence.md --pr-url https://...
adapter task-comment PX-123 "message"
adapter prd-get PRD-2026-001
```

所有命令应该返回 JSON。仓库里附带一个文件型 demo adapter，便于本地试跑。

## CodeGraph

每个已有仓库建议先跑：

```bash
cd repo-a && codegraph init -i
cd repo-b && codegraph init -i
cd repo-c && codegraph init -i
cd repo-d && codegraph init -i
```

开发前在 Claude 里执行：

```bash
aiops preflight-ok PX-123
```

表示本任务已经完成 CodeGraph context/search/impact 分析。实际团队可以把这一步做得更严格，例如记录 `codegraph_context` 输出摘要。

## 典型使用

```bash
cd ~/dev/product-x/repo-b
export AIOPS_TASK_ID=PX-123
export FEISHU_TASK_ID=PX-123
claude --worktree PX-123
```

在 Claude Code 中：

```text
/feishu-multirepo:task-build PX-123
```

Repo Agent 会读取飞书任务、确认 claim、完成 CodeGraph preflight、TDD 实现、测试并回写 evidence。

## 生产化建议

- 把 demo adapter 替换成你的飞书 CLI wrapper。
- 把 `.aiops.json` 中的 repos 改成真实仓库。
- 把任务 schema 和飞书多维表字段一一对应。
- 在 CI 中跑 `claude plugin validate .` 和 `claude plugin validate ./plugins/feishu-multirepo`。
- 给发布版本 bump `plugins/feishu-multirepo/.claude-plugin/plugin.json` 的 version。
