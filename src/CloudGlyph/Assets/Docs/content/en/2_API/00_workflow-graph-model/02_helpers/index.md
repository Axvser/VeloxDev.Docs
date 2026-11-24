# Helpers

A helper carries the behaviour of one component and can be replaced without replacing the model. Each role has a non-generic class (closed over the interface type) and a generic class whose `Component` is the host's concrete view model.

All types are in `VeloxDev.WorkflowSystem` and implement `IInputEvents` by exposing an `InputRelay Input`.

## `TreeHelper` and `TreeHelper<T>`

**Signature:** `class TreeHelper<T> : ITreeHelper, ITreeEvents, IInputEvents, IWorkflowLayoutHost where T : class, ITreeComponent`

`TreeHelper` is `TreeHelper<ITreeComponent>` with two constructors: `TreeHelper()` (virtualization off) and `TreeHelper(double cellSize)` (virtualization on, tickable started).

| Member | Type | Description |
| --- | --- | --- |
| `Component` | `T?` | The installed tree when it matches `T`; protected setter. |
| `Input` | `InputRelay` | Pointer and key events for this component. |
| `VisibleItems` | `ObservableCollection<IWorkflowComponent>` | The current visible set. |
| `Viewport` | `Viewport` | Setting it calls `Component.Virtualize(value)`. |
| `NodeAdded` / `NodeRemoved` | `EventHandler<INodeComponent>` | Raised from the `Nodes` collection. |
| `LinkAdded` / `LinkRemoved` | `EventHandler<ILinkComponent>` | Raised from the `Links` collection. |
| `VisibleItemAdded` / `VisibleItemRemoved` | `EventHandler<IWorkflowComponent>` | Raised from `VisibleItems`. |
| `Connecting` / `Connected` | `EventHandler<ConnectionEventArgs>` | Connection veto and report. |
| `LayoutSolver` | `IWorkflowLayoutSolver` | Per-tree layout solution; defaults to `DefaultWorkflowLayoutSolver`. |
| `Install(ITreeComponent)` / `Uninstall(ITreeComponent)` | `void` | Subscribes collection changes; a virtualizing helper also enables the spatial map. |
| `WithSynchronizationContext(SynchronizationContext?)` | `TreeHelper<T>` | Binds virtualization passes to a UI context; `null` runs them inline. |
| `Closing()` / `CloseAsync()` / `Closed()` | `void` / `Task` / `void` | Locks, closes and unlocks the standard commands. |
| `CreateLink(ISlotComponent, ISlotComponent)` | `ILinkComponent` | Returns `LinkDefaultViewModel` by default. |
| `CreateNode(INodeComponent)` / `SetPointer(Anchor)` / `Virtualize(Viewport)` | `void` | Forwards to the tree's standard operations. |
| `ValidateConnection(ISlotComponent, ISlotComponent)` | `bool` | `true` by default; override for a tree-wide rule. |
| `SendConnection` / `ReceiveConnection` / `ResetVirtualLink` | `void` | Connection drag lifecycle. |
| `RaiseConnecting(...)` / `RaiseConnected(...)` | `WorkflowEventHandle` / `void` | Per-attempt veto plumbing. |
| `Submit(IActionPair)` / `Undo()` / `Redo()` / `ClearHistory()` / `MarkDirty()` | `void` | Undo and dirty state. |
| `Arrange(INodeComponent?, WorkflowLayoutOptions?)` | `WorkflowLayoutResult` | Runs `LayoutSolver.Arrange`; throws when not installed. |

Protected virtual `OnVisibleItemsAdded/Removed`, `OnNodeAdded/Removed`, `OnLinkAdded/Removed` raise the corresponding events.

## `NodeHelper` and `NodeHelper<T>`

**Signature:** `class NodeHelper<T> : INodeHelper, INodeEvents, IInputEvents, IConditionalSlotProviders where T : class, INodeComponent`

