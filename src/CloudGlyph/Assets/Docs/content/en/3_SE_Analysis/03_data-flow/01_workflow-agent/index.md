# Data Flow — Workflow Agent

The workflow-agent feature operates a GUI workflow tree through ~60 `AITool`s and, for its compiled run/result tools, reuses the GUI's own `CompilerEx` model (`CompilerViewModel.CompileAsync` + `RuntimeEngine`). Each page below traces one sequence flow with PlantUML, covering the normal path and its error/async branches.

| # | Flow | Page |
|---|---|---|
| 1 | Tool call → tracked wrapper → one component command → framework undo stack; state snapshot/diff | [Agent tool call](00_agent-tool-call/index.md) |
| 2 | `RequestSelection` / `RequestConfirmation` interaction handoff to the host UI | [Interaction & confirmation](01_interaction-and-confirmation/index.md) |
| 3 | MCP server load: runtime install → transport → JSON-RPC handshake → `AITool[]`; per-server error isolation | [MCP server load](02_mcp-server-load/index.md) |
| 4 | `RunCompiledWorkflow`: `CompileRole.Root` compile + `RuntimeEngine` drives the whole chain | [Root chain run](03_root-run-execution/index.md) |
| 5 | `GetNodeResult`: `CompileRole.Terminal` reverse-compile of an ancestor cone + the "NOT reached" error contract | [Terminal result](04_terminal-result-execution/index.md) |
| 6 | A tool throws → JSON error result → Failure Handling Protocol (no silent retry loop) | [Error & recovery](05_error-and-recovery/index.md) |

All results are compact JSON (`Formatting.None`). Tools never bypass the component command/lifecycle pipeline: mutations go through `IWorkflow*ViewModel` commands so Core's undo/redo stack stays the single source of truth.

- Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, `.../Workflow/WorkflowAgentScope.cs`, `.../Workflow/WorkflowStateTracker.cs`, `.../Agent/MCP/McpScope.cs`.
