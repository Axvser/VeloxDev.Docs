# Workflow Agent — Design Patterns — Patterns Overview

The workflow-agent feature composes classic patterns so an LLM can operate a GUI-bound workflow tree without bypassing its invariants.

| # | Pattern | Where | How it appears |
|---|---|---|---|
| 1 | **Builder** | `WorkflowAgentScope` | Fluent `With*` methods return `this`; the chain materializes prompt + tools (`ProvideProgressiveContextPrompt()` / `ProvideTools()`). |
| 2 | **Facade** | `WorkflowAgentToolkit` | ~60 `AITool`s expose full graph control through one facade, hiding reflection, command dispatch and JSON formatting. |
| 3 | **Decorator** | `TrackedAIFunction` | A `DelegatingAIFunction` wrapper adds UI-thread marshalling, call counting, max-call enforcement, the `ToolCalled` callback and optional auto-dirty. |
| 4 | **Adapter** | `McpScope` | Adapts an external MCP runtime (stdio process or remote HTTP) into `AITool` instances — local install, transport, JSON-RPC handshake, per-server `ServerError` isolation. |
| 5 | **Memento** | `WorkflowStateTracker` | `TakeSnapshot` stores a JSON snapshot; `GetChangesSinceLastSnapshot` computes a property-level diff — the Agent observes change without re-reading full state. |
| 6 | **Command** | mutation + execution tools | Each tool dispatches one component command (`SetAnchorCommand`, `CreateNodeCommand`, `DeleteCommand`, …) and awaits real completion, so the framework undo/redo stack is the single source of truth. |
| 7 | **Observer** | `ToolCalled` / `ServerError` events | `WorkflowAgentScope.ToolCalled` notifies after every tool call; `McpScope.ServerError` notifies a failed server load (the error is not rethrown). |
| 8 | **Strategy** | `WorkflowToolCategory` + interaction handlers | `CreateTools(categories)` selects which tool group to surface; `WithSelectionHandler`/`WithConfirmationHandler` inject the host's interaction strategy and only register the tools when a handler exists and safety level > 0. |

## Capability gates and interaction safety

The tool surface is not limited by prose alone. `WithAllowNodeExecution` gates the node-execution tools (`ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`, `RunCompiledWorkflow`, `GetNodeResult`); `WithAllowedGenericCommands` allowlists the generic command tools; each gated tool returns a structured `{"status":"error"}` when disabled. `WithInteractionSafety(0-3)` decides how eagerly the agent pauses via `RequestSelection` / `RequestConfirmation`, and `ResolveConfirmationAsync` caches `AllowAlways` approvals per `operationKey` for the session (`WorkflowAgentScope.cs`, lines 214-254, 429-442).

## Compiled execution model (Root vs Terminal)

Run/result tools mirror the GUI compile path rather than executing nodes ad hoc:

- `RunCompiledWorkflow` compiles the sub-graph reachable from a start node with `CompileRole.Root` and lets `RuntimeEngine` drive the whole chain (routers select branches via `ICompileTimeRouter`).
- `GetNodeResult` compiles a node's ancestor cone with `CompileRole.Terminal` (reverse compile). Routers inside the cone keep **real** branch semantics: if a router selects a sibling branch at runtime, the target is NOT reached — the tool returns an explicit `error` naming the target (`... was NOT reached ... No result was produced.`) and no data (`WorkflowAgentToolkit.cs`, lines 1789-1801, 1827-1836). A value is never fabricated from a sibling branch.

The agent-facing specification for all of this lives in **bilingual embedded prompt docs** (`Resources/Workflow/{en,zh}/{References,Safety,Skills}/*.md`, loaded by `AgentEmbeddedResources`) — `CommandReference.md`, `CompilerUsage.md`, `Level1-3.md`, etc. — which are injected into the system prompt and are the authoritative description of tool semantics.
