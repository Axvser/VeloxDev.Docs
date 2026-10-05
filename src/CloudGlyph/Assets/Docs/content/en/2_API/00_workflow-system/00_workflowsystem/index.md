# Workflow System — Namespace: `VeloxDev.WorkflowSystem`

### Builder Attributes (Source Generator)

Partial classes decorated with these attributes receive generated properties, commands, helper wiring and `InitializeWorkflow()`.

| Attribute | Target | Generic constraint | Notes |
|---|---|---|---|
| `[WorkflowBuilder.Tree<T>]` | class | `T : IWorkflowTreeViewModelHelper, new()` | Optional ctor args `virtualLinkType`, `virtualSlotType` |
| `[WorkflowBuilder.Node<T>(workSemaphore = 1)]` | class | `T : IWorkflowNodeViewModelHelper, new()` | `workSemaphore` = concurrent capacity of `ReceiveCommand` |
| `[WorkflowBuilder.Slot<T>]` | class | `T : IWorkflowSlotViewModelHelper, new()` | — |
| `[WorkflowBuilder.Link<T>(slotType = null)]` | class | `T : IWorkflowLinkViewModelHelper, new()` | `slotType` = initial slot type |

**Examples** (shared demo lib, `Examples/Workflow/Common/Lib/ViewModels/Workflow/`) — `[WorkflowBuilder.Tree<AgentHelper>]` on `TreeViewModel.cs` (line 17); `[WorkflowBuilder.Node<NodeHelper>]` on `ControllerViewModel.cs` (line 10); `[WorkflowBuilder.Node<EnumSelectorHelper>(workSemaphore: 1)]` on `EnumSelectorNodeViewModel.cs` (line 12).

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`.*

### Core Interfaces

Every component derives from `IWorkflowViewModel` and exposes `GetHelper()` / `SetHelper(...)`.

#### `IWorkflowViewModel`

```csharp
public interface IWorkflowViewModel : INotifyPropertyChanging, INotifyPropertyChanged
```

| Member | Signature | Notes |
|---|---|---|
| `InitializeWorkflow()` | `void InitializeWorkflow()` | Generator-emitted; installs the Helper |
| `OnPropertyChanging` | `void OnPropertyChanging(string propertyName)` | Pre-change notification |
| `OnPropertyChanged` | `void OnPropertyChanged(string propertyName)` | Change notification |
| `CloseCommand` | `IVeloxCommand CloseCommand { get; }` | Terminates all in-progress tasks (param null) |

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowViewModel.cs`.*

#### `IWorkflowTreeViewModel : IWorkflowViewModel`

| Member | Type | Description |
|---|---|---|
| `Layout` | `CanvasLayout` | Canvas size / offset context |
| `VirtualLink` | `IWorkflowLinkViewModel` | Temporary link visible only while connecting |
| `Nodes` | `ObservableCollection<IWorkflowNodeViewModel>` | All node components |
| `Links` | `ObservableCollection<IWorkflowLinkViewModel>` | All link components |
| `LinksMap` | `Dictionary<IWorkflowSlotViewModel, Dictionary<IWorkflowSlotViewModel, IWorkflowLinkViewModel>>` | Slot→slot connection map |
| `CreateNodeCommand` | `IVeloxCommand` | param `IWorkflowNodeViewModel` |
| `SetPointerCommand` | `IVeloxCommand` | param `Anchor` |
| `ResetVirtualLinkCommand` | `IVeloxCommand` | param null |
| `SendConnectionCommand` | `IVeloxCommand` | param `IWorkflowSlotViewModel` |
| `ReceiveConnectionCommand` | `IVeloxCommand` | param `IWorkflowSlotViewModel` |
| `SubmitCommand` | `IVeloxCommand` | param `IWorkflowActionPair` |
| `UndoCommand` | `IVeloxCommand` | param null |
| `RedoCommand` | `IVeloxCommand` | param null |

**`IWorkflowTreeViewModelHelper : IWorkflowHelper`**

