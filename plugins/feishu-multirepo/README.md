# feishu-multirepo Claude Code Plugin

This plugin packages reusable Claude Code skills, subagents, and hooks for Feishu-first multi-repo product development.

The plugin itself is project-agnostic. Each workspace supplies `.aiops.json` to define repos, Feishu adapter, CodeGraph policy, and task-pool behavior.

- Source: <https://github.com/yuebanhome/feishu-multirepo-agent-kit>
- Marketplace install:

  ```bash
  claude plugin marketplace add yuebanhome/feishu-multirepo-agent-kit
  claude plugin install feishu-multirepo@aiops-agent-kit --scope user
  ```

See the [top-level README](../../README.md) for full workspace setup, agents, skills, hooks, and Feishu adapter contract.
