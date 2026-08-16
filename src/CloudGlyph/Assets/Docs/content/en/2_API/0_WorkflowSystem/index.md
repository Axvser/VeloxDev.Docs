# WorkflowSystem — API Reference

## Namespace: `VeloxDev.WorkflowSystem`

### Builder Attributes (Source Generator)

Partial classes decorated with these attributes receive generated properties, commands and `InitializeWorkflow()`.

| Attribute | Target | Generic constraint | Notes |
|---|---|---|---|
| `[WorkflowBuilder.Tree<T>]` | class | `T : IWorkflowTreeViewModelHelper, new()` | Optional ctor args `virtualLinkType`, `virtualSlotType` |
| `[WorkflowBuilder.Node<T>(workSemaphore = 1)]` | class | `T : IWorkflowNodeViewModelHelper, new()` | `workSemaphore` = concurrent capacity of `ReceiveCommand` |
| `[WorkflowBuilder.Slot<T>]` | class | `T : IWorkflowSlotViewModelHelper, new()` | — |
| `[WorkflowBuilder.Link<T>(slotType = null)]` | class | `T : IWorkflowLinkViewModelHelper, new()` | `slotType` = initial slot type |

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`, lines 11-49.*

### Core Interfaces

Every component derives from `IWorkflowViewModel` (`InitializeWorkflow()`, `OnPropertyChanging/Changed`, `CloseCommand`) and exposes `GetHelper()` / `SetHelper(...)`.

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

`IWorkflowTreeViewModelHelper : IWorkflowHelper` adds events (`NodeAdded/NodeRemoved`, `LinkAdded/LinkRemoved`, `VisibleItemAdded/Removed`), `VisibleItems`, `Viewport`, and methods `Install/Uninstall`, `CreateNode`, `CreateLink`, `SetPointer`, `ValidateConnection`, `SendConnection`, `ReceiveConnection`, `ResetVirtualLink`, `Virtualize`, `Submit`, `Redo`, `Undo`, `ClearHistory`, `MarkDirty`.

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
| `ReceiveCommand` | `IVeloxCommand` | param nullable |
| `BroadcastCommand` | `IVeloxCommand` | forward broadcast |
| `ReverseBroadcastCommand` | `IVeloxCommand` | backward broadcast |

`IWorkflowNodeViewModelHelper : IWorkflowHelper` adds `SlotAdded/SlotRemoved`, `Install/Uninstall`, `CreateSlot`, `Move`, `SetAnchor`, `SetSize`, `ReceiveAsync(context, ct)` — the single execution entry (nullable data/sender/receiver), `BroadcastAsync`, `ReverseBroadcastAsync`, `ValidateBroadcastAsync`, `Delete`.

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`.*

#### `IWorkflowSlotViewModel : IWorkflowViewModel`

| Member | Type | Description |
|---|---|---|
| `Targets` / `Sources` | `ObservableCollection<IWorkflowSlotViewModel>` | Connected peers |
| `Parent` | `IWorkflowNodeViewModel?` | Owning node |
| `Channel` | `SlotChannel` | Connection capacity (flags) |
| `State` | `SlotState` | Connection state (flags) |
| `Anchor` | `Anchor` | Position on the canvas |
| `SetChannelCommand` | `IVeloxCommand` | param `SlotChannel` |
| `SendConnectionCommand` | `IVeloxCommand` | start as sender |
| `ReceiveConnectionCommand` | `IVeloxCommand` | accept as receiver |
| `DeleteCommand` | `IVeloxCommand` | param null |

