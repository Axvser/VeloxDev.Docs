# Tree operations

`WorkflowTreeEx` contains the standard tree operations: the command bundle, node creation, the virtual-link pointer, undo history and degree/topology queries.

Namespace: `VeloxDev.WorkflowSystem.StandardEx`.

## GetStandardCommands

**Signature:** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this ITreeComponent component)`

Returns the eight commands a tree helper drives, in this order: `CreateNodeCommand`, `SetPointerCommand`, `ResetVirtualLinkCommand`, `SendConnectionCommand`, `ReceiveConnectionCommand`, `SubmitCommand`, `RedoCommand`, `UndoCommand`.

**Returns:** `IReadOnlyCollection<IVeloxCommand>` — the command bundle used by `Closing`/`CloseAsync`/`Closed`.

## StandardCreateNode

**Signature:** `static void StandardCreateNode(this ITreeComponent component, INodeComponent node)`

Detaches `node` from a previous tree (when it has one), then submits one `ActionPair` whose redo sets `node.Parent = component` and adds it to `Nodes`; undo removes it and restores the old parent.

| Parameter | Type | Description |
| --- | --- | --- |
| `component` | `ITreeComponent` | The destination tree. |
| `node` | `INodeComponent` | The node to add; it may already belong to another tree. |

**Returns:** `void`. Repeating a create is not guarded: adding the same node twice produces two entries and two collection items.

## StandardSetPointer

**Signature:** `static void StandardSetPointer(this ITreeComponent component, Anchor anchor)`

Moves the virtual link's receiver to `anchor`, keeping the sender's layer. When `VirtualLink` has no sender or receiver, the call is a no-op.

## StandardCloseAsync

**Signature:** `static Task StandardCloseAsync(this ITreeComponent component)`

Runs the three-phase close over the tree and every node, slot and link: `Closing()` (lock commands), `CloseAsync()` (drain), `Closed()` (unlock). Awaits each helper in turn.

**Returns:** `Task` — completes when every helper has closed.

## StandardSubmit

**Signature:** `static void StandardSubmit(this ITreeComponent component, IActionPair actionPair)`

Invokes `actionPair.Redo` and pushes the pair onto the undo stack. An exception from `Redo` is written to `Debug` and the pair is not pushed.

## StandardUndo / StandardRedo

**Signatures:** `static void StandardUndo(this ITreeComponent component)`, `static void StandardRedo(this ITreeComponent component)`

Pop one pair from the matching stack, invoke it, and push it onto the opposite stack. Exceptions are logged and the pair is not transferred.

## StandardClearHistory

**Signature:** `static void StandardClearHistory(this ITreeComponent component)`

Clears both the undo and redo stacks. It does not touch the model.

## Degree and topology queries

All six throw `ArgumentNullException` for a null tree; the two per-index methods also throw `ArgumentOutOfRangeException` for an index outside `Nodes`.

| Method | Returns | Description |
| --- | --- | --- |
| `GetNodeInDegree(this ITreeComponent tree, int nodeIndex)` | `int` | Sum of `Sources.Count` over the node's slots. |
| `GetNodeOutDegree(this ITreeComponent tree, int nodeIndex)` | `int` | Sum of `Targets.Count` over the node's slots. |
| `FindEntryNodeIndices(this ITreeComponent tree)` | `IReadOnlyList<int>` | Indices with in-degree `0`. |
| `FindExitNodeIndices(this ITreeComponent tree)` | `IReadOnlyList<int>` | Indices with out-degree `0`. |
| `FindNodesByInDegree(this ITreeComponent tree, int degree)` | `IReadOnlyList<int>` | Indices whose in-degree equals `degree`. |
| `FindNodesByOutDegree(this ITreeComponent tree, int degree)` | `IReadOnlyList<int>` | Indices whose out-degree equals `degree`. |

## Example

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel { Anchor = new Anchor(0, 0, 0) };
var b = new NodeDefaultViewModel { Anchor = new Anchor(300, 0, 0) };
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

Console.WriteLine($"entries={string.Join(",", tree.FindEntryNodeIndices())}");
Console.WriteLine($"exits={string.Join(",", tree.FindExitNodeIndices())}");

tree.GetHelper().Undo();
Console.WriteLine($"after undo nodes={tree.Nodes.Count}");
```
