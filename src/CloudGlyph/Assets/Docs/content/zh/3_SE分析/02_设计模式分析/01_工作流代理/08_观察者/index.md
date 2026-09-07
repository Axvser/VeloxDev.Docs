# Workflow Agent — 设计模式 — 观察者

代理层发布状态变化，使宿主无需轮询即可响应：

- **`WorkflowAgentScope.ToolCalled`**（`EventHandler<AgentToolCallEventArgs>`）—— 每次工具调用后触发；作用域还会通过 `RaiseToolCalledAsync` 调用可选的 `WithToolCallCallback` 处理器。`AgentToolCallEventArgs` 携带工具名、JSON 结果与累计调用次数。
- **`McpScope.ServerError`**（`Action<McpServerConfiguration, Exception>`）—— 单服务器加载失败时触发；错误**不**重抛，一台坏服务器不会中止整批。
- **`IAgentToolCallNotifier` / `IAgentSelectionNotifier` / `IAgentConfirmationNotifier`** —— 事件与交互交接所依托的通知者契约（见 `VeloxDev.Core` 中的 `VeloxDev.AI` 类型）。

> 源码：`WorkflowAgentScope.cs`，第 24 与 444-450 行（`ToolCalled`、`RaiseToolCalledAsync`）；`McpScope.cs`，第 35-38 与 220-229 行（`ServerError`、失败路径）。

```csharp
internal async Task RaiseToolCalledAsync(string toolName, string result, int callCount)
{
    var args = new AgentToolCallEventArgs(toolName, result, callCount);
    ToolCalled?.Invoke(this, args);
    if (_toolCallHandler is not null)
        await _toolCallHandler(args);
}
```

Demo 中，View 订阅 `AgentHelper.ToolCalled`（从构建链中的工具回调接出），以便每次 agent 变更后用新视口触发虚拟化刷新。
