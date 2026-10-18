# Workflow Agent — Namespace: `VeloxDev.AI.Workflow.Functions`

`WorkflowAgentToolkit` turns a scoped tree into MAF `AITool` instances (full operational control), grouped by `WorkflowToolCategory`; the helper classes `CommandInvoker`, `ComponentPatcher` and `TypeIntrospector` back the command/patch/schema tools. All JSON output is `Formatting.None` (compact) to save tokens; most tools return an object with `status: "ok" | "error" | "rejected"`.

Implemented in `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/`. **Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/*` — tools are invoked through the public `scope.ProvideTools()` registration path) + **Demo** (`AgentHelper.ProvideAgent`).

## WorkflowAgentToolkit

`public sealed class WorkflowAgentToolkit`. Constructed two ways: `WorkflowAgentToolkit(WorkflowAgentScope scope)` for a scope that owns the session allowance, and an `internal` overload taking an `outerLedger` for a scope whose allowance is a share of another's. Each toolkit owns a `WorkflowStateTracker` over the scoped tree and a `ToolCallLedger`.

| Member | Signature | Notes |
|---|---|---|
| `CreateTools` | `IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | The switchable surface: built-ins for `categories`, minus any tool switched off, plus the custom tools. |
| `CreateAllTools` (internal) | `IList<AITool> CreateAllTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | Every tool the toolkit can offer — **unfiltered** by per-tool switches. What a host UI enumerates. |
| `WrapTool` (internal) | `AITool WrapTool(AITool tool)` | Wraps an `AIFunction` with `TrackedAIFunction`; other tools returned as-is. |
| `CreateAccountingStage` (internal) | `IAgentPipelineStage CreateAccountingStage()` | The pipeline stage that counts completed calls, raises the callback and marks dirty. |
| `Ledger` (internal) | `ToolCallLedger { get; }` | This scope's place in the session's call accounting. |

`ResetBudgetToolName` is the `internal const string` `"ResetToolCallLimit"`; `ResetBudgetOperationKey` is `"extend-tool-call-budget"`.

## WorkflowToolCategory

`[Flags] public enum WorkflowToolCategory` — tool-group selector for `CreateTools`.

| Flag | Value | Contains |
|---|---|---|
| `Query` | `1 << 0` | Read-only inspection (**20 tools**). |
| `Mutation` | `1 << 1` | Structural graph edits (**23 tools**). |
| `Execution` | `1 << 2` | Run node business code + the compiled-run family (**12 tools**, gated). |
| `Command` | `1 << 3` | Generic allowlisted command execution (**2 tools**, gated). |
| `Graph` | `1 << 4` | Traversal & path finding (**5 tools**). |
| `Layout` | `1 << 5` | **Reserved — no tools.** Multi-node layout is done node-by-node. |
| `Analytics` | `1 << 6` | `GetNodeStatistics` (**1 tool**). |
| `State` | `1 << 7` | Snapshots & dirty marking (**3 tools**). |
| `Composite` | `1 << 8` | **Reserved — no tools.** Every operation is a single component-command step. |
| `Interaction` | `1 << 9` | `RequestSelection` / `RequestConfirmation` — registered when the matching handler is configured (**up to 2 tools**). `EnterPlanMode` / `ExitPlanMode` are added outside the category mask when a confirmation handler is configured. |
| `All` | all of the above | Every category. |

**Tool count.** The ten categories total **66 unconditional tools** (20 + 23 + 12 + 2 + 5 + 0 + 1 + 3 + 0 = 66; `Layout` and `Composite` contribute none, and the `Execution` and `Command` gates are checked inside each tool body, not by withholding the tool). On top of that:

- the two `Interaction` tools, each only when its handler exists;
- `EnterPlanMode` / `ExitPlanMode`, both only when a confirmation handler exists;
- `ResetToolCallLimit`, always offered regardless of `categories`;
- the tools registered with `WithTools` / `WithQueryTools`;
- every tool contributed by an attached subsystem (MCP / skills / sub-agents).

With both handlers registered, `ProvideTools()` returns **71**: 66 + 2 interaction + 2 plan tools + 1 reset.

**`Layout` and `Composite` are reserved by design:** multi-node layout is done node-by-node via `MoveNode` / `SetNodePosition`, and every operation is a single component-command step, so the framework's undo/redo stack stays the source of truth and is never bypassed or double-submitted.

## Tracking & accounting

Every built-in tool is created through a local `T(Delegate, name, AgentActionCategory)` helper that wraps it in `TrackedAIFunction`. `TrackedAIFunction` (namespace `VeloxDev.AI`, `internal sealed`) marshals the call onto the scope's `SynchronizationContext`, runs it past the `ToolPipeline` (permission refusal + confirmation), and reports `AgentToolCallStarted` / `AgentToolCallCompleted` into the scope's `AgentPipeline`. The category declared on that line is what the permission policy evaluates.

The pre-flight gate `CheckInvocation` runs inside the marshalled block, before the body:

1. a tool switched off via `IsToolEnabled` → `'{toolName}' is disabled by host policy. …`;
2. `ResetToolCallLimit` always passes;
3. a `PermissionDecision.Deny` from `PermissionPolicy.Evaluate(invocation)` → the mode/rule refusal;
4. for a child scope, the root's ceiling (`The session's tool-call budget (N) is spent.`);
5. this scope's own `MaxToolCalls`;
6. `MaxWriteToolCalls` (non-query) / `MaxReadToolCalls` (query).

A refusal never reaches the body and never counts. A `Succeeded` call is counted by `AccountingStage` → `AccountAsync`, which also raises the callback and marks dirty when `AutoMarkDirty` is on and the tool is not a query.

`QueryToolNames` is the read-only classification: the 20 Query tools, `TakeSnapshot` / `GetChangesSinceSnapshot`, `GetNodeStatistics`, the five Graph tools, `RequestSelection` / `RequestConfirmation`, `ResetToolCallLimit`, `CompileWorkflow` / `CompileNodeResult` / `GetCompileStatus` / `GetExecutionLog`, plus every name in `SkillAgentToolkit.ToolNames` and `SubAgentAgentToolkit.ToolNames`. `EnterPlanMode` / `ExitPlanMode` are deliberately absent from that list, so a plan-mode switch spends the write budget.

## Tool inventory

| Page | Category | Tools |
|---|---|---|
| [00 · Query & State tools](00_query-state-tools/index.md) | Query + State | 20 + 3 |
| [01 · Mutation tools](01_mutation-tools/index.md) | Mutation | 23 |
| [02 · Execution tools](02_execution-tools/index.md) | Execution | 12 (incl. the run-handle family) |
| [03 · Command, Graph, Analytics & Interaction tools](03_command-graph-analytics-interaction/index.md) | Command + Graph + Analytics + Interaction | 2 + 5 + 1 + up to 4 |
| [04 · Helper classes](04_helpers/index.md) | — | `CommandInvoker`, `ComponentPatcher`, `TypeIntrospector` |
