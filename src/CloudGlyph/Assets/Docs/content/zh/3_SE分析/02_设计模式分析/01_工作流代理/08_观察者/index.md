# Workflow Agent — 设计模式 — 观察者

- `WorkflowAgentScope.ToolCalled`（`EventHandler<AgentToolCallEventArgs>`）—— 每次工具调用后触发；作用域还会调用 `WithToolCallCallback` 处理器（`RaiseToolCalledAsync`）。
- `McpScope.ServerError`（`Action<McpServerConfiguration, Exception>`）—— 单服务器加载失败时触发；错误不重抛，一台坏服务器不会中止整批。

> 源码：`WorkflowAgentScope.cs` 第 444-450 行；`McpScope.cs` 第 216-224 行。
