# 工作流系统 — API 参考

## 命名空间：`VeloxDev.WorkflowSystem`

### 构建器属性（源生成器）

用这些属性修饰的 partial 类会获得生成的属性、命令与 `InitializeWorkflow()`。

| 属性 | 目标 | 泛型约束 | 说明 |
|---|---|---|---|
| `[WorkflowBuilder.Tree<T>]` | 类 | `T : IWorkflowTreeViewModelHelper, new()` | 可选构造参数 `virtualLinkType`、`virtualSlotType` |
| `[WorkflowBuilder.Node<T>(workSemaphore = 1)]` | 类 | `T : IWorkflowNodeViewModelHelper, new()` | `workSemaphore` = `ReceiveCommand` 并发容量 |
| `[WorkflowBuilder.Slot<T>]` | 类 | `T : IWorkflowSlotViewModelHelper, new()` | — |
| `[WorkflowBuilder.Link<T>(slotType = null)]` | 类 | `T : IWorkflowLinkViewModelHelper, new()` | `slotType` = 初始槽位类型 |

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`，第 11-49 行。*

### 核心接口

每个组件都派生自 `IWorkflowViewModel`（`InitializeWorkflow()`、`OnPropertyChanging/Changed`、`CloseCommand`），并暴露 `GetHelper()` / `SetHelper(...)`。

#### `IWorkflowTreeViewModel : IWorkflowViewModel`

| 成员 | 类型 | 描述 |
|---|---|---|
| `Layout` | `CanvasLayout` | 画布尺寸 / 偏移上下文 |
| `VirtualLink` | `IWorkflowLinkViewModel` | 仅在连接过程中可见的临时连接 |
| `Nodes` | `ObservableCollection<IWorkflowNodeViewModel>` | 所有 Node 组件 |
| `Links` | `ObservableCollection<IWorkflowLinkViewModel>` | 所有 Link 组件 |
| `LinksMap` | `Dictionary<IWorkflowSlotViewModel, Dictionary<IWorkflowSlotViewModel, IWorkflowLinkViewModel>>` | Slot 间连接映射 |
| `CreateNodeCommand` | `IVeloxCommand` | 参数 `IWorkflowNodeViewModel` |
| `SetPointerCommand` | `IVeloxCommand` | 参数 `Anchor` |
| `ResetVirtualLinkCommand` | `IVeloxCommand` | 参数 null |
| `SendConnectionCommand` | `IVeloxCommand` | 参数 `IWorkflowSlotViewModel` |
| `ReceiveConnectionCommand` | `IVeloxCommand` | 参数 `IWorkflowSlotViewModel` |
| `SubmitCommand` | `IVeloxCommand` | 参数 `IWorkflowActionPair` |
| `UndoCommand` | `IVeloxCommand` | 参数 null |
| `RedoCommand` | `IVeloxCommand` | 参数 null |

`IWorkflowTreeViewModelHelper : IWorkflowHelper` 增加事件（`NodeAdded/NodeRemoved`、`LinkAdded/LinkRemoved`、`VisibleItemAdded/Removed`）、`VisibleItems`、`Viewport`，以及 `Install/Uninstall`、`CreateNode`、`CreateLink`、`SetPointer`、`ValidateConnection`、`SendConnection`、`ReceiveConnection`、`ResetVirtualLink`、`Virtualize`、`Submit`、`Redo`、`Undo`、`ClearHistory`、`MarkDirty`。

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowTreeViewModel.cs`。*

#### `IWorkflowNodeViewModel : IWorkflowViewModel`

