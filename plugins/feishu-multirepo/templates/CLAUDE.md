# Feishu-first Multi-Repo Agent Team Rules

1. 飞书是唯一 PRD 和任务池 source of truth。
2. 没有 claim 的任务，任何 Agent 不准写代码。
3. 任务被 human owner 领取后，Agent 必须停止。
4. 每个开发任务只能有一个 primary_repo。
5. 跨仓库开发必须拆任务，用 depends_on 串联。
6. 已有仓库开发前必须使用 CodeGraph 做 context / search / callers / callees / impact。
7. 空仓库只能先建 bootstrap task，不能直接业务开发。
8. 每个任务完成必须回写 evidence：改动文件、测试命令、测试结果、PR、风险。
9. Claude Code hooks 是强制规则层，不要绕过。
10. 如果 CodeGraph 显示索引 stale 或 pending sync，必须直接读取相关文件确认最新内容。
