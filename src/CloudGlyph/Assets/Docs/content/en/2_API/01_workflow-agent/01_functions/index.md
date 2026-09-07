# Workflow Agent — Namespace: `VeloxDev.AI.Workflow.Functions`

`WorkflowAgentToolkit` turns a scoped tree into ~60 MAF `AITool` instances (full operational control), grouped by `WorkflowToolCategory`; the helper classes `CommandInvoker`, `ComponentPatcher` and `TypeIntrospector` back the command/patch/schema tools. All JSON output is `Formatting.None` (compact) to save tokens; most tools return an object with `status: "ok" | "error" | "rejected"` (rejections carry `reasons`, `hint`, `preferredAlternative`). Every built-in tool is wrapped so each call is marshalled onto the UI context when configured, counted against the caps, reported through `ToolCalled`/`WithToolCallCallback`, and optionally auto-marks the tree dirty.

Implemented in `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/`. **Evidence:** **Test** (`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/*` — tools are invoked through the public `scope.ProvideTools()` registration path) + **Demo** (`AgentHelper.ProvideAgent`).

## WorkflowAgentToolkit

`public sealed class WorkflowAgentToolkit(WorkflowAgentScope scope)`. Constructor throws `ArgumentNullException` when `scope` is null. Each toolkit owns a `WorkflowStateTracker` over the scoped tree.

| Member | Signature | Notes |
|---|---|---|
| `CreateTools` | `IList<AITool> CreateTools(WorkflowToolCategory categories = WorkflowToolCategory.All)` | Builds the tool set restricted to the given category flags. Default `CreateTools()` = `CreateTools(All)`. Custom tools registered on the scope (`WithTools`/`WithQueryTools`) are always included regardless of `categories`. |

## WorkflowToolCategory

`[Flags] public enum WorkflowToolCategory` — tool-group selector for `CreateTools`.

| Flag | Value | Contains |
|---|---|---|
| `Query` | `1 << 0` | Read-only inspection (20 tools). |
| `Mutation` | `1 << 1` | Structural graph edits (23 tools). |
| `Execution` | `1 << 2` | Run node business code (6 tools, gated). |
| `Command` | `1 << 3` | Generic allowlisted command execution (2 tools, gated). |
| `Graph` | `1 << 4` | Traversal & path finding (5 tools). |
| `Layout` | `1 << 5` | **Reserved** — no bundled layout tools. |
| `Analytics` | `1 << 6` | `GetNodeStatistics`. |
| `State` | `1 << 7` | Snapshots & dirty marking (3 tools). |
| `Composite` | `1 << 8` | **Reserved** — no composite/bundled tools. |
| `Interaction` | `1 << 9` | `RequestSelection` / `RequestConfirmation` — registered only when a handler is configured and safety level > 0. |
| `All` | (all of the above) | Every category. |

`Layout` and `Composite` are reserved by design: multi-node layout is done node-by-node via `MoveNode`/`SetNodePosition`, and every operation is a single component-command step, so the framework's undo/redo stack stays the source of truth and is never bypassed or double-submitted.

## Tool inventory (from `CreateTools()`)

### Query — read-only, 20 tools