| 成员 | 类型 | 描述 |
|---|---|---|
| `Parent` | `IWorkflowTreeViewModel?` | 所属 Tree |
| `Anchor` | `Anchor` | 画布坐标（X、Y、layer） |
| `Size` | `Size` | 宽度 / 高度 |
| `Slots` | `ObservableCollection<IWorkflowSlotViewModel>` | 拥有的槽位 |
| `MoveCommand` | `IVeloxCommand` | 参数 `Offset` |
| `SetAnchorCommand` | `IVeloxCommand` | 参数 `Anchor` |
| `SetSizeCommand` | `IVeloxCommand` | 参数 `Size` |
| `CreateSlotCommand` | `IVeloxCommand` | 参数 `IWorkflowSlotViewModel` |
| `DeleteCommand` | `IVeloxCommand` | 参数 null；级联删除槽位与连接 |
| `ReceiveCommand` | `IVeloxCommand` | 参数可空 |
| `BroadcastCommand` | `IVeloxCommand` | 正向广播 |
| `ReverseBroadcastCommand` | `IVeloxCommand` | 反向广播 |

`IWorkflowNodeViewModelHelper : IWorkflowHelper` 增加 `SlotAdded/SlotRemoved`、`Install/Uninstall`、`CreateSlot`、`Move`、`SetAnchor`、`SetSize`、`ReceiveAsync(context, ct)` —— 唯一的执行入口（data/sender/receiver 均可空）、`BroadcastAsync`、`ReverseBroadcastAsync`、`ValidateBroadcastAsync`、`Delete`。

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`。*

#### `IWorkflowSlotViewModel : IWorkflowViewModel`

| 成员 | 类型 | 描述 |
|---|---|---|
| `Targets` / `Sources` | `ObservableCollection<IWorkflowSlotViewModel>` | 连接的槽位 |
| `Parent` | `IWorkflowNodeViewModel?` | 所属节点 |
| `Channel` | `SlotChannel` | 连接容量（flags） |
| `State` | `SlotState` | 连接状态（flags） |
| `Anchor` | `Anchor` | 画布坐标 |
| `SetChannelCommand` | `IVeloxCommand` | 参数 `SlotChannel` |
| `SendConnectionCommand` | `IVeloxCommand` | 作为发送方发起连接 |
| `ReceiveConnectionCommand` | `IVeloxCommand` | 作为接收方接受连接 |
| `DeleteCommand` | `IVeloxCommand` | 参数 null |

`IWorkflowSlotViewModelHelper : IWorkflowHelper` 增加 `TargetAdded/Removed`、`SourceAdded/Removed`、`Install/Uninstall`、`SetChannel`、`UpdateState`、`SendConnection`、`ReceiveConnection`、`Delete`。

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowSlotViewModel.cs`。*

#### `IWorkflowLinkViewModel : IWorkflowViewModel`

