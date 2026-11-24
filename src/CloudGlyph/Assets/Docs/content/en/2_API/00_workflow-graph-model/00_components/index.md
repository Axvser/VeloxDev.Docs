# Component contracts

Every workflow type implements `IWorkflowComponent`; the four roles add their own state and commands. A helper is a separate object installed on the component, so behaviour can be replaced without replacing the model.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`. The command properties are typed `IVeloxCommand` from `VeloxDev.MVVM`.

## IWorkflowComponent

**Signature:** `interface IWorkflowComponent : INotifyPropertyChanging, INotifyPropertyChanged`

| Member | Type | Description |
| --- | --- | --- |
| `InitializeWorkflow()` | `void` | Installs the component's helper and seeds its generated members. |
| `OnPropertyChanging(string)` | `void` | Raises the pre-change notification for `propertyName`. |
| `OnPropertyChanged(string)` | `void` | Raises the post-change notification for `propertyName`. |
| `CloseCommand` | `IVeloxCommand` | Terminates all running tasks owned by the component. |

`IRuntimeIdentifiable` (same namespace) adds `string RuntimeId { get; }`. The default view models assign a new GUID string at construction; the id is stable across collection mutations and is what a checkpoint uses as a node key.

## ITreeComponent

**Signature:** `interface ITreeComponent : IWorkflowComponent`

| Member | Type | Description |
| --- | --- | --- |
| `Layout` | `CanvasLayout` | Canvas size, offsets, zoom scale and zoom centre. |
| `VirtualLink` | `ILinkComponent` | The provisional link shown during a connection drag. |
| `Nodes` | `ObservableCollection<INodeComponent>` | Every node in the workspace. |
| `Links` | `ObservableCollection<ILinkComponent>` | Every link in the workspace. |
| `LinksMap` | `Dictionary<ISlotComponent, Dictionary<ISlotComponent, ILinkComponent>>` | Sender slot → receiver slot → link. |
| `CreateNodeCommand` | `IVeloxCommand` | Parameter `INodeComponent`; one undoable step. |
| `SetPointerCommand` | `IVeloxCommand` | Parameter `Anchor`; moves the virtual link's receiver. |
| `ResetVirtualLinkCommand` | `IVeloxCommand` | Clears the provisional link. |
| `SendConnectionCommand` | `IVeloxCommand` | Parameter `ISlotComponent` (sender). |
| `ReceiveConnectionCommand` | `IVeloxCommand` | Parameter `ISlotComponent` (receiver). |
| `SubmitCommand` | `IVeloxCommand` | Parameter `IActionPair`. |
| `RedoCommand` / `UndoCommand` | `IVeloxCommand` | No parameter. |
| `GetHelper()` / `SetHelper(ITreeHelper)` | `ITreeHelper` / `void` | Reads or replaces the installed helper. |

## ITreeHelper

**Signature:** `interface ITreeHelper : IWorkflowHelper`

Events: `NodeAdded`, `NodeRemoved`, `EventHandler<INodeComponent>`; `LinkAdded`, `LinkRemoved`, `EventHandler<ILinkComponent>`; `VisibleItemAdded`, `VisibleItemRemoved`, `EventHandler<IWorkflowComponent>`.

Properties: `VisibleItems` (`ObservableCollection<IWorkflowComponent>`), `Viewport` (`Viewport`).

| Method | Returns | Description |
| --- | --- | --- |
| `Install(ITreeComponent)` / `Uninstall(ITreeComponent)` | `void` | Binds or detaches the helper. |
| `CreateNode(INodeComponent)` | `void` | Adds a node as one undoable step. |
| `CreateLink(ISlotComponent, ISlotComponent)` | `ILinkComponent` | Builds the link type for the tree. |
| `SetPointer(Anchor)` | `void` | Moves the provisional receiver. |
| `ValidateConnection(ISlotComponent, ISlotComponent)` | `bool` | The tree's own connection rule; `true` by default. |
| `SendConnection(ISlotComponent)` / `ReceiveConnection(ISlotComponent)` | `void` | Starts or completes a connection drag. |
| `ResetVirtualLink()` | `void` | Clears the provisional link. |
| `Virtualize(Viewport)` | `void` | Rebuilds `VisibleItems` for a viewport. |
| `Submit(IActionPair)` / `Undo()` / `Redo()` / `ClearHistory()` | `void` | Undo-history control. |
| `MarkDirty()` | `void` | Flags the tree for a virtualization pass. |

## INodeComponent

**Signature:** `interface INodeComponent : IWorkflowComponent`

| Member | Type | Description |
| --- | --- | --- |
| `Parent` | `ITreeComponent?` | Owning tree. |
| `Anchor` | `Anchor` | World position; the getter returns a scale-collapsed view value. |
| `Size` | `Size` | World size; the getter returns a scale-collapsed view value. |
| `Slots` | `ObservableCollection<ISlotComponent>` | Ports owned by the node. |
| `MoveCommand` | `IVeloxCommand` | Parameter `Offset` (view-space delta). |
| `SetAnchorCommand` / `SetSizeCommand` | `IVeloxCommand` | Parameters `Anchor` / `Size` (world values). |
| `CreateSlotCommand` | `IVeloxCommand` | Parameter `ISlotComponent`. |
| `DeleteCommand` | `IVeloxCommand` | Deletes the node, its slots and its links as one step. |
| `ReceiveCommand` | `IVeloxCommand` | Parameter `ITaskContext?`; the single execution entry. |
| `BroadcastCommand` / `ReverseBroadcastCommand` | `IVeloxCommand` | Parameter `object?`; dataflow along `Targets` / `Sources`. |
| `GetHelper()` / `SetHelper(INodeHelper)` | `INodeHelper` / `void` | Reads or replaces the installed helper. |

## INodeHelper

**Signature:** `interface INodeHelper : IWorkflowHelper`

Events: `SlotAdded`, `SlotRemoved` (`EventHandler<ISlotComponent>`).

| Method | Returns | Description |
| --- | --- | --- |
| `Install(INodeComponent)` / `Uninstall(INodeComponent)` | `void` | Binds or detaches the helper. |
| `CreateSlot(ISlotComponent)` | `void` | Adds a port. |
| `Move(Offset)` / `SetAnchor(Anchor)` / `SetSize(Size)` | `void` | Geometry changes. |
| `ReceiveAsync(ITaskContext, CancellationToken)` | `Task<object?>` | Runs the node; a non-null result chains to the next node. |
| `BroadcastAsync(object?, CancellationToken)` | `Task` | Sends along every outgoing edge. |
| `ReverseBroadcastAsync(object?, CancellationToken)` | `Task` | Sends along every incoming edge. |
| `AccessAsync(IAccessContext, CancellationToken)` | `Task<bool>` | Edge access check reused by compile and runtime phases. |
| `Delete()` | `void` | Deletes the node. |

`AccessAsync` receives `IAccessContext`: `Sender` and `Receiver` are the two end slots, `Data` is the payload (null at compile time), and `IsCompilePhase` distinguishes the phases. Returning `false` treats the edge as unconnected.

## ISlotComponent

**Signature:** `interface ISlotComponent : IWorkflowComponent`

| Member | Type | Description |
| --- | --- | --- |
| `Targets` | `ObservableCollection<ISlotComponent>` | Slots this slot connects out to. |
| `Sources` | `ObservableCollection<ISlotComponent>` | Slots that connect into this slot. |
| `Parent` | `INodeComponent?` | Owning node. |
| `Channel` | `SlotChannel` | Direction and capacity (see [Connection rules](../../02_connection-rules-preview/00_connection-rules/index.md)). |
| `State` | `SlotState` | Connection and drag state flags. |
| `Anchor` | `Anchor` | Port position on the canvas. |
| `SetChannelCommand` | `IVeloxCommand` | Parameter `SlotChannel`; not an undo entry. |
| `SendConnectionCommand` / `ReceiveConnectionCommand` | `IVeloxCommand` | Start or accept a connection at this slot. |
| `DeleteCommand` | `IVeloxCommand` | Deletes the slot and its links. |
| `GetHelper()` / `SetHelper(ISlotHelper)` | `ISlotHelper` / `void` | Reads or replaces the installed helper. |

## ISlotHelper

**Signature:** `interface ISlotHelper : IWorkflowHelper`

Events: `TargetAdded`, `TargetRemoved`, `SourceAdded`, `SourceRemoved` (`EventHandler<ISlotComponent>`).

Methods: `Install(ISlotComponent)`, `Uninstall(ISlotComponent)`, `SetChannel(SlotChannel)`, `UpdateState()`, `SendConnection()`, `ReceiveConnection()`, `Delete()`.

## ILinkComponent

**Signature:** `interface ILinkComponent : IWorkflowComponent`

| Member | Type | Description |
| --- | --- | --- |
| `Sender` | `ISlotComponent` | Source port. |
| `Receiver` | `ISlotComponent` | Destination port. |
| `IsVisible` | `bool` | Whether the link is drawn. |
| `DeleteCommand` | `IVeloxCommand` | Deletes the link as one undoable step. |
| `GetHelper()` / `SetHelper(ILinkHelper)` | `ILinkHelper` / `void` | Reads or replaces the installed helper. |

## ILinkHelper

**Signature:** `interface ILinkHelper : IWorkflowHelper`

Methods: `Install(ILinkComponent)`, `Uninstall(ILinkComponent)`, `Delete()`.

## IWorkflowHelper

**Signature:** `interface IWorkflowHelper`

| Member | Type | Description |
| --- | --- | --- |
| `Closing()` | `void` | Locks the helper's commands before close. |
| `CloseAsync()` | `Task` | Closes the component safely. |
| `Closed()` | `void` | Unlocks the helper's commands after close. |

## Example

```csharp
ITreeComponent tree = new TreeDefaultViewModel();
INodeComponent node = new NodeDefaultViewModel
{
    Anchor = new Anchor(60, 80, 0),
    Size = new Size(220, 120),
};
tree.GetHelper().CreateNode(node);

// A detached node still reports its identity and helper.
Console.WriteLine($"{node.RuntimeId.Length} {node.GetHelper().GetType().Name}");
```
