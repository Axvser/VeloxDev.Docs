# 工作流代理 —— 设计模式 —— 观察者

agent 层发布状态变化，让宿主无需轮询即可反应：

- **`WorkflowAgentScope.ToolCalled`**（`EventHandler<AgentToolCallEventArgs>`）—— 每次工具调用后触发；作用域还经 `RaiseToolCalledAsync` 调用可选的 `WithToolCallCallback` 处理器。`AgentToolCallEventArgs` 携带工具名、JSON 结果与累计调用数。
- **`McpScope.ServerError`**（`Action<McpServerConfiguration, Exception>`）—— 单服务器加载失败时触发；错误**不会**重新抛出，因此一个坏服务器不会中止整批。
- **`IAgentToolCallNotifier` / `IAgentSelectionNotifier` / `IAgentConfirmationNotifier`** —— 事件与交互交接所经由的通知契约（见 `VeloxDev.Core` 中的 `VeloxDev.AI` 类型）。

> 源码：`WorkflowAgentScope.cs`（`ToolCalled`、`RaiseToolCalledAsync`）；`McpScope.cs`（`ServerError`、失败路径）。

```csharp
internal async Task RaiseToolCalledAsync(string toolName, string result, int callCount)
{
    var args = new AgentToolCallEventArgs(toolName, result, callCount);
    ToolCalled?.Invoke(this, args);
    if (_toolCallHandler is not null)
        await _toolCallHandler(args);
}
```

在示例中，View 订阅 `AgentHelper.ToolCalled`（由建造者链中的工具调用回调接线），在每次 agent 变更后触发一次新的视口虚拟化。