| Tool | Purpose |
|---|---|
| `ListNodes` | Compact node list `[{i,id,t,x,y,l,w,h,slots,...props}]`; `GetNodeDetail` for full info. |
| `GetNodeDetail` | Full node detail by zero-based index: properties, slots with connections. |
| `GetNodeDetailById` | Full node detail by runtime ID (stable across add/remove). |
| `ListConnections` | Visible connections only (compact, with link ids). |
| `GetTypeSchema` | JSON schema of a .NET type by full name (`TypeIntrospector`). |
| `GetWorkflowSummary` | High-level summary: tree id/type, node/link counts, distinct node types. |
| `GetComponentContext` | `[AgentContext]` docs for a type by full name (`language` `"English"`/`"Chinese"`). |
| `ListComponentCommands` | Commands on a node: name + parameter type. |
| `FindNodes` | Nodes filtered by type-name substring and/or property value. |
| `ResolveSlotId` | Slot runtime ID from its owning property name (+ collection index). |
| `ListSlotProperties` | Named single slots, slot collections, and `SlotEnumerator` properties with ids/selectors/`allowedSelectorTypes`. |
| `GetEnumSlotByValue` | Runtime ID of a `SlotEnumerator` slot by enum/bool condition value. |
| `GetLinkDetail` | Full link detail by runtime ID (sender/receiver slots + parent nodes). |
| `ListCreatableTypes` | Creatable node/slot types (scan of registered + tree assemblies). |
| `ValidateWorkflow` | Warnings: zero-size, isolated (has slots, no connections), no-slot nodes, duplicate links. |
| `GetFullTopology` | Whole graph in one call: nodes + slots (property names/ids) + connections. |
| `CompileWorkflow` | Compile plan (Root role) for the subgraph reachable from a start node. |
| `CompileNodeResult` | Compile plan (Terminal role) for a node's ancestor cone. |
| `GetCompileStatus` | Current compile identity of every compile-aware node (Order/ChainIndex/Offset/isStopped) without recompiling. |
| `GetExecutionLog` | Tree's aggregate direct-execution log (convention-named `ExecutionLog` property). |

### State / diff / dirty — 3 tools

| Tool | Purpose |
|---|---|
| `TakeSnapshot` | Takes a state snapshot; returns `version` + summary counts only. |
| `GetChangesSinceSnapshot` | Diff since last snapshot (added/removed/modified nodes and links). |
| `MarkDirty` | Marks the tree dirty — call once at the end of a mutation task when auto-mark is off. |

### Mutation — structural, 23 tools

