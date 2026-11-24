# WorkflowAgentToolkit

`VeloxDev.AI.Workflow.Functions.WorkflowAgentToolkit` provides the MAF-compatible `AITool` instances that give an agent operational control over one `WorkflowAgentScope` tree. Reach it through `scope.CreateToolkit()`; there is one instance per scope because it owns the call ledger and snapshot history.

## Class: WorkflowAgentToolkit

| Member | Signature | Description |
|---|---|---|
| Constructor | `WorkflowAgentToolkit(WorkflowAgentScope scope)` | Creates a toolkit for a scope that owns the session's tool-call allowance. |
| CreateTools | `IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | Returns the built-in tools for the selected groups plus every custom tool, omitting tools switched off with `WithToolEnabled`. |

Every built-in tool is an `AIFunction` wrapped in a tracked function, so a call is marshalled to the scope's context, charged to the budget, reported through `ToolCalled`, and — when enabled — marks the tree dirty. A custom tool that is not an `AIFunction` is added as-is and receives none of that.

`CreateTools` is the single point that decides what reaches the model. A tool switched off is omitted whichever category was asked for, so a switch cannot be honoured on one path and ignored on another.

## Enum: WorkflowToolCategory

A `[Flags]` enum in `VeloxDev.AI.Workflow.Functions`. It is a **surface filter** — which groups are sent to the model — and is never consulted at call time. Call-time permission is a separate classification, `AgentActionCategory` in [Agent Safety and Budgets](../../18_agent-safety-budgets/index.md).

| Member | Value | Registers |
|---|---|---|
| `Query` | `1 << 0` | read-only inspection |
| `Mutation` | `1 << 1` | structural graph edits |
| `Execution` | `1 << 2` | node and chain execution |
| `Command` | `1 << 3` | generic command invocation |
| `Graph` | `1 << 4` | traversal and path queries |
| `Layout` | `1 << 5` | layout inspection, preview and apply |
| `Analytics` | `1 << 6` | node statistics |
| `State` | `1 << 7` | snapshot, diff and dirty marking |
| `Composite` | `1 << 8` | reserved; registers no tools |
| `Interaction` | `1 << 9` | selection, confirmation and mode transitions |
| `All` | union of all flags | every group |

## Tool catalogue

The tables below list the tool names as the model sees them. Their signatures are model-facing JSON schemas, not C# signatures; the Quick Start shows live calls.

### Query

`ListNodes`, `GetNodeDetail`, `GetNodeDetailById`, `ListConnections`, `GetTypeSchema`, `GetWorkflowSummary`, `GetComponentContext`, `ListComponentCommands`, `FindNodes`, `ResolveSlotId`, `ListSlotProperties`, `GetEnumSlotByValue`, `GetLinkDetail`, `ListCreatableTypes`, `ValidateWorkflow`, `GetFullTopology`, `CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus`, `GetExecutionLog`, `SerializeWorkflow`, `LocateNode`, `LocateSlot`, `LocateLink`, `ListCompiledRuns`

### Mutation

`MoveNode`, `SetNodePosition`, `ResizeNode`, `DeleteNode`, `DeleteSlot`, `ConnectSlots`, `ConnectSlotsById`, `ConnectByProperty`, `DisconnectSlots`, `DisconnectSlotsById`, `SetSlotChannel`, `SetEnumSlotChannel`, `ConnectEnumSlot`, `PatchNodeProperties`, `PatchComponentById`, `CreateNode`, `CreateSlotOnNode`, `AddSlotToCollection`, `RemoveSlotFromCollection`, `SetEnumSlotCollection`, `Undo`, `Redo`, `ClearHistory`, `LoadWorkflow`, `ClearFinishedRuns`

Each mutation tool performs exactly one component command, so the Core undo/redo stack stays the source of truth. There are no bundled multi-step gestures.

### Execution

`ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`, `RunCompiledWorkflow`, `GetNodeResult`, `StartCompiledWorkflow`, `ContinueCompiledWorkflow`, `GetCompiledRunStatus`, `PauseCompiledRun`, `ResumeCompiledRun`, `StopCompiledRun`

The node-execution tools (`ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`) run arbitrary business code and are refused until `WithAllowNodeExecution(true)`.

### Command

`ExecuteCommandOnNode`, `ExecuteCommandById`

Refused until `WithAllowedGenericCommands(...)` names the commands the model may invoke.

### Graph

`SearchForward`, `SearchReverse`, `SearchAllRelative`, `IsConnected`, `FindPath`

### Layout

`GetLayoutInfo`, `PreviewLayout`, `ArrangeLayout`

`PreviewLayout` uses the registered `IWorkflowLayoutSolver` in dry-run mode; `ArrangeLayout` applies it through the same path the GUI uses.

### Analytics

`GetNodeStatistics`

### State

`TakeSnapshot`, `GetChangesSinceSnapshot`, `MarkDirty`

### Interaction

| Tool | Registered when |
|---|---|
| `RequestSelection` | `WithSelectionHandler` was given a handler |
| `RequestConfirmation` | `WithConfirmationHandler` was given a handler |
| `EnterPlanMode`, `ExitPlanMode` | a confirmation handler exists |

Interaction tools are never blocked by the permission mode. Asking is how a plan gets agreed to, so a mode that removed them would leave the agent able only to refuse.

### Always offered

`ResetToolCallLimit` is registered in every mode and is never filtered by `WithToolEnabled`. It is the host's way out of a call budget; hiding it exactly when the budget runs out would make it useless.

## Example

```csharp
using VeloxDev.AI.Workflow.Functions;

var toolkit = scope.CreateToolkit();
foreach (var tool in toolkit.CreateTools(WorkflowToolCategory.Query))
    Console.WriteLine(tool.Name);
```

This prints the 25 query tool names in registration order.

## Related

- [WorkflowAgentScope](../00_workflow-agent-scope/index.md) — the scope that owns the toolkit.
- [Agent Safety and Budgets](../../18_agent-safety-budgets/index.md) — `AgentActionCategory` and the call-time gate.
- [Workflow Agent Tools quick start](../../../1_QuickStart/17_workflow-agent-tools/index.md) — the same tools in a live conversation.
