# Feishu Multi-Repo Agent Kit

一个可复用的 Claude Code workflow/plugin 仓库，用来把「飞书 PRD / 任务池 + 多仓库开发 + CodeGraph + Claude Code hooks + Agent 团队」固化成别人本地可安装的流程。

## 设计目标

- 飞书是 PRD、任务池、claim、evidence 的唯一 source of truth。
- CodeGraph 是代码结构、调用链、影响范围的事实层。
- Claude Code plugin 负责分发 skills、agents、hooks。
- workspace 初始化器负责接入每个人本地的六仓库、飞书 CLI、CodeGraph。
- hook 做硬约束：没有 claim 不能写代码；任务被真人领取不能写；写完要回写 evidence。

## 仓库地址

- GitHub: <https://github.com/yuebanhome/feishu-multirepo-agent-kit>
- Clone: `git@github.com:yuebanhome/feishu-multirepo-agent-kit.git` 或 `https://github.com/yuebanhome/feishu-multirepo-agent-kit.git`

## 前置依赖

这套工作流依赖两个外部 CLI，建议在安装 plugin 前先准备好。

### 1. Claude Code

参见 <https://docs.claude.com/en/docs/claude-code>。需要能在命令行执行 `claude` 命令。

### 2. 飞书 CLI（larksuite-cli）

用来跑 PRD、任务池、claim、evidence 这条飞书侧的链路。官方安装方式：

```bash
# 安装 / 升级
npx @larksuite/cli@latest install

# 登录（首次使用）
npx @larksuite/cli@latest auth login
```

安装后命令通常以 `lark-cli` 暴露（或继续用 `npx @larksuite/cli`）。把它包成飞书 adapter，见下面「飞书 Adapter 规范」一节。

> 如果你已经有内部包装好的飞书 CLI（不是 larksuite-cli），直接让它对齐 adapter 接口即可，不强制使用 larksuite-cli。

### 3. CodeGraph

用于代码结构、调用链、影响范围分析；hooks 会在写代码前要求做 preflight。安装：

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# Windows (PowerShell)
irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
```

装完后在每个已有仓库里跑一次 `codegraph init -i`，详情见下方「CodeGraph」一节。

## 安装方式

### 本地测试安装

```bash
git clone https://github.com/yuebanhome/feishu-multirepo-agent-kit.git
cd feishu-multirepo-agent-kit
./install.sh --workspace ~/dev/product-x --scope user
```

这会做三件事：

1. 注册当前 repo 为 Claude Code plugin marketplace。
2. 安装 `feishu-multirepo` 插件。
3. 在 workspace 根目录生成 `.aiops.json`、`.aiops/`、`CLAUDE.md`。

### 团队安装（推荐）

直接从 GitHub 注册 marketplace 并安装插件：

```bash
claude plugin marketplace add yuebanhome/feishu-multirepo-agent-kit
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

> 先确保安装并登录飞书 CLI：`npx @larksuite/cli@latest install` → `npx @larksuite/cli@latest auth login`。

你的真实飞书 CLI（larksuite-cli 或内部 wrapper）只需要适配下面这组命令即可：

```bash
adapter task-get PX-123
adapter task-list --status ready
adapter task-claim PX-123 agent:repo-b repo-b feat/PX-123
adapter task-update PX-123 --status review --evidence evidence.md --pr-url https://...
adapter task-comment PX-123 "message"
adapter prd-get PRD-2026-001
```

所有命令应该返回 JSON。仓库里附带一个文件型 demo adapter（`plugins/feishu-multirepo/scripts/demo_feishu_adapter.py`），便于本地试跑；接好真实 CLI 后，把 `.aiops.json` 里的 `feishu.adapter_command` 改成你的 wrapper 即可（参考 `examples/real-feishu-adapter.sh`）。

## CodeGraph

先确认本机已安装 CodeGraph（见上方「前置依赖」）。验证：

```bash
codegraph --version
```

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