```csharp
public interface IWorkflowTreeViewModelHelper : IWorkflowHelper
```

Events: `NodeAdded` / `NodeRemoved` (`EventHandler<IWorkflowNodeViewModel>`), `LinkAdded` / `LinkRemoved` (`EventHandler<IWorkflowLinkViewModel>`), `VisibleItemAdded` / `VisibleItemRemoved` (`EventHandler<IWorkflowViewModel>`).

| Method | Signature | Notes |
|---|---|---|
| `Install` / `Uninstall` | `void Install(IWorkflowTreeViewModel tree)` / `void Uninstall(IWorkflowTreeViewModel tree)` | Lifecycle hook; `Install` subscribes `Nodes`/`Links` collections |
| `CreateNode` | `void CreateNode(IWorkflowNodeViewModel node)` | → `StandardCreateNode` |
| `CreateLink` | `IWorkflowLinkViewModel CreateLink(IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | Default returns `LinkDefaultViewModel` |
| `SetPointer` | `void SetPointer(Anchor anchor)` | Moves the virtual link receiver |
| `ValidateConnection` | `bool ValidateConnection(IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | Overridable; default `true` |
| `SendConnection` / `ReceiveConnection` | `void SendConnection(IWorkflowSlotViewModel slot)` / `void ReceiveConnection(IWorkflowSlotViewModel slot)` | Two-phase connection |
| `ResetVirtualLink` | `void ResetVirtualLink()` | Hides the virtual link |
| `Virtualize` | `void Virtualize(Viewport viewport)` | Spatial virtualization |
| `Submit` | `void Submit(IWorkflowActionPair actionPair)` | Push onto undo stack |
| `Redo` / `Undo` / `ClearHistory` | `void Redo()` / `void Undo()` / `void ClearHistory()` | Stack ops |
| `MarkDirty` | `void MarkDirty()` | Flags the tree for re-virtualization |

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowTreeViewModel.cs`.*

#### `IWorkflowNodeViewModel : IWorkflowViewModel`

| Member | Type | Description |
|---|---|---|
| `Parent` | `IWorkflowTreeViewModel?` | Owning tree |
| `Anchor` | `Anchor` | Canvas position (X, Y, layer) |
| `Size` | `Size` | Width / height |
| `Slots` | `ObservableCollection<IWorkflowSlotViewModel>` | Owned slots |
| `MoveCommand` | `IVeloxCommand` | param `Offset` |
| `SetAnchorCommand` | `IVeloxCommand` | param `Anchor` |
| `SetSizeCommand` | `IVeloxCommand` | param `Size` |
| `CreateSlotCommand` | `IVeloxCommand` | param `IWorkflowSlotViewModel` |
| `DeleteCommand` | `IVeloxCommand` | param null; cascades to slots and links |
| `ReceiveCommand` | `IVeloxCommand` | param nullable `ITaskContext` |
| `BroadcastCommand` | `IVeloxCommand` | forward broadcast, param nullable |
| `ReverseBroadcastCommand` | `IVeloxCommand` | backward broadcast, param nullable |

**`IWorkflowNodeViewModelHelper : IWorkflowHelper`**

Events: `SlotAdded` / `SlotRemoved` (`EventHandler<IWorkflowSlotViewModel>`).

| Method | Signature | Notes |
|---|---|---|
| `Install` / `Uninstall` | `void Install(IWorkflowNodeViewModel node)` / `void Uninstall(IWorkflowNodeViewModel node)` | Lifecycle hook |
| `CreateSlot` | `void CreateSlot(IWorkflowSlotViewModel slot)` | → `StandardCreateSlot` |
| `Move` / `SetAnchor` / `SetSize` | `void Move(Offset)` / `void SetAnchor(Anchor)` / `void SetSize(Size)` | Mutate geometry + `MarkDirty` |
| `ReceiveAsync` | `Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)` | **The single execution entry** (nullable data/sender/receiver); returning a non-null value lets the Compiler chain results |
| `BroadcastAsync` | `Task BroadcastAsync(object? parameter, CancellationToken ct)` | Drive all connected downstream `ReceiveCommand`s |
| `ReverseBroadcastAsync` | `Task ReverseBroadcastAsync(object? parameter, CancellationToken ct)` | Drive all connected upstream `ReceiveCommand`s |
| `AccessAsync` | `Task<bool> AccessAsync(IAccessContext context, CancellationToken ct)` | Dataflow access gate for an edge (Sender→Receiver) + phase + payload; compile phase = static check (Data null), runtime phase = real-time check (Data = payload); default `true` |
| `Delete` | `void Delete()` | → `StandardDelete` (atomic, undoable) |

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`.*