| 成员 | 类型 | 描述 |
|---|---|---|
| `Sender` | `IWorkflowSlotViewModel` | 源槽位 |
| `Receiver` | `IWorkflowSlotViewModel` | 目标槽位 |
| `IsVisible` | `bool` | 渲染可见性 |
| `DeleteCommand` | `IVeloxCommand` | 参数 null |

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowLinkViewModel.cs`。*

### 值类型与枚举

| 类型 | 描述 |
|---|---|
| `Anchor(left, top, layer)` | 位置；实现 `IInterpolable`、相等性与 `+`/`-` 运算符 |
| `Size(width, height)` | 尺寸 |
| `Offset(horizontal, vertical)` | 增量向量 |
| `Viewport(x, y, width, height)` | 矩形；`IsEmpty`、`Contains`、`IntersectsWith`、静态 `Union`、`Empty` |
| `CanvasLayout` | `OriginSize`、`PositiveOffset`、`NegativeOffset`、`ActualSize`、`ActualOffset`、`ViewportOffset`；`AdaptTo(Size)`；`UpdateCommand` |
| `CellKey(x, y)` | 网格单元坐标 |
| `TaskContext(parameter, sender, receiver)` | 传给 `ReceiveCommand` 的载荷；`Deconstruct` |
| `WorkflowActionPair(redo, undo)` | 实现 `IWorkflowActionPair` 的 `readonly struct` |
| `SlotChannel` | `[Flags]`：`None`、`OneTarget`、`OneSource`、`OneBoth`、`MultipleTargets`、`MultipleSources`、`MultipleBoth` |
| `SlotState` | `[Flags]`：`StandBy`、`PreviewSender`、`PreviewReceiver`、`Sender`、`Receiver` |
| `IWorkflowIdentifiable` | `RuntimeId` 字符串，组件生命周期内稳定 |

*源码：`Anchor.cs`、`Size.cs`、`Offset.cs`、`Viewport.cs`、`CanvasLayout.cs`、`CellKey.cs`、`TaskContext.cs`、`WorkflowActionPair.cs`、`Enums/Slot.cs`、`Interfaces/WorkflowSystem/IWorkflowIdentifiable.cs`。*

### 默认 ViewModel 与 Helper

| 默认 ViewModel | 默认 Helper | 用途 |
|---|---|---|
| `TreeDefaultViewModel` | `TreeHelper<T>` | 根容器；`CreateLink` 返回 `LinkDefaultViewModel` |
| `NodeDefaultViewModel` | `NodeHelper<T>` | 提供 `Move/SetAnchor/SetSize/CreateSlot/Receive/Broadcast/ReverseBroadcast/Delete` |
| `SlotDefaultViewModel` | `SlotHelper<T>` | 处理通道与状态 |
| `LinkDefaultViewModel` | `LinkHelper<T>` | 提供 `Delete` |

`TreeHelper(double cellSize)` 启用空间虚拟化；该类型标注 `[MonoBehaviour(channel: nameof(TreeHelper), fps: 10)]`，并在 `Install` 时调用 `tree.EnableMap(CellSize, VisibleItems)`。`NodeHelper.SetAnchor/SetSize/Move` 在变更后调用 `Parent.GetHelper().MarkDirty()`。`NodeDefaultViewModel.ReceiveCommand` 把参数包装成 `TaskContext` 并调用 `ReceiveAsync(context, ct)` —— 单一接收路径，携带可空的 data/sender/receiver（见 `NodeDefaultViewModel.cs` 第 67-78 行）。

*源码：`Templates/ViewModels/*.cs`、`Templates/Helpers/*.cs`。*

### 选择器系统（`SelectorEx`）

| 类型 | 描述 |
|---|---|
| `SlotEnumerator<TSlot>` | 动态槽位集合。`SetSelector(object?)`（`Type`、类型名字符串或 `ISlotProvider`）、`TrySelect(value, out slot)`、`Items`、`SelectorType`、`SelectorTypeName`、`Install(parent, memberName)`、`Uninstall()`、`Count`、索引器。选择器切换以可撤销操作提交。 |
| `ConditionalSlot<TSlot>` | `SlotEnumerator.Items` 中的一项：`Name`、`Value`、`Slot`。 |
| `SlotDefinition(value, label)` | 由 `ISlotProvider` 产生的一项。 |
| `ISlotProvider` | `IEnumerable<SlotDefinition> GetSlots()` —— 用任意路由驱动枚举器（如 `CustomRouteSelector`）。 |
| `[SlotSelectors]` | `VeloxDev.AI` 属性，声明 `SlotEnumerator` 属性允许的选择器类型。 |

*源码：`SelectorEx/SlotEnumerator.cs`、`SelectorEx/ConditionalSlot.cs`、`SelectorEx/SlotDefinition.cs`、`Interfaces/WorkflowSystem/ISlotProvider.cs`、`AI/SlotSelectorsAttribute.cs`。*

### 空间系统

| 类型 | 描述 |
|---|---|
| `SpatialGridHashMap<T>` | 通用网格空间哈希（`T : ISpatialBoundsProvider`）。`Insert`、`Remove`、`Query(viewport)`、`Clear`、`Bounds`。单元尺寸在构造函数中设置。 |
| `WorkflowSpatialManager` | Tree 级管理器，索引节点（`NodeBoundsProvider`）与节点对（`NodePairBoundsProvider`，表示连接）。`GlobalBounds`、`QueryNodes(viewport)`。 |
| `WorkflowSpatialEx` | 扩展：`EnableMap(tree, cellSize, observable)`、`Virtualize(tree, viewport)`、`QueryNodes(tree, viewport)`、`ClearMap(tree)`。 |
| `ISpatialMap<T>` / `ISpatialBoundsProvider` | 空间抽象。 |

*源码：`WorkflowSystem/SpatialGridHashMap.cs`、`WorkflowSystem/WorkflowSpatialManager.cs`、`WorkflowSystem/NodeBoundsProvider.cs`、`WorkflowSystem/NodePairBoundsProvider.cs`、`StandardEx/WorkflowSpatialEx.cs`、`Interfaces/WorkflowSystem/ISpatialMap.cs`、`Interfaces/WorkflowSystem/ISpatialBoundsProvider.cs`。*

## 命名空间：`VeloxDev.WorkflowSystem.StandardEx`

生成命令所调用的标准行为静态扩展类。

| 类 | 关键成员 |
|---|---|
| `WorkflowTreeEx` | `StandardCreateNode`、`StandardSetPointer`、`StandardSendConnection`、`StandardReceiveConnection`、`StandardResetVirtualLink`、`StandardSubmit`、`StandardUndo`、`StandardRedo`、`StandardClearHistory`、`StandardCloseAsync`、`GetStandardCommands`、度/拓扑查询（`GetNodeInDegree`、`GetNodeOutDegree`、`FindEntryNodeIndices`、`FindExitNodeIndices`、`FindNodesByInDegree/OutDegree`） |
| `WorkflowNodeEx` | `StandardCreateSlot`、`StandardMove`、`StandardSetAnchor`、`StandardSetSize`、`StandardSetLayer`、`StandardDelete`、`StandardBroadcastAsync`、`StandardReverseBroadcastAsync`、图遍历（`SearchForwardNodes`、`SearchReverseNodes`、`SearchAllRelativeNodes`） |
| `WorkflowSlotEx` | `StandardSetChannel`、`StandardUpdateState`、`StandardApplyConnection`、`StandardReceiveConnection`、`StandardCanBeSender`、`StandardCanBeReceiver`、`StandardDelete` |
| `WorkflowLinkEx` | `StandardDelete` |
| `WorkflowCommandEx` | `StandardClosing`、`StandardCloseAsync`、`StandardClosed` |
| `WorkflowSpatialEx` | 见上文空间系统 |

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/`。*

## 命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`

V7 编译管道：编译期把起点可达子图分解成若干无环的编译图（多图语义），运行期由执行引擎按图驱动。旧的 `WorkflowCompiler`/`CompilationResult`/`CompiledItem` 及其 `CompileMode`/`CycleHandling` 四维度配置已移除。

| 类型 | 签名 / 成员 |
|---|---|
| `CompilerViewModel` | `CompileAsync<T>(T component) → IReadOnlyList<CompiledGraph>`（`T : IWorkflowViewModel`，起点须为 `IWorkflowNodeViewModel`）；`Graphs`（`ObservableCollection<CompiledGraph>`）。分解：线性段 → `ExecuteEntry`；实现 `ICompileTimeRouter` 的节点 → `BranchEntry`（静态按当前 key 剪枝、动态全保留）；路由 key 指向多个下游 → `ParallelEntry`（扇出/汇聚）；无下游 → 终端分支（`IsTerminal`）；分支后所有出口共同指向的节点为汇合点，作为父图下一段链的起点（序号带偏移，不归零）。编译完给每个实现 `ICompileTimeAware` 的节点注入 `CompileContext`。 |
| `CompiledGraph` | `Entries`（`ObservableCollection<ActionEntry>`）—— 一张编译图 |
| `ActionEntry` | 抽象基类；具体条目：`ExecuteEntry`、`BranchEntry`、`ParallelEntry` |
| `ExecuteEntry` | `Nodes`（线性段节点集合） |
| `BranchEntry` | `Router`（`IWorkflowNodeViewModel?`）、`Options`（`ObservableCollection<BranchOption>`）、`IsDynamic`、`CompileKey`（静态锁定 key） |
| `BranchOption` | `Key`、`Label`、`Graph`（`CompiledGraph?`）、`IsSkipped`、`IsTerminal` |
| `ParallelEntry` | `Branches`（`ObservableCollection<CompiledGraph>`）—— 扇出组，顺序执行各分支（顺序即"等待所有上游"的汇聚语义） |
| `CompilerEngine` | `RunAsync(CompiledGraph graph, RuntimeContext context, CancellationToken ct)` —— 驱动一张图的所有条目；带目标 Order 重跑整张图（跨链回退） |
| `ICompileTimeRouter` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()`、`Task<object?> ResolveRouteKey(object? payload)` —— 编译期/运行期槽位路由 |
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(RuntimeContext context, CancellationToken ct)` —— 节点报错时返回回退目标编译状态 Order |
| `ICompileTimeAware` | `AttachCompileTimeContext(CompileContext)`、`CompileContext` —— 编译期身份注入 |
| `IRuntimeAware` | `AttachRuntimeContext(RuntimeContext)` —— 每次驱动前注入运行会话 |
| `ICompileContext` | `Order`、`ChainIndex`、`Offset` —— 编译身份（`Order = -1` 表示绝对停止） |
| `IRuntimeContext` | `ITaskContext` + `Uid`、`Sequence`、`Logs`、`CurrentEntry`、`NodeIndex`、`BranchKey`、`Attempt`、`IsRunning`、`Status`、`CurrentOrder`；`Log()/Error()/Warn()/Set()/TryGet()` |
| `RuntimeContext` | `IRuntimeContext` 的默认实现（`VeloxProperty` 属性 + 共享变量字典）；`RedirectRequested`、`EndedWithError`、`PendingRedirectTarget` |
| `CompileContext` | `ICompileContext` 的默认实现 |
| `RouterCompileMode` | `Static`（编译期锁定 key，静态剪枝）、`Dynamic`（运行期重解析） |

执行语义（`CompilerEngine`）：`ExecuteEntry` 逐个驱动节点 —— 跨链回退时跳过 `Order < 目标` 的节点；节点在 `ReceiveAsync` 中调用 `RuntimeContext.Error()/Warn()` 或抛异常即视为请求重定向 —— 若实现 `IRedirectable`，按其返回的 Order **重跑整张图**（跳过目标之前的节点，可跨链；目标是 Router 时只重新路由、不重新计算），否则整个流程结束、状态标记为 `-1`。`BranchEntry` 静态模式以编译期锁定的 `CompileKey` 为准，动态模式运行期 `ResolveRouteKey` 重解析；终端分支（`IsTerminal`）选中即结束。`ParallelEntry` 顺序执行所有分支子图。重定向超过 50 次放弃。

*源码：`WorkflowSystem/CompilerEx/CompilerViewModel.cs`、`CompilerEngine.cs`、`CompiledGraph.cs`、`CompileContext.cs`、`RuntimeContext.cs`、`IRedirectable.cs`、`ActionEntry/*.cs`、`Interfaces/*.cs`。*

## 命名空间：`VeloxDev.AI`

| 类型 | 描述 |
|---|---|
| `[AgentContext(AgentLanguages language, string context)]` | 为 Agent 描述任意目标（类型、属性、字段、方法、枚举成员）。`AllowMultiple = true`。 |
| `[AgentCommandParameter(Type?)]` | 声明生成命令的参数类型。 |
| `[SlotSelectors(params Type[] 或 params string[])]` | `SlotEnumerator` 属性的选择器类型白名单。 |
| `AgentLanguages` | 语言枚举（English、ChineseSimplified/Chinese、ChineseTraditional、Japanese、……共 33 个值），含 `ToLanguageCode()`、`TryParseLanguageCode`、`GetDisplayName`。 |
| `AgentContextReader` | 读取某类型 / 语言的 `[AgentContext]` 值。 |
| `AgentCommandDiscoverer` | 发现并执行 `ICommand` 属性；`CommandDescriptor` |
| `AgentMethodInvoker` / `AgentPropertyAccessor` / `AgentTypeResolver` | Agent 工具用的反射辅助。 |
| `AgentSelectionEventArgs` / `AgentConfirmationEventArgs` / `AgentConfirmationResult` / `AgentToolCallEventArgs` | 交互 / 确认 / 工具调用流程的事件参数。 |

*源码：`Src/Core/VeloxDev.Core/AI/*.cs`。*

## 命名空间：`VeloxDev.AI.Workflow`

`WorkflowAgentScope` —— 通过 `tree.AsAgentScope()` 获得的流式构建器：

| 流式方法 | 作用 |
|---|---|
| `WithPromptLanguage(AgentLanguages)` | 提示词/文档的默认语言 |
| `WithOutputLanguage(AgentLanguages)` | LLM 回复必须使用的语言 |
| `WithMaxToolCalls(int)` | 累计工具调用上限 |
| `WithAutoMarkDirty(bool)` | 变更工具是否自动 `MarkDirty` |
| `WithInteractionSafety(int 0-3)` | 0 静默、1 谨慎、2 平衡、3 严格 |
| `WithInteractionSafetyPrompt(int, string)` | 覆盖 1-3 档的提示词正文 |
| `WithAutoDiscovery(Assembly 或 string)` | 自动注册工作流组件/枚举/接口/数据 |
| `WithEnums / WithInterfaces / WithComponents / WithData(Type[], AgentLanguages?)` | 手动类型注册 |
| `WithSelectionHandler(Func<AgentSelectionEventArgs, Task>)` | 启用 `RequestSelection` 工具 |
| `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task>)` | 启用 `RequestConfirmation` 工具 |
| `WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` | 每次工具调用后的回调 |
| `WithTools(string?, params AITool[])` | 合并自定义工具与提示词上下文 |
| `ProvideAllContexts() / ProvideAllContexts(language)` | 完整上下文字符串 |
| `ProvideProgressiveContextPrompt()` | 精简系统提示词（渐进式披露） |
| `ProvideFrameworkContext / ProvideCustomerContext / ProvideFrameworkDataContext / ProvideCustomerDataContext` | 分区构建器 |
| `CreateToolkit()` / `ProvideTools()` | 构建 `WorkflowAgentToolkit` 并返回所有 `AITool` |

`WorkflowStateTracker` 对树做 JSON 快照并计算 `added/removed/modified` 差异（`TakeSnapshot`、`GetChangesSinceLastSnapshot`）。

*源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`、`WorkflowStateTracker.cs`。*

## 命名空间：`VeloxDev.AI.Workflow.Functions`

`WorkflowAgentToolkit(WorkflowAgentScope)` —— `CreateTools()` 返回约 60 个带调用追踪的 `AITool`。分组：查询（`ListNodes`、`GetNodeDetail`、`ListConnections`、`GetTypeSchema`）、渐进式上下文（`GetWorkflowSummary`、`GetComponentContext`、`ListComponentCommands`）、状态差异（`TakeSnapshot`、`GetChangesSinceSnapshot`、`MarkDirty`）、变更（`CreateNode`、`MoveNode`、`SetNodePosition`、`ResizeNode`、`DeleteNode`、`DeleteSlot`、`ConnectSlots`、`ConnectSlotsById`、`DisconnectSlots`、`ExecuteNode`、`BroadcastNode`、`Undo`、`Redo`、`PatchNodeProperties`、`PatchComponentById`）、通用命令执行（`ExecuteCommandOnNode`、`ExecuteCommandById`）、槽位集合（`ListSlotProperties`、`AddSlotToCollection`、`RemoveSlotFromCollection`、`SetEnumSlotCollection`、`GetEnumSlotByValue`、`SetEnumSlotChannel`、`ConnectEnumSlot`）、图遍历（`SearchForward`、`SearchReverse`、`SearchAllRelative`、`IsConnected`、`FindPath`）、连接管理（`DisconnectSlotsById`、`DisconnectAllFromSlot`、`DisconnectAllFromNode`、`ReplaceConnection`、`SetSlotChannel`、`GetLinkDetail`）、批量（`BatchExecute`、`ExecuteNodes`、`BulkPatchNodes`、`CloneNodes`、`DeleteNodes`）、布局（`AlignNodes`、`DistributeNodes`、`AutoLayout`、`ArrangeNodes`）、分析（`GetNodeStatistics`、`ListCreatableTypes`、`ValidateWorkflow`、`GetFullTopology`）、复合（`ConnectByProperty`、`CreateAndConfigureNode`）与交互（`RequestSelection`、`RequestConfirmation`，仅在配置了处理器且安全级别大于 0 时注册）。

*源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`，`CreateTools()` 第 34-139 行。*

## 命名空间：`VeloxDev.AI.MCP`

| 类型 | 描述 |
|---|---|
| `McpScope` | `WithMcpRoot(string)`（默认 `.evn/mcp`）、`LoadAsync(IEnumerable<McpServerConfiguration>, CancellationToken)` → `AITool[]`；安装 npm/pip 包并通过 stdio 连接；`ServerError` 事件 |
| `McpServerConfiguration` | `Name`、`Description`、`RunMode`、`Package`、`Version`、`Arguments` —— 注意属性名是 `Package` |
| `McpServerRunMode` | `Npm`、`Npx`、`Uvx`、`Dotnet`、`Pip`、`Exe` |

*源码：`Src/Core/VeloxDev.Core.Extension/Agent/MCP/*.cs`。*

## 命名空间：`VeloxDev.MVVM.Serialization`

`ComponentModelEx`（基于 Newtonsoft）。设置：`TypeNameHandling.Auto`、`PreserveReferencesHandling.Objects`、`ReferenceLoopHandling.Ignore`、`WritablePropertiesOnlyResolver`。

| 方法 | 签名 |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)`，其中 `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)`（+ 带 options 的重载） |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)` |
| 异步 | `SerializeAsync`、`DeserializeAsync` |
| 流式 | `SerializeToUtf8Bytes`、`DeserializeFromUtf8Bytes`、`SerializeToTextWriterAsync`、`DeserializeFromTextReaderAsync`、`SerializeToStreamAsync`、`DeserializeFromStreamAsync` |
| Options | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)` |

*源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`。*

## 平台附加行为（`VeloxDev.WorkflowSystem.AttachedBehaviors`）

由各 UI 适配器提供（在 `VeloxDev.WPF` 上验证）：

| 行为 | 用途 |
|---|---|
| `WorkflowSurfaceBehavior` | 平移/缩放表面、滚动同步、网格装饰；静态 `Refresh(view)` |
| `WorkflowCanvasTransformBehavior` | 平移/缩放渲染变换（附加属性 `Transform`） |
| `ViewPool` | 虚拟化 —— 把 `ItemsSource` 绑定到 `Helper.VisibleItems` |
| `WorkflowNodeDragBehavior` | 拖拽移动节点（`CoordinateHostName`、`IsEnabled`） |
| `WorkflowSlotConnectionBehavior` | 点击/拖拽连接槽位 |
| `WorkflowSlotLayoutBehavior` | 自动定位命名槽位（`SlotNames`、`SlotEnumeratorNames`、`CoordinateHostName`） |
| `WorkflowMinimapOverlay` | 概览小地图 |

*验证用法：`Examples/Workflow/WPF/Demo/Views/Workflow/*.xaml`。*
