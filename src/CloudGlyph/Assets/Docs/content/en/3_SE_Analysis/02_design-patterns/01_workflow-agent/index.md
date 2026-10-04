# Design Patterns — Workflow Agent

The **workflow-agent** feature lets an LLM operate a live `IWorkflowTreeViewModel` through `Microsoft.Extensions.AI` tools. Its pattern surface is a fluent **builder** (`WorkflowAgentScope`), a **facade** of 68 `AITool`s (`WorkflowAgentToolkit`), a **decorator** (`TrackedAIFunction`) that wraps every tool, a **memento** (`WorkflowStateTracker`) for JSON snapshots/diffs, a **command** layer that dispatches the very same component commands the GUI uses (so the framework undo/redo stack stays the single source of truth), an **adapter** to remote/local MCP runtimes (`McpScope`), **observer** events, and **strategy**-selected tool categories (`WorkflowToolCategory`).

Two more structures carry the subsystem layer:

- A **chain-of-responsibility** pipeline (`AgentPipeline` → `TextPipeline` / `ToolPipeline` / accounting stage) every run and tool call flows through, with a **gated decorator** (`ToolPipeline.Refuse` / `Confirm`) that reaches every slice — built-ins, MCP, skills and sub-agents alike.
- A **narrowed-view** family: a sub-agent spawn, a granted skill set and a granted MCP server set are all *filtered views* of the parent rather than tool-name lists, because a capability that carries the ability to reconfigure it cannot be expressed as a list of names.

The execution tools behind run/result (`RunCompiledWorkflow`, `GetNodeResult`, and the run-handle family) mirror the GUI compile path: `CompilerViewModel.CompileAsync(node, CompileRole{Root,Terminal})` drives a `RuntimeEngine`, and routers stay real (a sibling-branch selection means the target is NOT reached — no fabricated value). Security is enforced by capability gates in code (`WithAllowNodeExecution`, `WithAllowedGenericCommands`, `WithToolApproval`), not by prompt prose.

## Pages

- [00 · Class Diagram](00_class-diagram/index.md) — the scope and its collaborators
- [01 · Patterns Overview](01_patterns-overview/index.md) — every pattern in one table
- [02 · Builder](02_builder/index.md) — fluent `With*` configuration on `WorkflowAgentScope`
- [03 · Facade](03_facade/index.md) — one tool surface hides reflection, command dispatch and JSON
- [04 · Decorator](04_decorator/index.md) — `TrackedAIFunction` wraps every `AIFunction`
- [05 · Adapter](05_adapter/index.md) — MCP servers (stdio/HTTP) exposed as `AITool`s
- [06 · Memento](06_memento/index.md) — `WorkflowStateTracker` JSON snapshot + property-level diff
- [07 · Command](07_command/index.md) — mutation tools dispatch one component command each
- [08 · Observer](08_observer/index.md) — the pipeline events and the notifier interfaces
- [09 · Strategy](09_strategy/index.md) — `WorkflowToolCategory` flags + interaction handlers
- [10 · Sub-Agent Capability Narrowing](10_sub-agent-narrowing/index.md) — why a spawn hands down a narrowed *view* rather than a tool-name list
- [11 · Sub-Agent Tree & Consumption Metering](11_sub-agent-tree-and-consumption/index.md) — flat rosters projected into one tree, upward call accounting vs. bottom-up token aggregation, and the rebuild gate
- [12 · Tool-Category Hierarchy](12_tool-category-hierarchy/index.md) — the `WorkflowToolCategory` flags and the ten tool groups, with the two reserved ones
