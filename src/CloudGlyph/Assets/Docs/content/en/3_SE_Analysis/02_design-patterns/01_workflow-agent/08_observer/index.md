# Workflow Agent — Design Patterns — Observer

- `WorkflowAgentScope.ToolCalled` (`EventHandler<AgentToolCallEventArgs>`) — raised after each tool call; the scope also invokes the `WithToolCallCallback` handler (`RaiseToolCalledAsync`).
- `McpScope.ServerError` (`Action<McpServerConfiguration, Exception>`) — raised on per-server load failure; the error is not rethrown so one bad server does not abort the batch.

> Source: `WorkflowAgentScope.cs` lines 444-450; `McpScope.cs` lines 216-224.
