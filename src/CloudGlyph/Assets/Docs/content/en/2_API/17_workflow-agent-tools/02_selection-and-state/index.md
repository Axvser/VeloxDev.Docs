# Selection and state

Two small services support the agent without adding tools: the selection extensions narrow the per-turn prompt to the nodes the user has picked, and `WorkflowStateTracker` lets the model read a diff instead of the whole graph again.

## Class: WorkflowAgentSelectionExtensions

`VeloxDev.AI.Workflow.WorkflowAgentSelectionExtensions` is a static class of extension methods. Selection is prompt context, not a tool: it changes only the per-turn instructions that name the selected nodes, never the tool set or the tree.

The selection is an identity snapshot (stable runtime id plus type name). Geometry, slots and properties are deliberately not captured; the model reads those through the normal query tools, so the prompt never carries a stale position. A node that is deleted, reparented or removed from its tree is dropped immediately.

| Method | Returns | Description |
|---|---|---|
| `SelectForAgent(this INodeComponent node)` | `bool` | Adds one node to its tree's selection. `true` when newly added. |
| `SelectForAgent(this IReadOnlyCollection<INodeComponent> nodes)` | `int` | Unions several nodes into their trees' selections. Returns the number newly added, `0` when nothing changed, `-1` on an internal error. |
| `DeselectForAgent(this INodeComponent node)` | `bool` | Removes one node from the selection. |
| `DeselectForAgent(this IReadOnlyCollection<INodeComponent> nodes)` | `int` | Removes several nodes; returns the number actually removed. |
| `ClearAgentSelection(this ITreeComponent tree)` | `int` | Clears the tree's selection and returns the number released. |
| `GetAgentSelection(this ITreeComponent tree)` | `IReadOnlyList<INodeComponent>` | A copy of the current selection, in selection order. |

The operations are set-like: selecting an already-selected node is a no-op, and a collection call reports only what actually changed. To replace the whole selection, call `ClearAgentSelection` and then add the new set. No exception escapes; null, unattached or id-less nodes are skipped.

The prompt lists at most 64 identities; the reported count is always the full selection. This keeps a select-all from turning every turn into a large prompt while still telling the model how large the working set is.

```csharp
using VeloxDev.AI.Workflow;

node.SelectForAgent();                 // add one node
selectedNodes.SelectForAgent();        // union; returns how many were added
tree.ClearAgentSelection();            // release everything
var current = tree.GetAgentSelection();
```

## Class: WorkflowStateTracker

`VeloxDev.AI.Workflow.WorkflowStateTracker` captures lightweight snapshots and computes diffs, so an agent can track changes with minimal context. The workflow toolkit owns one instance per scope, behind `TakeSnapshot` and `GetChangesSinceSnapshot`.

| Member | Signature | Description |
|---|---|---|
| Constructor | `WorkflowStateTracker(ITreeComponent tree)` | Binds the tracker to one tree. |
| `Version` | `long` | Monotonically increasing snapshot version. |
| `TakeSnapshot` | `string TakeSnapshot()` | Records the current tree state and returns it as JSON. |
| `GetChangesSinceLastSnapshot` | `string GetChangesSinceLastSnapshot()` | Returns a JSON diff of added, removed and modified nodes and links. With no previous snapshot, returns the full current state. |

The tracker is a plain class; it does not raise change notifications. The `State` tool category exposes it to the model as `TakeSnapshot` and `GetChangesSinceSnapshot`.

## Related

- [WorkflowAgentToolkit](../01_workflow-agent-toolkit/index.md) — the tools backed by these services.
- [WorkflowAgentScope](../00_workflow-agent-scope/index.md) — `CreateToolkit` owns the scope's tracker.
