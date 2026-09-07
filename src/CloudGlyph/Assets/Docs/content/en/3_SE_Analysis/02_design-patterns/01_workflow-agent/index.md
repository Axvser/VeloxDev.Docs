# Design Patterns — Workflow Agent

The **workflow-agent** feature lets an LLM operate a live `IWorkflowTreeViewModel` through `Microsoft.Extensions.AI` tools. Its pattern surface is a fluent **builder** (`WorkflowAgentScope`), a **facade** of ~60 `AITool`s (`WorkflowAgentToolkit`), a **decorator** (`TrackedAIFunction`) that wraps every tool, a **memento** (`WorkflowStateTracker`) for JSON snapshots/diffs, a **command** layer that dispatches the very same component commands the GUI uses (so the framework undo/redo stack stays the single source of truth), an **adapter** to remote/local MCP runtimes (`McpScope`), **observer** events, and **strategy**-selected tool categories.

The execution tools behind run/result (`RunCompiledWorkflow`, `GetNodeResult`) mirror the GUI compile path: `CompilerViewModel.CompileAsync(node, CompileRole{Root,Terminal})` drives a `RuntimeEngine`, and routers stay real (a sibling-branch selection means the target is NOT reached — no fabricated value). Security is enforced by capability gates in code (`WithAllowNodeExecution`, `WithAllowedGenericCommands`), not by prompt prose.

## Pages

- [00 · Class Diagram](00_class-diagram/index.md) — agent scope / toolkit / state tracker / MCP + compile-execution classes
- [01 · Patterns Overview](01_patterns-overview/index.md) — all eight patterns in one table
- [02 · Builder](02_builder/index.md) — fluent `With*` configuration on `WorkflowAgentScope`
- [03 · Facade](03_facade/index.md) — one tool surface hides reflection, command dispatch and JSON
- [04 · Decorator](04_decorator/index.md) — `TrackedAIFunction` wraps every `AIFunction`
- [05 · Adapter](05_adapter/index.md) — MCP servers (stdio/HTTP) exposed as `AITool`s
- [06 · Memento](06_memento/index.md) — `WorkflowStateTracker` JSON snapshot + property-level diff
- [07 · Command](07_command/index.md) — mutation tools dispatch one component command each
- [08 · Observer](08_observer/index.md) — `ToolCalled` / `ServerError` events
- [09 · Strategy](09_strategy/index.md) — `WorkflowToolCategory` flags + interaction handlers
