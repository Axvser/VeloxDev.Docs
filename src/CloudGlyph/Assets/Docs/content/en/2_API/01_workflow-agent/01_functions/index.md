# Workflow Agent — Namespace: `VeloxDev.AI.Workflow.Functions`

### `WorkflowAgentToolkit`

**Signature:** `public sealed class WorkflowAgentToolkit(WorkflowAgentScope scope)`
**Constructor exceptions:** `ArgumentNullException` when `scope` is null.
**Key member:** `public IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` — builds ~60 `AITool`s wrapped in call-tracking. Default `CreateTools()` equals `CreateTools(All)` (asserted by tests). Custom tools registered on the scope are always included regardless of `categories`.

**Example:** `WorkflowAgentToolkit.cs` `CreateTools()` lines 34–161; tests `WorkflowAgentToolkitTests.CreateTools_All_MatchesDefaultAndIncludesEveryCategory`.

### `WorkflowToolCategory`

**Signature:** `[Flags] public enum WorkflowToolCategory` — `Query`, `Mutation`, `Execution`, `Command`, `Graph`, `Layout`, `Analytics`, `State`, `Composite`, `Interaction`, `All`.
**Notes:** `Layout` and `Composite` are reserved — no bundled layout/composite tools exist (each operation is a single component-command step so the undo/redo stack is never bypassed). `Interaction` tools appear only when a handler is configured and safety level > 0.

### Tool groups (enumerated from `CreateTools()`)

All JSON output is `Formatting.None` (compact) to save tokens. Every tool returns a JSON object; most use `status: "ok" | "error" | "rejected"`.

#### Query (read-only) — 19 tools

| Tool | Purpose (from `[Description]`) |
|---|---|
| `ListNodes` | Compact list: `[{i,id,t,x,y,l,w,h,slots,...props}]`. |
| `GetNodeDetail` | Full node detail by index: properties, slots with connections. |
| `GetNodeDetailById` | Full node detail by runtime ID (stable across add/remove). |
| `ListConnections` | Visible connections only (compact, with link ids). |
| `GetTypeSchema` | JSON schema of a .NET type by full name. |
| `GetWorkflowSummary` | High-level summary: counts, distinct node types, tree id. |
| `GetComponentContext` | `[AgentContext]` docs for a type by full name (English/Chinese). |
| `ListComponentCommands` | Commands on a node: name + parameter type. |
| `FindNodes` | Nodes filtered by type-name substring and/or property value. |
| `ResolveSlotId` | Slot runtime ID from its owning property name (+ collection index). |
| `ListSlotProperties` | Named single slots, collections and `SlotEnumerator` props with ids/selectors. |
| `GetEnumSlotByValue` | Runtime ID of a `SlotEnumerator` slot by enum/bool condition value. |
| `GetLinkDetail` | Full link detail by runtime ID. |
| `ListCreatableTypes` | Creatable node/slot types (scan of registered + tree assemblies). |
| `ValidateWorkflow` | Warnings: zero-size, isolated, no-slot nodes, duplicate links. |
| `GetFullTopology` | Whole graph in one call: nodes+slots+connections. |
| `CompileWorkflow` | Compiles reachable subgraph; returns entries + compile orders. |
| `GetCompileStatus` | Current compile identity (Order/ChainIndex/Offset) without recompiling. |
| `GetExecutionLog` | Tree's aggregate direct-execution log (convention-named `ExecutionLog` property). |

#### State / diff / dirty — 3 tools

| Tool | Purpose |
|---|---|
| `TakeSnapshot` | State snapshot; returns version + summary counts. |
| `GetChangesSinceSnapshot` | Diff since last snapshot (added/removed/modified nodes and links). |
| `MarkDirty` | Marks the tree dirty (call once at end of a mutation task when auto-mark is off). |

#### Mutation (structural) — 23 tools

