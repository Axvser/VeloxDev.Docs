# Actions and commands

An edit is submitted as a redo/undo pair. The tree keeps two concurrent stacks of those pairs; the component commands are thin wrappers that build the pair and call `Submit`.

Namespace: `VeloxDev.WorkflowSystem` (`IActionPair`, `ActionPair`) and `VeloxDev.WorkflowSystem.StandardEx` (`WorkflowCommandEx`).

## IActionPair

**Signature:** `interface IActionPair`

| Member | Type | Description |
| --- | --- | --- |
| `Redo` | `Action` | Applies the change. |
| `Undo` | `Action` | Restores the previous state. |

## ActionPair

**Signature:** `readonly struct ActionPair(Action redo, Action undo) : IActionPair`

| Member | Type | Description |
| --- | --- | --- |
| `ActionPair(Action redo, Action undo)` | constructor | Stores both delegates. |
| `Redo` / `Undo` | `Action` | The stored delegates. |

```csharp
var before = node.GetWorldAnchor();
var after = new Anchor(before.Horizontal + 40, before.Vertical, before.Layer);
tree.GetHelper().Submit(new ActionPair(
    () => node.Anchor = after,
    () => node.Anchor = before));
```

## Command set

Every parameter is a plain model value, so the same command serves a gesture, a menu item and an Agent tool call.

| Component | Command | Parameter | Undo entry |
| --- | --- | --- | --- |
| `ITreeComponent` | `CreateNodeCommand` | `INodeComponent` | one |
| `ITreeComponent` | `SendConnectionCommand` | `ISlotComponent` | one for the drag's cleanup, if any |
| `ITreeComponent` | `ReceiveConnectionCommand` | `ISlotComponent` | one for the new link, plus any cleanup |
| `ITreeComponent` | `SubmitCommand` | `IActionPair` | the submitted pair |
| `ITreeComponent` | `UndoCommand` / `RedoCommand` | none | moves one entry |
| `ITreeComponent` | `SetPointerCommand` | `Anchor` | none |
| `ITreeComponent` | `ResetVirtualLinkCommand` | none | none |
| `INodeComponent` | `SetAnchorCommand` / `SetSizeCommand` | `Anchor` / `Size` | none |
| `INodeComponent` | `MoveCommand` | `Offset` | none |
| `INodeComponent` | `CreateSlotCommand` | `ISlotComponent` | one when attached |
| `INodeComponent` | `DeleteCommand` | none | one (node, slots and links) |
| `INodeComponent` | `ReceiveCommand` | `ITaskContext?` | none |
| `INodeComponent` | `BroadcastCommand` / `ReverseBroadcastCommand` | `object?` | none |
| `ISlotComponent` | `SetChannelCommand` | `SlotChannel` | none |
| `ISlotComponent` | `SendConnectionCommand` / `ReceiveConnectionCommand` | none | through the tree |
| `ISlotComponent` | `DeleteCommand` | none | one (slot and links) |
| `ILinkComponent` | `DeleteCommand` | none | one |

`SetChannelCommand` deliberately writes no undo entry: a channel decides how many connections a slot may hold, so changing it can tear existing links down, and that teardown is not an editable step. Set channels before wiring.

A host's own controller (`CompileCommand`, `RunCommand`, `StopCommand`, …) is generated from `[VeloxCommand]` methods on its own view model, not by the workflow model; see [MVVM ViewModel generation](../../../1_QuickStart/11_mvvm-viewmodel-generation/index.md).

## WorkflowCommandEx

**Signature:** `static class WorkflowCommandEx` — lifecycle operations over a command collection.

| Method | Returns | Description |
| --- | --- | --- |
| `StandardClosing(this IReadOnlyCollection<IVeloxCommand>)` | `void` | Calls `Lock()` on every command. |
| `StandardClosingAsync(...)` | `Task` | Awaits `LockAsync()` on each. |
| `StandardClose(...)` | `void` | Calls `Clear()` on every command. |
| `StandardCloseAsync(...)` | `Task` | Awaits `ClearAsync()` on each. |
| `StandardClosed(...)` | `void` | Calls `Unlock()` on every command. |
| `StandardClosedAsync(...)` | `Task` | Awaits `UnlockAsync()` on each. |

These are what a helper's `Closing` / `CloseAsync` / `Closed` use; they are not meant for per-edit use.

## History semantics

- `StandardSubmit(pair)` calls `pair.Redo` immediately and pushes the pair onto the undo stack; an action that throws is logged and not pushed.
- `StandardUndo` pops the undo stack, calls `Undo` and pushes onto the redo stack; `StandardRedo` is the mirror.
- The stacks are per tree, stored in a `ConditionalWeakTable`, so a tree that is collected releases its history.
- The history is one entry per logical operation, not a log of every internal collection change: deleting a node with links is one entry, and creating a slot on an attached node is one entry.

## Example

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0) };
var b = new NodeDefaultViewModel { Anchor = new Anchor(420, 80, 0) };
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

tree.GetHelper().Undo();
Console.WriteLine(tree.Nodes.Count);   // 1
tree.GetHelper().Redo();
Console.WriteLine(tree.Nodes.Count);   // 2

tree.GetHelper().ClearHistory();       // both stacks cleared
```