`IWorkflowSlotViewModelHelper : IWorkflowHelper` adds `TargetAdded/Removed`, `SourceAdded/Removed`, `Install/Uninstall`, `SetChannel`, `UpdateState`, `SendConnection`, `ReceiveConnection`, `Delete`.

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowSlotViewModel.cs`.*

#### `IWorkflowLinkViewModel : IWorkflowViewModel`

| Member | Type | Description |
|---|---|---|
| `Sender` | `IWorkflowSlotViewModel` | Source slot |
| `Receiver` | `IWorkflowSlotViewModel` | Target slot |
| `IsVisible` | `bool` | Rendering visibility |
| `DeleteCommand` | `IVeloxCommand` | param null |

*Source: `Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowLinkViewModel.cs`.*

### Value Types and Enums

| Type | Description |
|---|---|
| `Anchor(left, top, layer)` | Position; implements `IInterpolable`, equality and `+`/`-` operators |
| `Size(width, height)` | Dimensions |
| `Offset(horizontal, vertical)` | Delta vector |
| `Viewport(x, y, width, height)` | Rectangle; `IsEmpty`, `Contains`, `IntersectsWith`, static `Union`, `Empty` |
| `CanvasLayout` | `OriginSize`, `PositiveOffset`, `NegativeOffset`, `ActualSize`, `ActualOffset`, `ViewportOffset`; `AdaptTo(Size)`; `UpdateCommand` |
| `CellKey(x, y)` | Grid cell coordinate |
| `TaskContext(parameter, sender, receiver)` | Payload passed to `ReceiveCommand`; `Deconstruct` |
| `WorkflowActionPair(redo, undo)` | `readonly struct` implementing `IWorkflowActionPair` |
| `SlotChannel` | `[Flags]`: `None`, `OneTarget`, `OneSource`, `OneBoth`, `MultipleTargets`, `MultipleSources`, `MultipleBoth` |
| `SlotState` | `[Flags]`: `StandBy`, `PreviewSender`, `PreviewReceiver`, `Sender`, `Receiver` |
| `IWorkflowIdentifiable` | `RuntimeId` string, stable for the component lifetime |

*Sources: `Anchor.cs`, `Size.cs`, `Offset.cs`, `Viewport.cs`, `CanvasLayout.cs`, `CellKey.cs`, `TaskContext.cs`, `WorkflowActionPair.cs`, `Enums/Slot.cs`, `Interfaces/WorkflowSystem/IWorkflowIdentifiable.cs`.*

### Default ViewModels and Helpers

| Default ViewModel | Default Helper | Purpose |
|---|---|---|
| `TreeDefaultViewModel` | `TreeHelper<T>` | Root container; `CreateLink` returns `LinkDefaultViewModel` |
| `NodeDefaultViewModel` | `NodeHelper<T>` | Node with `Move/SetAnchor/SetSize/CreateSlot/Receive/Broadcast/ReverseBroadcast/Delete` |
| `SlotDefaultViewModel` | `SlotHelper<T>` | Slot with channel/state handling |
| `LinkDefaultViewModel` | `LinkHelper<T>` | Link with `Delete` |

`TreeHelper(double cellSize)` enables spatial virtualization; the type is annotated `[MonoBehaviour(channel: nameof(TreeHelper), fps: 10)]` and calls `tree.EnableMap(CellSize, VisibleItems)` on `Install`. `NodeHelper.SetAnchor/SetSize/Move` call `Parent.GetHelper().MarkDirty()` after mutating. `NodeDefaultViewModel.ReceiveCommand` wraps the parameter into `TaskContext` and calls `ReceiveAsync(context, ct)` — a single receive path carrying nullable data/sender/receiver (see `NodeDefaultViewModel.cs` lines 67-78).

*Sources: `Templates/ViewModels/*.cs`, `Templates/Helpers/*.cs`.*

### Selector System (`SelectorEx`)

| Type | Description |
|---|---|
| `SlotEnumerator<TSlot>` | Dynamic slot collection. `SetSelector(object?)` (a `Type`, type-name string, or `ISlotProvider`), `TrySelect(value, out slot)`, `Items`, `SelectorType`, `SelectorTypeName`, `Install(parent, memberName)`, `Uninstall()`, `Count`, indexer. Selector switches are submitted as undoable actions. |
| `ConditionalSlot<TSlot>` | One entry in `SlotEnumerator.Items`: `Name`, `Value`, `Slot`. |
| `SlotDefinition(value, label)` | Entry produced by an `ISlotProvider`. |
| `ISlotProvider` | `IEnumerable<SlotDefinition> GetSlots()` — drives an enumerator with arbitrary routes (e.g. `CustomRouteSelector`). |
| `[SlotSelectors]` | `VeloxDev.AI` attribute declaring allowed selector types on a `SlotEnumerator` property. |

*Sources: `SelectorEx/SlotEnumerator.cs`, `SelectorEx/ConditionalSlot.cs`, `SelectorEx/SlotDefinition.cs`, `Interfaces/WorkflowSystem/ISlotProvider.cs`, `AI/SlotSelectorsAttribute.cs`.*

### Spatial System

| Type | Description |
|---|---|
| `SpatialGridHashMap<T>` | Generic grid spatial hash (`T : ISpatialBoundsProvider`). `Insert`, `Remove`, `Query(viewport)`, `Clear`, `Bounds`. Cell size set in ctor. |
| `WorkflowSpatialManager` | Tree-level manager indexing nodes (`NodeBoundsProvider`) and node pairs (`NodePairBoundsProvider`, which represent links). `GlobalBounds`, `QueryNodes(viewport)`. |
| `WorkflowSpatialEx` | Extensions: `EnableMap(tree, cellSize, observable)`, `Virtualize(tree, viewport)`, `QueryNodes(tree, viewport)`, `ClearMap(tree)`. |
| `ISpatialMap<T>` / `ISpatialBoundsProvider` | Spatial abstractions. |

*Sources: `WorkflowSystem/SpatialGridHashMap.cs`, `WorkflowSystem/WorkflowSpatialManager.cs`, `WorkflowSystem/NodeBoundsProvider.cs`, `WorkflowSystem/NodePairBoundsProvider.cs`, `StandardEx/WorkflowSpatialEx.cs`, `Interfaces/WorkflowSystem/ISpatialMap.cs`, `Interfaces/WorkflowSystem/ISpatialBoundsProvider.cs`.*

## Namespace: `VeloxDev.WorkflowSystem.StandardEx`

Static extension classes that implement the standard behavior invoked by generated commands.

| Class | Key members |
|---|---|
| `WorkflowTreeEx` | `StandardCreateNode`, `StandardSetPointer`, `StandardSendConnection`, `StandardReceiveConnection`, `StandardResetVirtualLink`, `StandardSubmit`, `StandardUndo`, `StandardRedo`, `StandardClearHistory`, `StandardCloseAsync`, `GetStandardCommands`, degree/topology queries (`GetNodeInDegree`, `GetNodeOutDegree`, `FindEntryNodeIndices`, `FindExitNodeIndices`, `FindNodesByInDegree/OutDegree`) |
| `WorkflowNodeEx` | `StandardCreateSlot`, `StandardMove`, `StandardSetAnchor`, `StandardSetSize`, `StandardSetLayer`, `StandardDelete`, `StandardBroadcastAsync`, `StandardReverseBroadcastAsync`, graph traversal (`SearchForwardNodes`, `SearchReverseNodes`, `SearchAllRelativeNodes`) |
| `WorkflowSlotEx` | `StandardSetChannel`, `StandardUpdateState`, `StandardApplyConnection`, `StandardReceiveConnection`, `StandardCanBeSender`, `StandardCanBeReceiver`, `StandardDelete` |
| `WorkflowLinkEx` | `StandardDelete` |
| `WorkflowCommandEx` | `StandardClosing`, `StandardCloseAsync`, `StandardClosed` |
| `WorkflowSpatialEx` | See Spatial System above |

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/`.*

## Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`

V7 compilation pipeline: compile time decomposes the reachable subgraph from a start node into acyclic compiled graphs (multi-graph semantics); the execution engine drives the graph at runtime. The old `WorkflowCompiler`/`CompilationResult`/`CompiledItem` and their four-dimension settings (`CompileMode`/`CycleHandling`/…) are removed.

| Type | Signature / members |
|---|---|
| `CompilerViewModel` | `CompileAsync<T>(T component) → IReadOnlyList<CompiledGraph>` (`T : IWorkflowViewModel`, start must be an `IWorkflowNodeViewModel`); `Graphs` (`ObservableCollection<CompiledGraph>`). Decomposition: linear segments → `ExecuteEntry`; nodes implementing `ICompileTimeRouter` → `BranchEntry` (static prunes to the current key, dynamic keeps all); a route key pointing to multiple downstreams → `ParallelEntry` (fan-out/join); no downstream → terminal branch (`IsTerminal`); the node all branch exits share is the merge point, continued as the next chain of the parent graph (order offset, not reset). After compiling, every `ICompileTimeAware` node receives its `CompileContext`. |
| `CompiledGraph` | `Entries` (`ObservableCollection<ActionEntry>`) — one compiled graph |
| `ActionEntry` | Abstract base; concrete entries: `ExecuteEntry`, `BranchEntry`, `ParallelEntry` |
| `ExecuteEntry` | `Nodes` (linear-segment node collection) |
| `BranchEntry` | `Router` (`IWorkflowNodeViewModel?`), `Options` (`ObservableCollection<BranchOption>`), `IsDynamic`, `CompileKey` (statically locked key) |
| `BranchOption` | `Key`, `Label`, `Graph` (`CompiledGraph?`), `IsSkipped`, `IsTerminal` |
| `ParallelEntry` | `Branches` (`ObservableCollection<CompiledGraph>`) — fan-out group, branches run in order (the order IS the "wait for all upstreams" join semantics) |
| `CompilerEngine` | `RunAsync(CompiledGraph graph, RuntimeContext context, CancellationToken ct)` — drives all entries of a graph; re-runs the whole graph with a target Order (cross-chain rollback) |
| `ICompileTimeRouter` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()`, `Task<object?> ResolveRouteKey(object? payload)` — compile-time / runtime slot routing |
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(RuntimeContext context, CancellationToken ct)` — returns the compile-state Order to roll back to when the node reports an error |
| `ICompileTimeAware` | `AttachCompileTimeContext(CompileContext)`, `CompileContext` — compile-time identity injection |
| `IRuntimeAware` | `AttachRuntimeContext(RuntimeContext)` — runtime session injected before each drive |
| `ICompileContext` | `Order`, `ChainIndex`, `Offset` — compile identity (`Order = -1` means absolute stop) |
| `IRuntimeContext` | `ITaskContext` + `Uid`, `Sequence`, `Logs`, `CurrentEntry`, `NodeIndex`, `BranchKey`, `Attempt`, `IsRunning`, `Status`, `CurrentOrder`; `Log()/Error()/Warn()/Set()/TryGet()` |
| `RuntimeContext` | Default `IRuntimeContext` implementation (`VeloxProperty` members + shared-variable dictionary); `RedirectRequested`, `EndedWithError`, `PendingRedirectTarget` |
| `CompileContext` | Default `ICompileContext` implementation |
| `RouterCompileMode` | `Static` (key locked at compile time, static pruning), `Dynamic` (runtime re-resolution) |

Execution semantics (`CompilerEngine`): `ExecuteEntry` drives nodes one by one — on cross-chain rollback it skips nodes with `Order < target`; a node calling `RuntimeContext.Error()/Warn()` or throwing during `ReceiveAsync` requests a redirect — if it implements `IRedirectable`, the engine **re-runs the whole graph** from the returned Order (skipping earlier nodes, possibly cross-chain; if the target is a Router it re-routes only, without recomputing), otherwise the flow ends with status `-1`. `BranchEntry` uses the statically locked `CompileKey` in static mode and re-resolves via `ResolveRouteKey` in dynamic mode; selecting a terminal branch (`IsTerminal`) ends the run. `ParallelEntry` runs all branch graphs in order. Redirects are abandoned after 50 attempts.

*Sources: `WorkflowSystem/CompilerEx/CompilerViewModel.cs`, `CompilerEngine.cs`, `CompiledGraph.cs`, `CompileContext.cs`, `RuntimeContext.cs`, `IRedirectable.cs`, `ActionEntry/*.cs`, `Interfaces/*.cs`.*

## Namespace: `VeloxDev.AI`

| Type | Description |
|---|---|
| `[AgentContext(AgentLanguages language, string context)]` | Documents any target (type, property, field, method, enum member) for the Agent. `AllowMultiple = true`. |
| `[AgentCommandParameter(Type?)]` | Declares the parameter type of a generated command. |
| `[SlotSelectors(params Type[] or params string[])]` | Whitelist of selector types for a `SlotEnumerator` property. |
| `AgentLanguages` | Language enum (English, ChineseSimplified/Chinese, ChineseTraditional, Japanese, … 33 values) with `ToLanguageCode()`, `TryParseLanguageCode`, `GetDisplayName`. |
| `AgentContextReader` | Reads `[AgentContext]` values for a type / language. |
| `AgentCommandDiscoverer` | Discovers `ICommand` properties and executes them; `CommandDescriptor` |
| `AgentMethodInvoker` / `AgentPropertyAccessor` / `AgentTypeResolver` | Reflection helpers for agent tooling. |
| `AgentSelectionEventArgs` / `AgentConfirmationEventArgs` / `AgentConfirmationResult` / `AgentToolCallEventArgs` | Event args for the interaction / confirmation / tool-call flow. |

*Sources: `Src/Core/VeloxDev.Core/AI/*.cs`.*

## Namespace: `VeloxDev.AI.Workflow`

`WorkflowAgentScope` — fluent builder obtained via `tree.AsAgentScope()`:

| Fluent method | Effect |
|---|---|
| `WithPromptLanguage(AgentLanguages)` | Default language for prompts/docs |
| `WithOutputLanguage(AgentLanguages)` | Language the LLM must use for replies |
| `WithMaxToolCalls(int)` | Cap on cumulative tool calls |
| `WithAutoMarkDirty(bool)` | Auto-`MarkDirty` on mutation tools |
| `WithInteractionSafety(int 0-3)` | 0 silent, 1 cautious, 2 balanced, 3 strict |
| `WithInteractionSafetyPrompt(int, string)` | Override prompt body per level (1-3) |
| `WithAutoDiscovery(Assembly or string)` | Auto-register workflow components/enums/interfaces/data |
| `WithEnums / WithInterfaces / WithComponents / WithData(Type[], AgentLanguages?)` | Manual type registration |
| `WithSelectionHandler(Func<AgentSelectionEventArgs, Task>)` | Enables `RequestSelection` tool |
| `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task>)` | Enables `RequestConfirmation` tool |
| `WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` | After-each-tool-call callback |
| `WithTools(string?, params AITool[])` | Merge custom tools + prompt context |
| `ProvideAllContexts() / ProvideAllContexts(language)` | Full context string |
| `ProvideProgressiveContextPrompt()` | Compact system prompt (progressive disclosure) |
| `ProvideFrameworkContext / ProvideCustomerContext / ProvideFrameworkDataContext / ProvideCustomerDataContext` | Section builders |
| `CreateToolkit()` / `ProvideTools()` | Build `WorkflowAgentToolkit` and return all `AITool` |

`WorkflowStateTracker` takes JSON snapshots of the tree and computes `added/removed/modified` diffs (`TakeSnapshot`, `GetChangesSinceLastSnapshot`).

*Sources: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`, `WorkflowStateTracker.cs`.*

## Namespace: `VeloxDev.AI.Workflow.Functions`

`WorkflowAgentToolkit(WorkflowAgentScope)` — `CreateTools()` returns ~60 `AITool`s wrapped in call-tracking. Groups: query (`ListNodes`, `GetNodeDetail`, `ListConnections`, `GetTypeSchema`), progressive context (`GetWorkflowSummary`, `GetComponentContext`, `ListComponentCommands`), state diff (`TakeSnapshot`, `GetChangesSinceSnapshot`, `MarkDirty`), mutation (`CreateNode`, `MoveNode`, `SetNodePosition`, `ResizeNode`, `DeleteNode`, `DeleteSlot`, `ConnectSlots`, `ConnectSlotsById`, `DisconnectSlots`, `ExecuteNode`, `BroadcastNode`, `Undo`, `Redo`, `PatchNodeProperties`, `PatchComponentById`), generic command execution (`ExecuteCommandOnNode`, `ExecuteCommandById`), slot collections (`ListSlotProperties`, `AddSlotToCollection`, `RemoveSlotFromCollection`, `SetEnumSlotCollection`, `GetEnumSlotByValue`, `SetEnumSlotChannel`, `ConnectEnumSlot`), graph traversal (`SearchForward`, `SearchReverse`, `SearchAllRelative`, `IsConnected`, `FindPath`), connection management (`DisconnectSlotsById`, `DisconnectAllFromSlot`, `DisconnectAllFromNode`, `ReplaceConnection`, `SetSlotChannel`, `GetLinkDetail`), bulk (`BatchExecute`, `ExecuteNodes`, `BulkPatchNodes`, `CloneNodes`, `DeleteNodes`), layout (`AlignNodes`, `DistributeNodes`, `AutoLayout`, `ArrangeNodes`), analytics (`GetNodeStatistics`, `ListCreatableTypes`, `ValidateWorkflow`, `GetFullTopology`), composite (`ConnectByProperty`, `CreateAndConfigureNode`) and interaction (`RequestSelection`, `RequestConfirmation`, only when handlers configured and safety level > 0).

*Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, `CreateTools()` lines 34-139.*

## Namespace: `VeloxDev.AI.MCP`

| Type | Description |
|---|---|
| `McpScope` | `WithMcpRoot(string)` (default `.evn/mcp`), `LoadAsync(IEnumerable<McpServerConfiguration>, CancellationToken)` → `AITool[]`; installs npm/pip packages and connects over stdio; `ServerError` event |
| `McpServerConfiguration` | `Name`, `Description`, `RunMode`, `Package`, `Version`, `Arguments` — note the property is `Package` |
| `McpServerRunMode` | `Npm`, `Npx`, `Uvx`, `Dotnet`, `Pip`, `Exe` |

*Sources: `Src/Core/VeloxDev.Core.Extension/Agent/MCP/*.cs`.*

## Namespace: `VeloxDev.MVVM.Serialization`

`ComponentModelEx` (Newtonsoft based). Settings: `TypeNameHandling.Auto`, `PreserveReferencesHandling.Objects`, `ReferenceLoopHandling.Ignore`, `WritablePropertiesOnlyResolver`.

| Method | Signature |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)` where `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)` (+ options overload) |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)` |
| Async | `SerializeAsync`, `DeserializeAsync` |
| Streaming | `SerializeToUtf8Bytes`, `DeserializeFromUtf8Bytes`, `SerializeToTextWriterAsync`, `DeserializeFromTextReaderAsync`, `SerializeToStreamAsync`, `DeserializeFromStreamAsync` |
| Options | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)` |

*Source: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`.*

## Platform Attached Behaviors (`VeloxDev.WorkflowSystem.AttachedBehaviors`)

Provided by each UI adapter (verified on `VeloxDev.WPF`):

| Behavior | Used for |
|---|---|
| `WorkflowSurfaceBehavior` | Pan/zoom surface, scroll sync, grid decorator; static `Refresh(view)` |
| `WorkflowCanvasTransformBehavior` | Render transform for pan/zoom (attached property `Transform`) |
| `ViewPool` | Virtualization — binds `ItemsSource` to `Helper.VisibleItems` |
| `WorkflowNodeDragBehavior` | Drag-to-move nodes (`CoordinateHostName`, `IsEnabled`) |
| `WorkflowSlotConnectionBehavior` | Click/drag to connect slots |
| `WorkflowSlotLayoutBehavior` | Auto-position named slots (`SlotNames`, `SlotEnumeratorNames`, `CoordinateHostName`) |
| `WorkflowMinimapOverlay` | Overview minimap |

*Verified usage: `Examples/Workflow/WPF/Demo/Views/Workflow/*.xaml`.*