| Tool | Purpose |
|---|---|
| `CreateNode` | Creates a node via `CreateNodeCommand`; auto-offsets to avoid overlap; 0 size reads the type default (fallback 300×260). |
| `CreateSlotOnNode` | Creates a dynamic slot via `CreateSlotCommand`. |
| `MoveNode` | Moves a node by relative offset (dispatches `SetAnchorCommand`; not undoable, mirrors GUI drag). |
| `SetNodePosition` | Sets absolute position/layer (dispatches `SetAnchorCommand`; not undoable). |
| `ResizeNode` | Resizes (dispatches `SetSizeCommand`; not undoable). |
| `DeleteNode` | Deletes a node; cascades slots and connections (atomic, one undo entry). |
| `DeleteSlot` | Deletes a slot and its connections. |
| `ConnectSlots` | Connects by node/slot indices (prefer `ConnectByProperty`). |
| `ConnectSlotsById` | Connects by runtime IDs. |
| `ConnectByProperty` | Connects by slot property names on owning nodes (composite convenience). |
| `DisconnectSlots` | Removes a connection by node/slot indices. |
| `DisconnectSlotsById` | Removes a connection by slot runtime IDs. |
| `SetSlotChannel` | Changes a slot's `SlotChannel`. |
| `SetEnumSlotChannel` | Sets channel of a `SlotEnumerator` slot by condition value. |
| `ConnectEnumSlot` | Connects a `SlotEnumerator` slot (by condition) to a slot/index/enum slot. |
| `PatchNodeProperties` | Patches custom node properties (rejects framework-managed and slot props). |
| `PatchComponentById` | Patches any component's custom properties by runtime ID. |
| `AddSlotToCollection` | Adds a slot to a collection property via `CreateSlotCommand`. |
| `RemoveSlotFromCollection` | Removes a slot from a collection property by runtime ID. |
| `SetEnumSlotCollection` | Sets a `SlotEnumerator` selector on an existing node (enum/bool or non-enum `ISlotProvider`). |
| `Undo` | Undoes the last action. |
| `Redo` | Redoes the last undone action. |
| `ClearHistory` | Drops the undo/redo history without touching the canvas. |

#### Execution (node business code, gated by `WithAllowNodeExecution`) — 5 tools

| Tool | Purpose |
|---|---|
| `ExecuteNode` | Executes a node's `ReceiveCommand` and waits for completion (node-level EXEC). |
| `ExecuteNodes` | Executes `ReceiveCommand` on multiple nodes and waits. |
| `BroadcastNode` | Executes `BroadcastCommand` (forward dispatch is fire-and-forget). |
| `ReverseBroadcastNode` | Executes `ReverseBroadcastCommand` (triggers upstream `ReceiveCommand`). |
| `RunCompiledWorkflow` | Chain-level entry: compiles from a start node and drives the whole chain via `CompilerEngine` + `RuntimeContext`. |

#### Command (generic, gated by `WithAllowedGenericCommands`) — 2 tools

| Tool | Purpose |
|---|---|
| `ExecuteCommandOnNode` | Executes any command on a node by index. |
| `ExecuteCommandById` | Executes any command on a component (node/slot/link) by runtime ID. |

#### Graph (traversal) — 5 tools

| Tool | Purpose |
|---|---|
| `SearchForward` | BFS downstream from a node (optional type filter, max depth). |
| `SearchReverse` | BFS upstream from a node. |
| `SearchAllRelative` | BFS both directions. |
| `IsConnected` | Direct/transitive connection check (`forward`/`reverse`/`any`). |
| `FindPath` | Shortest forward path (BFS) between two nodes. |

#### Analytics — 1 tool

| Tool | Purpose |
|---|---|
| `GetNodeStatistics` | In-degree/out-degree/total connections/connected node ids/slot utilization. |

#### Interaction (only when a handler is registered AND safety level > 0) — 2 tools

| Tool | Purpose |
|---|---|
| `RequestSelection` | Presents a single/multi-choice + free-text prompt and waits for the user. |
| `RequestConfirmation` | Requests explicit user confirmation; supports allow-once/allow-always-for-session/deny. |

> **Removed tools.** The previous doc revision listed `AlignNodes`, `DistributeNodes`, `AutoLayout`, `ArrangeNodes`, `BatchExecute`, `BulkPatchNodes`, `CloneNodes`, `DeleteNodes`, `DisconnectAllFromSlot`, `DisconnectAllFromNode`, `ReplaceConnection`, `CreateAndConfigureNode`. These are **no longer provided** — `WorkflowAgentToolkitTests` asserts their absence (`AutoLayout`, `BatchExecute`, `CloneNodes`, `CreateAndConfigureNode` are explicitly checked). Multi-node layout is done node-by-node via `MoveNode`/`SetNodePosition`; bulk operations via `ExecuteNodes`/loop-and-mutate. `GetChanges` from the old page is `GetChangesSinceSnapshot` in the current source.
