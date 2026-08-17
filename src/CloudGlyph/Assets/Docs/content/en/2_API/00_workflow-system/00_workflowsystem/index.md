# Workflow System — Namespace: `VeloxDev.WorkflowSystem`

### Builder Attributes (Source Generator)

Partial classes decorated with these attributes receive generated properties, commands, helper wiring and `InitializeWorkflow()`.

| Attribute | Target | Generic constraint | Notes |
|---|---|---|---|
| `[WorkflowBuilder.Tree<T>]` | class | `T : IWorkflowTreeViewModelHelper, new()` | Optional ctor args `virtualLinkType`, `virtualSlotType` |
| `[WorkflowBuilder.Node<T>(workSemaphore = 1)]` | class | `T : IWorkflowNodeViewModelHelper, new()` | `workSemaphore` = concurrent capacity of `ReceiveCommand` |
| `[WorkflowBuilder.Slot<T>]` | class | `T : IWorkflowSlotViewModelHelper, new()` | — |
| `[WorkflowBuilder.Link<T>(slotType = null)]` | class | `T : IWorkflowLinkViewModelHelper, new()` | `slotType` = initial slot type |

**Example** — demo node decoration: `Examples/Workflow/Common/Lib/ViewModels/Workflow/NodeViewModel.cs`, line 11-14 (`[WorkflowBuilder.Node<HttpHelper<NodeViewModel>>(workSemaphore: 5)]`).

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`, lines 3-50.*

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

### Value Types and Enums

| Type | Description |
|---|---|
| `Anchor(left, top, layer)` | Position; `ICloneable`, `IEquatable<Anchor>`, `IInterpolable`; `==`/`!=`/`+`/`-` operators |
| `Size(width, height)` | Dimensions; `ICloneable`, `IEquatable<Size>`, `IInterpolable` |
| `Offset(left, top)` | Delta vector; `ICloneable`, `IEquatable<Offset>`, `IInterpolable` |
| `Viewport(left, top, width, height)` | `readonly struct`; `Empty`, `Right`, `Bottom`, `IsEmpty`, `Contains`, `IntersectsWith`, `Union`, `==`/`!=` |
| `CanvasLayout` | `OriginSize`, `PositiveOffset`, `NegativeOffset`, `ActualSize`, `ActualOffset`, `ViewportOffset`; `AdaptTo(Size)`; `UpdateCommand` |
| `CellKey(x, y)` | `readonly struct` grid cell coordinate; `==`/`!=` |
| `TaskContext(data, sender, receiver)` | `readonly struct : ITaskContext`; `Deconstruct(out data, out sender, out receiver)` |
| `WorkflowActionPair(redo, undo)` | `readonly struct : IWorkflowActionPair` |
| `SlotChannel` | `[Flags] int`: `None=0`, `OneTarget=1`, `OneSource=2`, `OneBoth=3`, `MultipleTargets=4`, `MultipleSources=8`, `MultipleBoth=12` |
| `SlotState` | `[Flags] int`: `StandBy=1`, `PreviewSender=2`, `PreviewReceiver=4`, `Sender=8`, `Receiver=16` |

*Sources: `Anchor.cs`, `Size.cs`, `Offset.cs`, `Viewport.cs`, `CanvasLayout.cs`, `CellKey.cs`, `TaskContext.cs`, `WorkflowActionPair.cs`, `Enums/Slot.cs` in `Src/Core/VeloxDev.Core/WorkflowSystem/`.*

### Default ViewModels and Helpers

| Default ViewModel | Default Helper | Purpose |
|---|---|---|
| `TreeDefaultViewModel` | `TreeHelper<T>` | Root container; `CreateLink` returns `LinkDefaultViewModel` |
| `NodeDefaultViewModel` | `NodeHelper<T>` | Node with `Move/SetAnchor/SetSize/CreateSlot/Receive/Broadcast/ReverseBroadcast/Delete` |
| `SlotDefaultViewModel` | `SlotHelper<T>` | Slot with channel/state handling |
| `LinkDefaultViewModel` | `LinkHelper<T>` | Link with `Delete` |

Notes:

- `TreeHelper()` disables virtualization; `TreeHelper(double cellSize)` enables it. The type is annotated `[MonoBehaviour(channel: nameof(TreeHelper), fps: 10)]` and calls `tree.EnableMap(CellSize, VisibleItems)` on `Install`. `CellSize` defaults to `200`.
- `NodeHelper.SetAnchor/SetSize/Move` call `Component.Parent.GetHelper().MarkDirty()` after mutating.
- `NodeDefaultViewModel.ReceiveCommand` wraps the parameter into `TaskContext` and calls `Helper.ReceiveAsync(ctx, ct)` — a single receive path carrying nullable data/sender/receiver (`NodeDefaultViewModel.cs` lines 67-72).
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
| `SlotEnumerator<TSlot>` | Dynamic slot collection (`TSlot : IWorkflowSlotViewModel, new()`). `SetSelector(object?)` (a `Type`, type-name string, or `ISlotProvider`), `TrySelect(object, out TSlot?)`, `Items`, `Count`, indexer, `CurrentValue`, `SelectorType`, `SelectorTypeName`, `Install(parent, memberName)`, `Uninstall()`. Selector switches are submitted as undoable actions; per-type slot state is remembered across switches. |
| `ConditionalSlot<TSlot>` | One entry in `SlotEnumerator.Items`: `Name`, `Value`, `Slot`. |
| `SlotDefinition(value, label)` | Entry produced by an `ISlotProvider`. |
| `ISlotProvider` | `IEnumerable<SlotDefinition> GetSlots()` — drives an enumerator with arbitrary routes. |
| `[SlotSelectors(params Type[] or params string[])]` | `VeloxDev.AI` attribute declaring allowed selector types on a `SlotEnumerator` property. |
| `IConditionalSlotProvider<TSlot>` | Contract implemented by `SlotEnumerator<TSlot>`: `Parent`, `SelectorTypeName`, `Items`, `CurrentValue`, `TrySelect`, `SetSelector`, `Install`, `Uninstall`. |

`TrySelect` is a dictionary lookup over `conditionMap` (expected `O(1)`). `CurrentValue` getter returns the string form; setter accepts string / enum / numeric and normalizes.

*Sources: `SelectorEx/SlotEnumerator.cs`, `SelectorEx/ConditionalSlot.cs`, `SelectorEx/SlotDefinition.cs`, `Interfaces/WorkflowSystem/ISlotProvider.cs`, `Interfaces/WorkflowSystem/IConditionalSlotProvider.cs`, `Src/Core/VeloxDev.Core/AI/SlotSelectorsAttribute.cs`.*

### Spatial System

| Type | Description |
|---|---|
| `SpatialGridHashMap<T>` | Generic grid spatial hash (`T : class, ISpatialBoundsProvider`). `Insert`, `Remove`, `Query(Viewport)`, `Clear`, `Bounds`. Cell size set in ctor (`Math.Max(1d, cellSize)`). |
| `WorkflowSpatialManager` | Tree-level manager indexing nodes (`NodeBoundsProvider`) and node pairs (`NodePairBoundsProvider`, which represent links). `GlobalBounds`, `QueryNodes(Viewport)`, `QueryAgentBounds` (internal, depth-expanded). |
| `WorkflowSpatialEx` | Extensions: `EnableMap(tree, cellSize, observable)`, `Virtualize(tree, viewport)`, `QueryNodes(tree, viewport)`, `ClearMap(tree)`. |
| `ISpatialMap<T>` / `ISpatialBoundsProvider` | Spatial abstractions (see "Other interfaces" above). |

*Sources: `WorkflowSystem/SpatialGridHashMap.cs`, `WorkflowSystem/WorkflowSpatialManager.cs`, `WorkflowSystem/NodeBoundsProvider.cs`, `WorkflowSystem/NodePairBoundsProvider.cs`, `StandardEx/WorkflowSpatialEx.cs`, `Interfaces/WorkflowSystem/ISpatialMap.cs`, `Interfaces/WorkflowSystem/ISpatialBoundsProvider.cs`.*

### Render-readiness helpers (core, GUI-agnostic)

| Type | Description |
|---|---|
| `WorkflowSlotUpdateGate` | `IsLinkRenderReady(IWorkflowLinkViewModel)` — true when both endpoint anchors are non-NaN (or not yet mounted) |
| `WorkflowLinkRenderEx` | `bool IsRenderReady(this IWorkflowLinkViewModel)` — `IsVisible && WorkflowSlotUpdateGate.IsLinkRenderReady(link)` |
| `WorkflowGuard` | `[Conditional("DEBUG")] Fail(message)` — debug-only contract guard throwing `InvalidOperationException` |

*Sources: `WorkflowSlotUpdateGate.cs`, `WorkflowLinkRenderEx.cs`, `WorkflowGuard.cs`.*