| Member | Type | Description |
| --- | --- | --- |
| `Component` | `T?` | The installed node. |
| `Input` | `InputRelay` | Pointer and key events. |
| `Providers` | `IList<IConditionalSlotProvider>` | Slot enumerators installed on the node. |
| `SlotAdded` / `SlotRemoved` | `EventHandler<ISlotComponent>` | Raised from `Slots`. |
| `Moving` / `Moved` | `EventHandler<NodeMoveEventArgs>` | Before and after a placement. |
| `Resizing` / `Resized` | `EventHandler<NodeResizeEventArgs>` | Before and after a size change. |
| `Deleting` / `Deleted` | `EventHandler<NodeEventArgs>` | Before and after a deletion. |
| `Install` / `Uninstall` | `void` | Binds the helper. |
| `Closing` / `CloseAsync` / `Closed` | lifecycle | Command lock/close/unlock. |
| `CreateSlot(ISlotComponent)` | `void` | Standard slot creation. |
| `BroadcastAsync(object?, CancellationToken)` / `ReverseBroadcastAsync(...)` | `Task` | Dataflow along `Targets` / `Sources`. |
| `ReceiveAsync(ITaskContext, CancellationToken)` | `Task<object?>` | Returns `null` by default; override for node behaviour. |
| `AccessAsync(IAccessContext, CancellationToken)` | `Task<bool>` | `true` by default. |
| `SetAnchor(Anchor)` / `SetSize(Size)` / `Move(Offset)` | `void` | Standard geometry write, then `MarkDirty` on the tree. |
| `Delete()` | `void` | Standard delete. |
| `RaiseMoving` / `RaiseResizing` / `RaiseDeleting` | `WorkflowEventHandle` | Ask the host; each returns the handle passed to the matching `RaiseMoved`/`RaiseResized`/`RaiseDeleted`. |

## `SlotHelper` and `SlotHelper<T>`

**Signature:** `class SlotHelper<T> : ISlotHelper, ISlotEvents, IInputEvents where T : class, ISlotComponent`

Members: `Component` (`T?`), `Input`, events `TargetAdded`, `TargetRemoved`, `SourceAdded`, `SourceRemoved`; `Install`, `Uninstall`, `Closing`, `CloseAsync`, `Closed`; `SetChannel(SlotChannel)`, `UpdateState()`, `SendConnection()`, `ReceiveConnection()`, `Delete()`.

`ChannelChanging` / `ChannelChanged` (`EventHandler<SlotChannelEventArgs>`) run through `RaiseChannelChanging(SlotChannel from, SlotChannel to)` and `RaiseChannelChanged(...)`. Setting `PreventDefault` on the changing handle keeps the old channel.

## `LinkHelper` and `LinkHelper<T>`

**Signature:** `class LinkHelper<T> : ILinkHelper, ILinkHitTestable, IInputEvents where T : class, ILinkComponent`

Members: `Component` (`T?`), `Input`, `Install`, `Uninstall`, `Closing`, `CloseAsync`, `Closed`, `Delete()`.

| Member | Type | Description |
| --- | --- | --- |
| `Visual` | `object?` | The control that publishes the curve; private setter. |
| `Curve` | `LinkCurve?` | The curve last published by the view. |
| `SetCurve(LinkCurve?, object?)` | `void` | Stores the curve and visual; clearing the curve clears both. |
| `Contains(double x, double y, double radius)` | `bool` | Hit test against the published curve. |

## Example

```csharp
// Replace the tree-wide rule without replacing the tree.
public sealed class NoSelfLinks : TreeHelper<TreeDefaultViewModel>
{
    public override bool ValidateConnection(ISlotComponent sender, ISlotComponent receiver)
        => !ReferenceEquals(sender.Parent, receiver.Parent);
}

var tree = new TreeDefaultViewModel();
var helper = (TreeHelper<TreeDefaultViewModel>)tree.GetHelper();
helper.CreateNode(new NodeDefaultViewModel { Anchor = new Anchor(10, 20, 0) });
```

A helper is installed by `[WorkflowBuilder.*<THelper>]` on a generated component, or by passing it to `SetHelper`. `NodeHelper<T>.Component` is only non-null when the installed node is assignable to `T`; a helper whose `T` does not match observes the node but cannot reach its typed members.