Each executes exactly one component command (single undo entry at most; the framework's undo/redo stack is authoritative).

| Tool | Purpose |
|---|---|
| `MoveNode` | Moves a node by relative offset (`SetAnchorCommand`; not undoable — mirrors GUI drag). |
| `SetNodePosition` | Absolute position/layer (`SetAnchorCommand`; not undoable). |
| `ResizeNode` | Resize (`SetSizeCommand`; not undoable). |
| `DeleteNode` | Deletes a node; cascades child slots + connections atomically (one undo entry). |
| `DeleteSlot` | Deletes a slot and its connections. |
| `ConnectSlots` | Connect by node/slot indices (`ConnectByProperty` preferred). |
| `ConnectSlotsById` | Connect by slot runtime IDs. |
| `ConnectByProperty` | Connect by slot property names on owning nodes (handles single/collection/`SlotEnumerator`). |
| `DisconnectSlots` | Removes a connection by node/slot indices. |
| `DisconnectSlotsById` | Removes a connection by slot runtime IDs. |
| `SetSlotChannel` | Changes a slot's `SlotChannel`. |
| `SetEnumSlotChannel` | Sets channel of a `SlotEnumerator` slot by condition value. |
| `ConnectEnumSlot` | Connects a `SlotEnumerator` slot (by condition) to a slot/index/enum slot. |
| `PatchNodeProperties` | Patches a node's custom properties (rejecting patcher). |
| `PatchComponentById` | Patches any component's custom properties by runtime ID. |
| `CreateNode` | Creates a node via `CreateNodeCommand`; auto-offsets to avoid overlap; 0 size reads the type default (`[DefaultSize]`, fallback 300×260). |
| `CreateSlotOnNode` | Creates a dynamic slot via `CreateSlotCommand` (typed slot properties are source-generated). |
| `AddSlotToCollection` | Adds a slot to a collection property via `CreateSlotCommand`. |
| `RemoveSlotFromCollection` | Removes a slot from a collection property by slot runtime ID. |
| `SetEnumSlotCollection` | Sets a `SlotEnumerator` selector on an existing node (enum/bool type name, or non-enum `ISlotProvider` via JSON + `nonEnumTypeName`). |
| `Undo` | Undoes the last action. |
| `Redo` | Redoes the last undone action. |
| `ClearHistory` | Drops the undo/redo history without touching the canvas. |

**Connection rejects.** Connection tools verify the link actually exists in `LinksMap` after dispatching; the framework may silently refuse (channel incompatibility, same-node rule, `ValidateConnection`). On refusal they return `status: "rejected"` with `reasons`, `hint`, and often `preferredAlternative` naming the property-route tool to use next — never blindly retry.

### Execution — runs node business code, 6 tools, gated by `WithAllowNodeExecution`

Return `status: "error"` with a "disabled by host policy" message when the gate is off.

| Tool | Role | Purpose |
|---|---|---|
| `ExecuteNode` | node EXEC | Executes one node's `ReceiveCommand` and **waits** for real completion. |
| `ExecuteNodes` | node EXEC | Executes `ReceiveCommand` on a JSON array of node indices and waits for each. |
| `BroadcastNode` | node broadcast | Executes `BroadcastCommand` (downstream dispatch is fire-and-forget); waits for the command. |
| `ReverseBroadcastNode` | node broadcast | Executes `ReverseBroadcastCommand` (triggers upstream `ReceiveCommand`); waits for the command. |
| `RunCompiledWorkflow` | chain Root | Compiles from a start node and drives the whole chain with the engine. |
| `GetNodeResult` | Terminal result | Computes a single node's result from its ancestor cone. |

### Command — generic, 2 tools, gated by `WithAllowedGenericCommands`

| Tool | Purpose |
|---|---|
| `ExecuteCommandOnNode` | Executes any (allowlisted) command on a node by index. |
| `ExecuteCommandById` | Executes any (allowlisted) command on a component (node/slot/link) by runtime ID. |

### Graph — traversal, 5 tools

| Tool | Purpose |
|---|---|
| `SearchForward` | BFS downstream (optional type-name filter, max depth). |
| `SearchReverse` | BFS upstream. |
| `SearchAllRelative` | BFS both directions. |
| `IsConnected` | Direct/transitive connection check (`forward`/`reverse`/`any`). |
| `FindPath` | Shortest forward path (BFS); ordered `{i,id,t}` list or empty. |

### Analytics — 1 tool

| Tool | Purpose |
|---|---|
| `GetNodeStatistics` | In-degree/out-degree/total connections/connected node ids/slot utilization. |

### Interaction — 2 tools, only when a handler is registered AND safety level > 0

| Tool | Purpose |
|---|---|
| `RequestSelection` | Presents single-/multi-choice + free-text and waits for the user; returns `chosen` (single) or `chosenList` (multi) plus `freeText`. |
| `RequestConfirmation` | Requests explicit confirmation; allow-once / allow-always-for-session / deny. |

## Root vs Terminal compile semantics

The compile and chain-run tools are the Agent's view over the `VeloxDev.Core.WorkflowSystem.CompilerEx` engine. Underlying engine: `new CompilerViewModel().CompileAsync(node, CompileRole)` then `new RuntimeEngine().RunAsync(graph, runtimeContext, ct)` — **not** the older `CompilerEngine`/`CompileToAsync` API. Two compile roles mirror the two entries:

| | `CompileWorkflow` (plan) / `RunCompiledWorkflow` (run) | `CompileNodeResult` (plan) / `GetNodeResult` (run) |
|---|---|---|
| Role | `CompileRole.Root` — start node is a controller/entry. | `CompileRole.Terminal` — the node is the result terminal. |
| Scope | Compiles the sub-graph reachable downstream from the start node. | Reverse-compiles the node's **ancestor cone**: upstream producers feeding it, traced back from its input slots; no controller needed, the cone's entry frontier is derived. |
| Runtime target | Whole chain run; `context.Target` is null. | `context.Target = node`; the run drives only the cone and reports the node's result. |
| Output | `role`, `runStatus` (`Completed`/`Stopped`), `endedWithError`, `attempts`, `data`, `logs`. | Same shape **plus** `targetReached` (present only for Terminal). |
| Branch semantics | Static pruning: a downstream node on no live branch gets `Order = -1` (absolute stop). | Routers in the cone keep **real** `BranchSegment` selection — only the branch leading to the node is compiled (siblings absent, not `Order = -1`). If more than one route key of the same router reaches the node, compilation returns an error (a single forward run can take only one branch). |

**Terminal error contract.** If a router on the cone actually selects a **sibling** branch at runtime, the target is not driven: `GetNodeResult` returns `status: "error"` with a message naming the target (`"... was NOT reached ... No result was produced."`) and no data — never treat another branch's final payload as this node's result. Point the router at the branch leading to the node first (`PatchNodeProperties`/`SetEnumSlotCollection`), then retry. `targetReached: true` is returned when the node was driven.

Compiling attaches compile identity to the cone/chain's `ICompileTimeAware` nodes; `GetCompileStatus` reads it afterward without recompiling. `RunCompiledWorkflow` uses compiled-step semantics — nodes run `ReceiveAsync` with an `IRuntimeContext` session and do **not** auto-broadcast; the engine owns downstream dispatch. `GetExecutionLog` returns the tree's *direct* (non-compiler) execution log; use the run tool's `logs` field for the compiler run-session log.

## Helper classes

### CommandInvoker

`public static class CommandInvoker` — discovers and invokes `IVeloxCommand` properties on workflow components; backs `ListComponentCommands`, `ExecuteCommandOnNode`, `ExecuteCommandById`. Deserializes JSON parameters to the type declared by `[AgentCommandParameter]`.

| Member | Signature | Notes |
|---|---|---|
| `DiscoverCommands` | `IReadOnlyList<CommandDescriptor> DiscoverCommands(object component)` | `ICommand`-typed properties — interface properties first (authoritative attributes), then the concrete type's own (deduplicated). |
| `Invoke` | `string Invoke(object component, string commandName, string? jsonParameter)` | Executes a named command, returns JSON; `"Command"` suffix appended if missing. |

`CommandDescriptor` (`Name`, `ParameterType` (`Type?`), `Descriptions` as `IReadOnlyList<KeyValuePair<AgentLanguages, string>>`) is declared in this file.

### ComponentPatcher

`public static class ComponentPatcher` — applies a JSON patch object to a component by setting writable public properties. Backs `PatchNodeProperties`/`PatchComponentById`.

| Member | Signature | Notes |
|---|---|---|
| `ApplyPatch` | `string ApplyPatch(object target, string jsonPatch)` | Applies `{"Prop": value}`. Rejects (with `rejected`/`skipped` + `reason`) framework-managed props (`Parent`, `Nodes`, `Links`, `LinksMap`, `Slots`, `Targets`, `Sources`, `State`, `VirtualLink`, `RuntimeId`, `Helper`), command-backed props (routed to their backing command), slot-typed and `[SlotSelectors]`-marked props; errors on a target not mounted in a tree (no parent chain); a `Type` property resolves names via `TypeIntrospector`. Direct writes are intentionally non-undoable (undo is Core's command pipeline's job). |
| `ApplyPatchWithUndo` | `string ApplyPatchWithUndo(object target, string jsonPatch, IWorkflowTreeViewModel? tree = null)` | Backward-compatible alias → `ApplyPatch` (`tree` ignored). |
| `CopyScalarProperties` | `void CopyScalarProperties(object source, object target)` | Copies writable scalar/enum properties, skipping command/slot/framework-managed ones. |

### TypeIntrospector

`public static class TypeIntrospector` — type resolution + JSON schema for Agent consumption; backs `GetTypeSchema`.

| Member | Signature | Notes |
|---|---|---|
| `ResolveType` | `Type? ResolveType(string fullTypeName)` | Delegates to `AgentTypeResolver.ResolveType`. |
| `GetTypeSchema` | `string GetTypeSchema(Type type)` | Indented JSON: `fullName`, `kind` (enum/interface/struct/class), `baseType`, `interfaces`, enum `values` or property list (`name`/`type`/`canRead`/`canWrite`), plus `developerInstructions` (`[AgentContext]` across languages) and `defaultJson_runtimeOnly` when a default instance can be built. |