> `ReceiveAsync` is the single execution entry shared by the Compiler (engine-driven) and the non-Compiler (node-driven broadcast) paths — each path reaches it with a different context. Entry points, parameters, and timing: see `Execution Mechanism`.

#### `IWorkflowSlotViewModel : IWorkflowViewModel`

| Member | Type | Description |
|---|---|---|
| `Targets` / `Sources` | `ObservableCollection<IWorkflowSlotViewModel>` | Connected peers (outgoing / incoming) |
| `Parent` | `IWorkflowNodeViewModel?` | Owning node |
| `Channel` | `SlotChannel` | Connection capacity (flags) |
| `State` | `SlotState` | Connection state (flags) |
| `Anchor` | `Anchor` | Position on the canvas |
| `SetChannelCommand` | `IVeloxCommand` | param `SlotChannel` |
| `SendConnectionCommand` | `IVeloxCommand` | start as sender |
| `ReceiveConnectionCommand` | `IVeloxCommand` | accept as receiver |
| `DeleteCommand` | `IVeloxCommand` | param null |

**`IWorkflowSlotViewModelHelper : IWorkflowHelper`** — events `TargetAdded/Removed`, `SourceAdded/Removed`; methods `Install/Uninstall`, `SetChannel(SlotChannel)`, `UpdateState()`, `SendConnection()`, `ReceiveConnection()`, `Delete()`.

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowSlotViewModel.cs`.*

#### `IWorkflowLinkViewModel : IWorkflowViewModel`

| Member | Type | Description |
|---|---|---|
| `Sender` | `IWorkflowSlotViewModel` | Source slot |
| `Receiver` | `IWorkflowSlotViewModel` | Target slot |
| `IsVisible` | `bool` | Rendering visibility |
| `DeleteCommand` | `IVeloxCommand` | param null |

**`IWorkflowLinkViewModelHelper : IWorkflowHelper`** — `Install/Uninstall(IWorkflowLinkViewModel)`, `Delete()`.

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowLinkViewModel.cs`.*

#### Other interfaces

| Type | Signature / members |
|---|---|
| `IWorkflowActionPair` | `Action Redo { get; }`, `Action Undo { get; }` |
| `IWorkflowIdentifiable` | `string RuntimeId { get; }` — unique for the component lifetime |
| `IContext` | Root contract carrying the universal payload `object? Data { get; }` — real at runtime, null at compile identity; base of `IAccessContext` (`ITaskContext`, `IRuntimeContext`, `ICompileContext`) |
| `IAccessContext : IContext` | `bool IsCompilePhase` (true = compile-time static check / no data, false = runtime real-time check), `IWorkflowSlotViewModel? Sender`, `IWorkflowSlotViewModel? Receiver` — a dataflow access (edge + phase); the parameter of `AccessAsync` |
| `ITaskContext : IAccessContext` | Inherits `Data`/`Sender`/`Receiver`/`IsCompilePhase` — nullable payload passed to `ReceiveCommand → ReceiveAsync` |
| `ISlotProvider` | `IEnumerable<SlotDefinition> GetSlots()` — drives a `SlotEnumerator` with an instance-based slot list |
| `ISpatialMap<T>` | `T : class, ISpatialBoundsProvider`; `Insert(T)`, `Remove(T)`, `Query(Viewport)`, `Clear()`, `Bounds` |
| `ISpatialBoundsProvider` | `Viewport Bounds { get; }` + `INotifyPropertyChanged`; raise `PropertyChanged("Bounds")` on change |

