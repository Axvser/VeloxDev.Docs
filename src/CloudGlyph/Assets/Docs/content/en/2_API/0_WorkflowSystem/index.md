# WorkflowSystem — API Reference

## Namespace: `VeloxDev.WorkflowSystem`

### Core Interfaces

#### `IWorkflowTreeViewModel`
The root container that manages all nodes, slots, and links within a workspace.

| Property | Type | Description |
|---|---|---|
| `Layout` | `CanvasLayout` | Canvas size and offset information |
| `VirtualLink` | `IWorkflowLinkViewModel` | Temporary link visible during connection building |
| `Nodes` | `ObservableCollection<IWorkflowNodeViewModel>` | All node components |
| `Links` | `ObservableCollection<IWorkflowLinkViewModel>` | All link components |
| `LinksMap` | `Dictionary<IWorkflowSlotViewModel, Dictionary<IWorkflowSlotViewModel, IWorkflowLinkViewModel>>` | Slot-to-slot connection mapping |

| Command | Parameter | Description |
|---|---|---|
| `CreateNodeCommand` | `IWorkflowNodeViewModel` | Creates a new node |
| `SetPointerCommand` | `Anchor` | Updates the pointer/cursor position |
| `ResetVirtualLinkCommand` | `null` | Resets the temporary virtual link |
| `SendConnectionCommand` | `IWorkflowSlotViewModel` | Initiates connection from a slot |
| `ReceiveConnectionCommand` | `IWorkflowSlotViewModel` | Completes connection to a slot |
| `SubmitCommand` | `IWorkflowActionPair` | Submits an undoable action |
| `RedoCommand` | `null` | Redoes the last undone action |
| `UndoCommand` | `null` | Undoes the last action |

#### `IWorkflowNodeViewModel`
Represents a single node on the canvas.

| Property | Type | Description |
|---|---|---|
| `Parent` | `IWorkflowTreeViewModel?` | The parent tree component |
| `Anchor` | `Anchor` | Anchor position on the canvas |
| `Size` | `Size` | Width and height of the node |
| `Slots` | `ObservableCollection<IWorkflowSlotViewModel>` | All slots owned by this node |

| Command | Parameter | Description |
|---|---|---|
| `MoveCommand` | `Offset` | Moves the node by an offset |
| `SetAnchorCommand` | `Anchor` | Sets absolute anchor position |
| `SetSizeCommand` | `Size` | Sets node dimensions |
| `CreateSlotCommand` | `IWorkflowSlotViewModel` | Creates a new slot |
| `DeleteCommand` | `null` | Deletes this node and related slots/links |
| `WorkCommand` | `object?` | Executes the node's work logic |
| `BroadcastCommand` | `object?` | Broadcasts data forward to connected nodes |
| `ReverseBroadcastCommand` | `object?` | Broadcasts data backward |
| `CloseCommand` | `null` | Closes the node |

#### `IWorkflowSlotViewModel`
A connection point on a node.

| Property | Type | Description |
|---|---|---|
| `Parent` | `IWorkflowNodeViewModel?` | The parent node |
| `Targets` | `ObservableCollection<IWorkflowSlotViewModel>` | Connected target slots |
| `Sources` | `ObservableCollection<IWorkflowSlotViewModel>` | Connected source slots |
| `Channel` | `SlotChannel` | Input or Output channel |
| `State` | `SlotState` | Current connection state |
| `Anchor` | `Anchor` | Position relative to the parent node |

| Command | Parameter | Description |
|---|---|---|
| `SetChannelCommand` | `SlotChannel` | Changes the slot channel type |
| `SendConnectionCommand` | `IWorkflowSlotViewModel` | Connects to a target slot |
| `ReceiveConnectionCommand` | `IWorkflowSlotViewModel` | Accepts connection from a source |
| `DeleteCommand` | `null` | Deletes this slot and its links |
| `CloseCommand` | `null` | Closes the slot |

#### `IWorkflowLinkViewModel`
Represents a visual connection between two slots.

| Property | Type | Description |
|---|---|---|
| `Sender` | `IWorkflowSlotViewModel` | Source slot |
| `Receiver` | `IWorkflowSlotViewModel` | Target slot |
| `IsVisible` | `bool` | Whether the link is currently visible |
| `UsePolyline` | `bool` | Whether to render as polyline instead of bezier |

---

### Helper System

Helpers define the lifecycle and business logic for each component.

| Base Class | Type Parameter | Key Overrides |
|---|---|---|
| `TreeHelper<T>` | `T : IWorkflowTreeViewModel` | `Install()`, `Uninstall()`, `CreateLink()`, `CreateNode()`, `ValidateConnection()` |
| `NodeHelper<T>` | `T : IWorkflowNodeViewModel` | `Install()`, `Uninstall()`, `WorkAsync()`, `ValidateBroadcastAsync()` |
| `SlotHelper<T>` | `T : IWorkflowSlotViewModel` | `Install()`, `Uninstall()`, `ValidateConnection()` |
| `LinkHelper<T>` | `T : IWorkflowLinkViewModel` | `Install()`, `Uninstall()` |

---

### Spatial System

#### `SpatialGridHashMap<T>`
Spatial indexing for efficient viewport queries.

```csharp
var map = new SpatialGridHashMap<MyItem>(cellSize: 100);
map.Insert(item);
var results = map.Query(viewport).ToList();
map.Remove(item);
```

#### `WorkflowSpatialManager`
Manages spatial indexing for nodes and node pairs (links) at the tree level.

```csharp
var spatial = new WorkflowSpatialManager(tree, cellSize: 200);
Viewport bounds = spatial.GlobalBounds;
```

---

### Enums and Structs

| Type | Description |
|---|---|
| `Anchor` | Position with `Horizontal`, `Vertical`, `Layer` (Z-index) |
| `Size` | Dimensions with `Width`, `Height` |
| `Offset` | Delta with `Horizontal`, `Vertical` |
| `Viewport` | Rectangular region with `X`, `Y`, `Width`, `Height` |
| `CanvasLayout` | Canvas context with `ActualSize`, `OriginSize`, `ViewportOffset`, `ActualOffset` |
| `SlotChannel` | Enum: `Input`, `Output` |
| `SlotState` | Enum: connection state of a slot |
| `CellKey` | Grid cell coordinate used by `SpatialGridHashMap` |

---

### Builder Attributes (Source Generator)

| Attribute | Applied To | Description |
|---|---|---|
| `[WorkflowBuilder.Tree<T>]` | Class | Generates Tree ViewModel boilerplate; `T` must implement `IWorkflowTreeViewModelHelper` |
| `[WorkflowBuilder.Node<T>]` | Class | Generates Node ViewModel boilerplate; `T` must implement `IWorkflowNodeViewModelHelper` |
| `[WorkflowBuilder.Slot<T>]` | Class | Generates Slot ViewModel boilerplate; `T` must implement `IWorkflowSlotViewModelHelper` |
| `[WorkflowBuilder.Link<T>]` | Class | Generates Link ViewModel boilerplate; `T` must implement `IWorkflowLinkViewModelHelper` |
