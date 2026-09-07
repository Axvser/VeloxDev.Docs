# Workflow Agent — Design Patterns — Observer

The agent layer publishes state changes so hosts can react without polling:

- **`WorkflowAgentScope.ToolCalled`** (`EventHandler<AgentToolCallEventArgs>`) — raised after every tool call; the scope also invokes the optional `WithToolCallCallback` handler through `RaiseToolCalledAsync`. `AgentToolCallEventArgs` carries the tool name, the JSON result and the cumulative call count.
- **`McpScope.ServerError`** (`Action<McpServerConfiguration, Exception>`) — raised on a per-server load failure; the error is **not** rethrown, so one bad server does not abort the batch.
- **`IAgentToolCallNotifier` / `IAgentSelectionNotifier` / `IAgentConfirmationNotifier`** — the notifier contracts that the events and interaction handoffs are expressed through (see the `VeloxDev.AI` types in `VeloxDev.Core`).

> Source: `WorkflowAgentScope.cs`, lines 24 and 444-450 (`ToolCalled`, `RaiseToolCalledAsync`); `McpScope.cs`, lines 35-38 and 220-229 (`ServerError`, failure path).

```csharp
internal async Task RaiseToolCalledAsync(string toolName, string result, int callCount)
{
    var args = new AgentToolCallEventArgs(toolName, result, callCount);
    ToolCalled?.Invoke(this, args);
    if (_toolCallHandler is not null)
        await _toolCallHandler(args);
}
```

In the demo, the View subscribes to `AgentHelper.ToolCalled` (wired from the tool-call callback in the builder chain) to trigger a fresh viewport virtualization after each agent mutation.