*Sources: `Interfaces/WorkflowSystem/IWorkflowActionPair.cs`, `IWorkflowIdentifiable.cs`, `IContext.cs`, `ITaskContext.cs`, `ISlotProvider.cs`, `ISpatialMap.cs`, `ISpatialBoundsProvider.cs`.*

### Value Types, Geometry Classes and Enums

| Type | Description |
|---|---|
| `Anchor(left, top, layer)` | Geometry class (`sealed partial class`); position. `ICloneable`, `IEquatable<Anchor>`; `==`/`!=`/`+`/`-` operators |
| `Size(width, height)` | Geometry class (`sealed partial class`); dimensions. `ICloneable`, `IEquatable<Size>`; `==`/`!=`/`+`/`-` operators |
| `Offset(left, top)` | Geometry class (`sealed partial class`); delta vector. `ICloneable`, `IEquatable<Offset>`; `==`/`!=`/`+`/`-` operators |
| `Viewport(left, top, width, height)` | `readonly struct`; `Empty`, `Right`, `Bottom`, `IsEmpty`, `Contains`, `IntersectsWith`, `Union`, `==`/`!=` |
| `CanvasLayout` | `OriginSize`, `PositiveOffset`, `NegativeOffset`, `ActualSize`, `ActualOffset`, `ViewportOffset`; `AdaptTo(Size)`; `UpdateCommand` |
| `CellKey(x, y)` | `readonly struct` grid cell coordinate; `==`/`!=` |
| `TaskContext(data, sender, receiver)` | `readonly struct : ITaskContext`; `Deconstruct(out data, out sender, out receiver)` |
| `WorkflowActionPair(redo, undo)` | `readonly struct : IWorkflowActionPair` |
| `SlotChannel` | `[Flags] int`: `None=0`, `OneTarget=1`, `OneSource=2`, `OneBoth=3`, `MultipleTargets=4`, `MultipleSources=8`, `MultipleBoth=12` |
| `SlotState` | `[Flags] int`: `StandBy=1`, `PreviewSender=2`, `PreviewReceiver=4`, `Sender=8`, `Receiver=16` |

*Sources: `GUI/GeometryModels/Anchor.cs`, `GUI/GeometryModels/Size.cs`, `GUI/GeometryModels/Offset.cs`, `GUI/GeometryModels/Viewport.cs`, `GUI/GeometryModels/CanvasLayout.cs`, `GUI/Virtualization/CellKey.cs`, `TaskContext.cs`, `WorkflowActionPair.cs`, `Enums/Slot.cs` in `Src/Core/VeloxDev.Core/WorkflowSystem/`.*

### Default ViewModels and Helpers

| Default ViewModel | Default Helper | Purpose |
|---|---|---|
| `TreeDefaultViewModel` | `TreeHelper<T>` | Root container; `CreateLink` returns `LinkDefaultViewModel` |
| `NodeDefaultViewModel` | `NodeHelper<T>` | Node with `Move/SetAnchor/SetSize/CreateSlot/Receive/Broadcast/ReverseBroadcast/Delete` |
| `SlotDefaultViewModel` | `SlotHelper<T>` | Slot with channel/state handling |
| `LinkDefaultViewModel` | `LinkHelper<T>` | Link with `Delete` |

Notes:

- `TreeHelper()` disables virtualization; `TreeHelper(double cellSize)` enables it. The type is annotated `[Tickable(channel: nameof(TreeHelper), fps: 10)]` and calls `tree.EnableMap(CellSize, VisibleItems)` on `Install`. `CellSize` defaults to `200`.
- `NodeHelper.SetAnchor/SetSize/Move` call `Component.Parent.GetHelper().MarkDirty()` after mutating.
- `NodeDefaultViewModel`'s generated `Receive` handler (the body behind `ReceiveCommand`, lines 115-120) passes the parameter through when it is already an `ITaskContext`, else wraps it as `new TaskContext(parameter)`, and calls `Helper.ReceiveAsync(ctx, ct)` — a single receive path carrying nullable data/sender/receiver.
- All four default ViewModels implement `IWorkflowIdentifiable` (`RuntimeId = Guid.NewGuid().ToString("N")`).

