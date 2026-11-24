# Node, slot and link operations

Three static classes carry the standard per-component operations. They are the implementations behind the component commands and the hooks a host overrides.

Namespace: `VeloxDev.WorkflowSystem.StandardEx`.

## WorkflowNodeEx

### GetStandardCommands

**Signature:** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this INodeComponent component)`

Returns, in order: `SetAnchorCommand`, `SetSizeCommand`, `CreateSlotCommand`, `DeleteCommand`, `ReceiveCommand`, `BroadcastCommand`, `ReverseBroadcastCommand`.

### StandardCreateSlot

**Signature:** `static void StandardCreateSlot(this INodeComponent component, ISlotComponent slot)`

Adds `slot` to `component.Slots`. On a detached node the add is immediate; on an attached node it is submitted as one undoable step. A slot already registered with the same reference is ignored (idempotency guard).

### GetWorldAnchor / GetWorldSize

**Signatures:** `static Anchor GetWorldAnchor(this INodeComponent component)`, `static Size GetWorldSize(this INodeComponent component)`

Return the stored world value by undoing the getter's scale collapse. Both throw `ArgumentNullException` when `component` is null. Use these whenever a value is read for writing back; the `Anchor`/`Size` getters return a collapsed copy.

### StandardSetAnchor

**Signature:** `static void StandardSetAnchor(this INodeComponent component, Anchor anchor)`

Writes a world anchor. The notification is the property setter's responsibility; the standard implementation raises `PropertyChanged` for `Anchor`.

### StandardSetLayer

**Signature:** `static void StandardSetLayer(this INodeComponent component, int layer)`

Keeps the world position and replaces only `Layer`.

### StandardSetSize

**Signature:** `static void StandardSetSize(this INodeComponent component, Size size)`

Raises `Resizing(from, to)`; a `PreventDefault` on that handle stops the write. Otherwise writes the size and raises `Resized(from, to, handle)`.

### StandardMove

**Signature:** `static void StandardMove(this INodeComponent component, Offset offset)`

`offset` is a **view-space** drag delta. The method expands the collapsed anchor, computes `to = (view + offset) * scale`, raises `Moving(from, to)` with both ends as complete world anchors (layer included), writes unless prevented, then raises `Moved`.

### StandardBroadcastAsync / StandardReverseBroadcastAsync

**Signatures:** `static Task StandardBroadcastAsync(this INodeComponent component, object? parameter, CancellationToken ct = default)`, `static Task StandardReverseBroadcastAsync(...)`

Walk `Targets` (forward) or `Sources` (reverse), build a `TaskContext` per edge, call the node helper's `AccessAsync`, and dispatch `ReceiveCommand` on each accepted receiver. A rejected edge is skipped, exactly as an unconnected one would be. Throws `ArgumentException` when the helper cannot be obtained.

### SearchForwardNodes / SearchReverseNodes / SearchAllRelativeNodes

**Signatures:** `static IEnumerable<INodeComponent> SearchForwardNodes(this INodeComponent component, Func<INodeComponent, bool>? predicate = null, int maxDepth = 0)`, same for `SearchReverseNodes`, and `SearchAllRelativeNodes`

Breadth-first traversal over `Targets` (forward), `Sources` (reverse) or both. `maxDepth = 0` means unlimited. The start node is excluded; `predicate` filters what is yielded but not what is traversed. `SearchAllRelativeNodes` shares one visited set across both directions.

### StandardDelete

**Signature:** `static void StandardDelete(this INodeComponent component)`

Raises `Deleting()`; a `PreventDefault` keeps the node. Otherwise collects every link whose both endpoints belong to the same tree, and submits one pair that removes links, clears slot parents and removes the node (redo), or restores all of them (undo). An unattached node calls `WorkflowGuard.Fail`.

## WorkflowSlotEx

### GetStandardCommands

**Signature:** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this ISlotComponent component)`

Returns `SendConnectionCommand`, `ReceiveConnectionCommand`, `DeleteCommand`.

### StandardSetChannel

**Signature:** `static void StandardSetChannel(this ISlotComponent component, SlotChannel channel)`

Raises `ChannelChanging(from, to)`; a `PreventDefault` keeps the old channel. Otherwise deletes the links the new channel disallows, writes the channel, then raises `ChannelChanged`. A slot not attached to a tree calls `WorkflowGuard.Fail`.

### StandardUpdateState

**Signature:** `static void StandardUpdateState(this ISlotComponent component)`

Recomputes `State` from `Targets`/`Sources`: `Sender`, `Receiver`, `Sender | Receiver`, or `StandBy`. The two preview bits (`PreviewSender`, `PreviewReceiver`) are preserved because they belong to an in-progress drag.

### StandardSendConnection / StandardReceiveConnection

**Signatures:** `static void StandardSendConnection(this ISlotComponent component)`, `static void StandardReceiveConnection(this ISlotComponent component)`

Forward to the owning tree's helper. A slot not attached to a tree calls `WorkflowGuard.Fail`.

### StandardDelete

**Signature:** `static void StandardDelete(this ISlotComponent component)`

Collects the slot's links and submits one pair that removes the links and the slot (redo) or restores them (undo). An unattached slot calls `WorkflowGuard.Fail`.

### StandardCanBeSender / StandardCanBeReceiver

**Signatures:** `static bool StandardCanBeSender(this ISlotComponent component)`, `static bool StandardCanBeReceiver(this ISlotComponent component)`

Test the channel flags: sending needs `OneTarget`, `MultipleTargets`, `OneBoth` or `MultipleBoth`; receiving needs the `...Source...` equivalents.

## WorkflowLinkEx

### GetStandardCommands

**Signature:** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this ILinkComponent component)`

Returns the single `DeleteCommand`.

### StandardDelete

**Signature:** `static void StandardDelete(this ILinkComponent component)`

Submits one pair that removes the link from `Links`, `LinksMap`, the sender's `Targets` and the receiver's `Sources` (redo), or restores it (undo). Both end states recompute the slot states. A link whose sender is not attached calls `WorkflowGuard.Fail`.

## Example

```csharp
var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0), Size = new Size(220, 120) };
tree.GetHelper().CreateNode(node);

node.GetHelper().SetAnchor(new Anchor(100, 80, 0));
Console.WriteLine(node.GetWorldAnchor());          // Anchor(100,80,0)

var forward = node.SearchForwardNodes(maxDepth: 2).Select(n => n.GetType().Name);
Console.WriteLine(string.Join(",", forward));      // empty for a leaf node

node.DeleteCommand.Execute(null);                  // one undo entry
tree.GetHelper().Undo();
Console.WriteLine(tree.Nodes.Count);               // 1
```
