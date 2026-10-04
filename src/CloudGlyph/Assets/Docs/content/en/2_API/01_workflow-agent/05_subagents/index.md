# Workflow Agent — API: Sub-Agents

The `VeloxDev.AI.SubAgents` namespace (implemented in `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/`) lets an agent dispatch **background child agents**, each handed a narrowed slice of its dispatcher's capabilities. Seven public types make the surface: the subsystem itself and its context provider, the Agent-facing toolkit, the state/summary pair, and the two tree view-models.

Entry point: `SubAgentScope.ForClient(chatClient)` → `workflowScope.WithSubAgents(subAgents)`. From there the model reaches the subsystem through five tools (`SpawnSubAgent`, `WaitSubAgents`, `GetSubAgentResult`, `ListSubAgents`, `CancelSubAgent`).

**Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/*` — nine `[TestClass]` files, the primary source for every claim on these pages) + **Demo** (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` lines 306-307, plus the Avalonia sub-agent tree panel under `Examples/Workflow/Avalonia/Demo/Views/Workflow/`). Where a member's behavior is inferred from source rather than exercised by a test it is marked *inferred*.

## API — Sections

- [subagentscope](00_subagentscope/index.md) — `SubAgentScope`: construction, spawn budgeting (`SpawnBudget`, `WithSpawnBudget`), depth (`MaxDepth`, `WithSubAgentDepth`), roster (`Children`, `Snapshot`, `Version`, `Changed`), disposal.
- [toolkit-and-provider](01_toolkit-and-provider/index.md) — `SubAgentAgentToolkit` (the five `AITool`s, `ToolNames`, the three `CreateTools` overloads) and `SubAgentAgentContextProvider` (per-turn instructions + tools, `StateKeys`).
- [state-and-rows](02_state-and-rows/index.md) — `SubAgentState`, the immutable `SubAgentSummary` (thread-safe snapshot) and the bindable `SubAgentStatusViewModel` row.
- [tree](03_tree/index.md) — `SubAgentTreeNodeViewModel` and `SubAgentTreeViewModel`: the projection of the per-scope rosters into one tree, with duration, token and subtree aggregates.

## Integration members on `WorkflowAgentScope`

The subsystem is reached from the workflow feature's own scope (`VeloxDev.AI.Workflow`), whose sub-agent-related members are:

| Member | Signature | Notes |
|---|---|---|
| `SubAgents` | `SubAgentScope? { get; }` | `null` until `WithSubAgents` attaches one. |
| `WithSubAgents` | `WorkflowAgentScope WithSubAgents(SubAgentScope)` | Attaches the subsystem, calls `SubAgentScope.Attach(this)`, forwards the UI `SynchronizationContext`, and registers the subsystem's provider composed with this scope's `ToolPipeline`. Throws `ArgumentNullException` on `null`. |
| `AllowNodeExecution` | `bool { get; }` — **internal** | Read by a spawn to decide whether node execution can be handed down. Internal, so tests reach it through `InternalsVisibleTo`. |
| `MaxReadToolCalls` / `MaxWriteToolCalls` | `int? { get; }` — **internal** | The read/write caps a spawn clamps against; inherited by a child when the request is silent. |
| `GrantInteractionTo` | `void GrantInteractionTo(WorkflowAgentScope child)` — **internal** | Copies the interaction safety level, its per-level prompt overrides, and both handlers onto a spawned child. |
| `GrantCustomToolsTo` | `void GrantCustomToolsTo(WorkflowAgentScope child, IReadOnlyCollection<string> granted)` — **internal** | Re-registers the granted subset of this scope's custom tool **groups**, guidance included. |
| `ParentLedger` | `ToolCallLedger? { get; set; }` — **internal** | The outer ledger a spawned scope chains to, so its calls are counted at the root. Read by `CreateToolkit()`. |

The three capability sources a spawn narrows against are the parent scope's own subsystems: `Skills` (`SkillScope`, narrowed through its internal `GrantableNames` / `CreateNarrowed`), `Mcp` (`McpScope`, narrowed through its internal `GrantableNames` / `CreateGrantedView`), and the tool switches `IsToolEnabled` / `WithToolEnabled` / `SetToolEnabled` / `DisabledToolNames`.

> Source: `WorkflowAgentScope.cs` lines 251-296 (grant helpers), 1514-1526 (ledger + toolkit), 1581 (`SubAgents`), 1788-1804 (`WithSubAgents` body); `SkillScope.cs` lines 353-378 (`GrantableNames` / `CreateNarrowed`); `McpScope.cs` lines 429-500 (`GrantableNames` / `CreateGrantedView`).