*Sources: `Templates/ViewModels/*.cs`, `Templates/Helpers/*.cs`.*

### `NodeLayoutAttributes`

| Attribute | Effect |
|---|---|
| `[DefaultAnchor(horizontal = 0, vertical = 0, layer = 0)]` | Source generator bakes the default `Anchor` into the backing-field initializer |
| `[DefaultSize(width = 0, height = 0)]` | Source generator bakes the default `Size` into the backing-field initializer |

*Source: `Templates/NodeLayoutAttributes.cs`.*

### Selector System (`SelectorEx`)

| Type | Description |
|---|---|
| `SlotEnumerator<TSlot>` | Dynamic slot collection (`TSlot : IWorkflowSlotViewModel, new()`). `SetSelector(object?)` (a `Type`, type-name string, or `ISlotProvider`), `TrySelect(object, out TSlot?)`, `Items`, `Count`, indexer, `CurrentValue`, `SelectorType`, `SelectorTypeName`, `Install(parent, memberName)`, `Uninstall()`. Selector switches are submitted as undoable actions. An **enum** selector remembers its per-type state across switches (slot layout and wiring); a **provider** selector does not — a provider is a *value*, not a type, so two instances of one class can expose different ports and the port set is rebuilt on every call. Rebuilding a port set re-wires the links that fed the old branches, matching by name when the selector type did not change and by position when it did. |
| `ConditionalSlot<TSlot>` | One entry in `SlotEnumerator.Items`: `Name`, `Value`, `Slot`. |
| `SlotDefinition(value, label)` | Entry produced by an `ISlotProvider`. |
| `ISlotProvider` | `IEnumerable<SlotDefinition> GetSlots()` — drives an enumerator with arbitrary routes. |
| `[SlotSelectors(params Type[] or params string[])]` | `VeloxDev.AI` attribute declaring allowed selector types on a `SlotEnumerator` property. |
| `IConditionalSlotProvider<TSlot>` | Contract implemented by `SlotEnumerator<TSlot>`: `Parent`, `SelectorTypeName`, `Items`, `CurrentValue`, `TrySelect`, `SetSelector`, `Install`, `Uninstall`. |
| `IConditionalSlotProvider` | The **non-generic** view of the same object, which `SlotEnumerator<TSlot>` implements explicitly — so a caller holding only an `object` (the Agent toolkit, for one) can open the selector without reflection: `Parent`, `SelectorTypeName`, `SelectorType`, `CurrentValue`, `Slots` (`IReadOnlyList<IConditionalSlot>`), `TrySelect(object, out IWorkflowSlotViewModel?)`, `SetSelector(object?)`. `Slots` is a projection of `Items`, not a copy. |
| `IConditionalSlot` | The non-generic form of `ConditionalSlot<TSlot>`: `Name`, `Value`, `Slot` (`IWorkflowSlotViewModel`). |

`TrySelect` is a dictionary lookup over `conditionMap` (expected `O(1)`). `CurrentValue` getter returns the string form; setter accepts string / enum / numeric and normalizes.

*Sources: `SelectorEx/SlotEnumerator.cs`, `SelectorEx/ConditionalSlot.cs`, `SelectorEx/SlotDefinition.cs`, `Interfaces/WorkflowSystem/ISlotProvider.cs`, `Interfaces/WorkflowSystem/IConditionalSlotProvider.cs`, `Src/Core/VeloxDev.Core/AI/SlotSelectorsAttribute.cs`.*

### Spatial System

