# Functions · Query & State Tools

Namespace `VeloxDev.AI.Workflow.Functions`. Every signature below is the tool's parameter list (the model sees the parameter names and the `[Description]` text). All return compact JSON with `status` unless noted. **23 tools: `Query` (20) + `State` (3).**

## Query — read-only inspection (20)

| Tool | Signature | Purpose |
|---|---|---|
| `ListNodes` | `ListNodes()` | Compact node list `[{i,id,t,x,y,l,w,h,slots,...props}]`; use `GetNodeDetail` for full info. |
| `GetNodeDetail` | `GetNodeDetail(int nodeIndex)` | Full node detail by zero-based index: properties, slots with connections. |
| `GetNodeDetailById` | `GetNodeDetailById(string runtimeId)` | Full node detail by runtime ID (stable across add/remove). |
| `ListConnections` | `ListConnections()` | Visible connections only (compact, with link ids). Prefer `GetFullTopology` for the whole graph. |
| `GetTypeSchema` | `GetTypeSchema(string fullTypeName)` | JSON schema of a .NET type by full name (`TypeIntrospector`). |
| `GetWorkflowSummary` | `GetWorkflowSummary()` | High-level summary: tree id/type, node/link counts, distinct node types. Call first to orient. |
| `GetComponentContext` | `GetComponentContext(string fullTypeName, string language = "English")` | `[AgentContext]` docs for a type (`"English"` / `"Chinese"`). |
| `ListComponentCommands` | `ListComponentCommands(int nodeIndex)` | Commands on a node: name + parameter type. |
| `FindNodes` | `FindNodes(string typeName = "", string? propertyName = null, string? propertyValue = null)` | Nodes filtered by type-name substring and/or property value. |
| `ResolveSlotId` | `ResolveSlotId(int nodeIndex, string propertyName, int collectionIndex = 0)` | Slot runtime ID from its owning property name (+ collection index). |
| `ListSlotProperties` | `ListSlotProperties(int nodeIndex)` | Named single slots, slot collections, and `SlotEnumerator` properties with ids/selectors/`allowedSelectorTypes`. |
| `GetEnumSlotByValue` | `GetEnumSlotByValue(int nodeIndex, string propertyName, string conditionValue)` | Runtime ID of a `SlotEnumerator` slot by enum/bool condition value. |
| `GetLinkDetail` | `GetLinkDetail(string linkId)` | Full link detail by runtime ID (sender/receiver slots + parent nodes). |
| `ListCreatableTypes` | `ListCreatableTypes()` | Creatable node/slot types (scan of registered + tree assemblies). |
| `ValidateWorkflow` | `ValidateWorkflow()` | Warnings: zero-size, isolated (has slots, no connections), no-slot nodes, duplicate links. |
| `GetFullTopology` | `GetFullTopology()` | Whole graph in one call: nodes + slots (property names/ids) + connections. |
| `CompileWorkflow` | `CompileWorkflow(int startNodeIndex)` | Compile plan (Root role) for the subgraph reachable from a start node. |
| `CompileNodeResult` | `CompileNodeResult(int nodeIndex)` | Compile plan (Terminal role) for a node's ancestor cone. |
| `GetCompileStatus` | `GetCompileStatus()` | Current compile identity of every compile-aware node (`Order`/`ChainIndex`/`Offset`/`isStopped`) without recompiling. |
| `GetExecutionLog` | `GetExecutionLog()` | Tree's aggregate direct-execution log (a convention-named `ExecutionLog` property). |

Note `CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus` and `GetExecutionLog` are **Query tools** but never run node code — they are not gated by `WithAllowNodeExecution`.

## State / diff / dirty (3)

| Tool | Signature | Purpose |
|---|---|---|
| `TakeSnapshot` | `TakeSnapshot()` | Takes a state snapshot; returns `version` + summary counts only. |
| `GetChangesSinceSnapshot` | `GetChangesSinceSnapshot()` | Diff since last snapshot (added/removed/modified nodes and links). |
| `MarkDirty` | `MarkDirty()` | Marks the tree dirty — call once at the end of a mutation task when auto-mark is off. |

`TakeSnapshot` / `GetChangesSinceSnapshot` read from a `WorkflowStateTracker`; see the `VeloxDev.AI.Workflow` page. `MarkDirty` is a **write** (it counts against `MaxWriteToolCalls` and, unlike the reads, marks the tree dirty).

## Example

```text
// Source: Test — ComposedProvidersTests
ListNodes()                                  → [{"i":0,"id":"...","t":"NodeDefaultViewModel",...}]
GetChangesSinceSnapshot()                    → {"status":"diff","version":2,"changes":{"addedNodes":[...]}}
MarkDirty()                                  → {"status":"ok"}
```

**Expected result:** `AddSlotToCollection` then `Undo` (see the Mutation page) makes `GetChangesSinceSnapshot` report the slot's removal in `changes`.
