# Workflow Agent — 设计模式 — Patterns Overview

| # | 模式 | 位置 | 如何体现 |
|---|---|---|---|
| 1 | **构建者** | `WorkflowAgentScope` | 流式 `With*` 方法返回 `this`；链末端物化为提示词与工具（`ProvideProgressiveContextPrompt()` / `ProvideTools()`）。 |
| 2 | **门面** | `WorkflowAgentToolkit` | 约 60 个 `AITool` 通过一个门面暴露完整的图控制，隐藏反射、命令派发与 JSON 格式化。 |
| 3 | **装饰器** | `TrackedAIFunction` | 一个 `DelegatingAIFunction` 包装器加入 UI 线程 marshal、调用计数、最大调用强制、`ToolCalled` 回调与可选自动置脏。 |
| 4 | **适配器** | `McpScope` | 把外部 MCP 服务器（stdio 进程或远程 HTTP）适配成 `AITool` 实例（`StdioClientTransport` + 经 CliWrap 的 CLI 安装）。 |
| 5 | **备忘录** | `WorkflowStateTracker` | `TakeSnapshot` 存储 JSON 快照；`GetChangesSinceLastSnapshot` 计算属性级差异 —— Agent 无需重读完整状态即可观察变化。 |
| 6 | **命令** | 工具包变更工具 | 每个变更工具恰好派发一个组件命令（`SetAnchorCommand`、`CreateNodeCommand`、`DeleteCommand`、……），让框架撤销/重做栈保持唯一真相源。 |
| 7 | **观察者** | `ToolCalled` / `ServerError` 事件 | `WorkflowAgentScope.ToolCalled` 在每次工具调用后通知；`McpScope.ServerError` 通知服务器加载失败（错误不重抛）。 |
| 8 | **策略** | `WorkflowToolCategory` + 处理器 | `CreateTools(categories)` 选择暴露哪些工具组；`WithSelectionHandler`/`WithConfirmationHandler` 注入宿主的交互策略。 |