| Type | Description |
|---|---|
| `SpatialGridHashMap<T>` | Generic grid spatial hash (`T : class, ISpatialBoundsProvider`). `Insert`, `Remove`, `Query(Viewport)`, `Clear`, `Bounds`. Cell size set in ctor (`Math.Max(1d, cellSize)`). |
| `WorkflowSpatialManager` | Tree-level manager indexing nodes (`NodeBoundsProvider`) and node pairs (`NodePairBoundsProvider`, which represent links). `GlobalBounds`, `QueryNodes(Viewport)`, `QueryAgentBounds` (internal, depth-expanded). |
| `WorkflowSpatialEx` | Extensions: `EnableMap(tree, cellSize, observable)`, `Virtualize(tree, viewport)`, `QueryNodes(tree, viewport)`, `ClearMap(tree)`. |
| `ISpatialMap<T>` / `ISpatialBoundsProvider` | Spatial abstractions (see "Other interfaces" above). |

*Sources: `WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs`, `WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs`, `WorkflowSystem/GUI/Virtualization/NodeBoundsProvider.cs`, `WorkflowSystem/GUI/Virtualization/NodePairBoundsProvider.cs`, `WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`, `Interfaces/WorkflowSystem/ISpatialMap.cs`, `Interfaces/WorkflowSystem/ISpatialBoundsProvider.cs`.*

### Render-readiness helpers (core, GUI-agnostic)

| Type | Description |
|---|---|
| `WorkflowSlotUpdateGate` | `IsLinkRenderReady(IWorkflowLinkViewModel)` — true when both endpoint anchors are non-NaN (or not yet mounted) |
| `WorkflowLinkRenderEx` | `bool IsRenderReady(this IWorkflowLinkViewModel)` — `IsVisible && WorkflowSlotUpdateGate.IsLinkRenderReady(link)` |
| `WorkflowGuard` | `[Conditional("DEBUG")] Fail(message)` — debug-only contract guard throwing `InvalidOperationException` |

*Sources: `WorkflowSlotUpdateGate.cs`, `WorkflowLinkRenderEx.cs`, `WorkflowGuard.cs`.*

### Link interaction (`LinkInteraction`)

The hub every GUI forwards link input into, one instance per tree. `LinkInteraction.For(IWorkflowTreeViewModel)` returns the shared instance; a host publishes translated input with `Publish(PointerEvent)`, `Publish(KeyEvent)`, and — when its own menu opens or closes — `Publish(ContextMenuEvent)`, then subscribes to the outcome instead of re-deriving hit testing per platform.

| Member | Kind | Description |
|---|---|---|
| `For(tree)` | static | The one hub for a tree (kept as long as the tree lives). |
| `HoveredLink`, `HitRadius` | property | The link under the pointer; reach either side of a drawn curve. |
| `AutoHighlight`, `AutoDelete`, `IsSuspended` | property | Hover highlight and Delete-to-remove are on by default; `IsSuspended` is set while a host menu is open, so pointer movement over the menu does not clear the selection. |
| `HoverChanged`, `LinkPressed`, `LinkDeleteRequested` | event | Outcome events; Delete is requested, not performed, unless `AutoDelete` is on. |
| `PreviewHoverChanged`, `PreviewLinkPressed`, `PreviewLinkDeleteRequested` | event | Preview phase, refusable per event through `WorkflowEventHandle.PreventDefault`. |
| `ContextMenuRequesting`, `ContextMenuRequested` | event | Right-press phases for whoever shows the menu; refusing in `Requesting` suppresses `Requested` by construction. |
| `ContextMenuOpened`, `ContextMenuClosed` | event | Raised after `Publish(ContextMenuEvent)` reports a menu on screen / gone; hover suspension tracks them. |
| `ContextMenuDismissRequested` | event | Raised when the link an open menu was about leaves the tree, asking the host to take that menu down — so a menu never outlives its link. The host closes it and reports `ContextMenuPhase.Closed`. |

*Sources: `WorkflowSystem/GUI/Events/LinkInteraction.cs`, `WorkflowSystem/GUI/Events/Link/*.cs`, `WorkflowSystem/GUI/Events/Menu/*.cs`.*
