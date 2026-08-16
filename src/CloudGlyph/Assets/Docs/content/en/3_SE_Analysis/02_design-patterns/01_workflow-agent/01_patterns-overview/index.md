# Workflow Agent — Design Patterns — Patterns Overview

| # | Pattern | Where | How |
|---|---|---|---|
| 1 | **Builder** | `WorkflowAgentScope` | Fluent `With*` methods return `this`; the chain materializes prompt + tools (`ProvideProgressiveContextPrompt()` / `ProvideTools()`). |
| 2 | **Facade** | `WorkflowAgentToolkit` | About 60 `AITool`s expose full graph control through one facade, hiding reflection, command dispatch and JSON formatting. |
| 3 | **Decorator** | `TrackedAIFunction` | A `DelegatingAIFunction` wrapper adds UI-thread marshalling, call counting, max-call enforcement, the `ToolCalled` callback and optional auto-dirty. |
| 4 | **Adapter** | `McpScope` | Adapts an external MCP server (stdio process or remote HTTP) into `AITool` instances (`StdioClientTransport` + CLI install via CliWrap). |
| 5 | **Memento** | `WorkflowStateTracker` | `TakeSnapshot` stores a JSON snapshot; `GetChangesSinceLastSnapshot` computes a property-level diff — the Agent observes change without re-reading full state. |
| 6 | **Command** | toolkit mutation tools | Each mutation tool dispatches exactly one component command (`SetAnchorCommand`, `CreateNodeCommand`, `DeleteCommand`, …), keeping the framework undo/redo stack the single source of truth. |
| 7 | **Observer** | `ToolCalled` / `ServerError` events | `WorkflowAgentScope.ToolCalled` notifies after every tool call; `McpScope.ServerError` notifies a failed server load (the error is not rethrown). |
| 8 | **Strategy** | `WorkflowToolCategory` + handlers | `CreateTools(categories)` selects which tool group to surface; `WithSelectionHandler`/`WithConfirmationHandler` inject the host's interaction strategy. |
