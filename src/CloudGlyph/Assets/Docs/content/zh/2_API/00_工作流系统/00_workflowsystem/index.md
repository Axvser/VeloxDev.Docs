# Workflow System — 命名空间：`VeloxDev.WorkflowSystem`

### 构建器属性（源生成器）

以这些属性修饰的 partial 类会获得生成的属性、命令、Helper 装配与 `InitializeWorkflow()`。

| 属性 | 目标 | 泛型约束 | 说明 |
|---|---|---|---|
| `[WorkflowBuilder.Tree<T>]` | class | `T : IWorkflowTreeViewModelHelper, new()` | 可选构造参数 `virtualLinkType`、`virtualSlotType` |
| `[WorkflowBuilder.Node<T>(workSemaphore = 1)]` | class | `T : IWorkflowNodeViewModelHelper, new()` | `workSemaphore` = `ReceiveCommand` 的并发容量 |
| `[WorkflowBuilder.Slot<T>]` | class | `T : IWorkflowSlotViewModelHelper, new()` | — |
| `[WorkflowBuilder.Link<T>(slotType = null)]` | class | `T : IWorkflowLinkViewModelHelper, new()` | `slotType` = 初始槽位类型 |

**示例** —— 演示节点装饰：`Examples/Workflow/Common/Lib/ViewModels/Workflow/NodeViewModel.cs`，第 11-14 行（`[WorkflowBuilder.Node<HttpHelper<NodeViewModel>>(workSemaphore: 5)]`）。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/WorkflowBuilder.cs`，第 3-50 行。*

### 核心接口

每个组件都派生自 `IWorkflowViewModel`，并暴露 `GetHelper()` / `SetHelper(...)`。

#### `IWorkflowViewModel`

```csharp
public interface IWorkflowViewModel : INotifyPropertyChanging, INotifyPropertyChanged
```

| 成员 | 签名 | 说明 |
|---|---|---|
| `InitializeWorkflow()` | `void InitializeWorkflow()` | 生成器发出；安装 Helper |
| `OnPropertyChanging` | `void OnPropertyChanging(string propertyName)` | 变更前通知 |
| `OnPropertyChanged` | `void OnPropertyChanged(string propertyName)` | 变更通知 |
| `CloseCommand` | `IVeloxCommand CloseCommand { get; }` | 终结所有进行中的任务（参数为 null） |

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowViewModel.cs`。*

#### `IWorkflowTreeViewModel : IWorkflowViewModel`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Layout` | `CanvasLayout` | 画布尺寸 / 偏移上下文 |
| `VirtualLink` | `IWorkflowLinkViewModel` | 仅在建立连接过程中可见的临时连接 |
| `Nodes` | `ObservableCollection<IWorkflowNodeViewModel>` | 所有节点组件 |
| `Links` | `ObservableCollection<IWorkflowLinkViewModel>` | 所有连接组件 |
| `LinksMap` | `Dictionary<IWorkflowSlotViewModel, Dictionary<IWorkflowSlotViewModel, IWorkflowLinkViewModel>>` | 槽位→槽位连接映射 |
| `CreateNodeCommand` | `IVeloxCommand` | 参数 `IWorkflowNodeViewModel` |
| `SetPointerCommand` | `IVeloxCommand` | 参数 `Anchor` |
| `ResetVirtualLinkCommand` | `IVeloxCommand` | 参数 null |
| `SendConnectionCommand` | `IVeloxCommand` | 参数 `IWorkflowSlotViewModel` |
| `ReceiveConnectionCommand` | `IVeloxCommand` | 参数 `IWorkflowSlotViewModel` |
| `SubmitCommand` | `IVeloxCommand` | 参数 `IWorkflowActionPair` |
| `UndoCommand` | `IVeloxCommand` | 参数 null |
| `RedoCommand` | `IVeloxCommand` | 参数 null |

**`IWorkflowTreeViewModelHelper : IWorkflowHelper`**

```csharp
public interface IWorkflowTreeViewModelHelper : IWorkflowHelper
```

事件：`NodeAdded` / `NodeRemoved`（`EventHandler<IWorkflowNodeViewModel>`）、`LinkAdded` / `LinkRemoved`（`EventHandler<IWorkflowLinkViewModel>`）、`VisibleItemAdded` / `VisibleItemRemoved`（`EventHandler<IWorkflowViewModel>`）。

| 方法 | 签名 | 说明 |
|---|---|---|
| `Install` / `Uninstall` | `void Install(IWorkflowTreeViewModel tree)` / `void Uninstall(IWorkflowTreeViewModel tree)` | 生命周期钩子；`Install` 订阅 `Nodes`/`Links` 集合 |
| `CreateNode` | `void CreateNode(IWorkflowNodeViewModel node)` | → `StandardCreateNode` |
| `CreateLink` | `IWorkflowLinkViewModel CreateLink(IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | 默认返回 `LinkDefaultViewModel` |
| `SetPointer` | `void SetPointer(Anchor anchor)` | 移动虚拟连接的接收端 |
| `ValidateConnection` | `bool ValidateConnection(IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver)` | 可覆写；默认 `true` |
| `SendConnection` / `ReceiveConnection` | `void SendConnection(IWorkflowSlotViewModel slot)` / `void ReceiveConnection(IWorkflowSlotViewModel slot)` | 两阶段连接 |
| `ResetVirtualLink` | `void ResetVirtualLink()` | 隐藏虚拟连接 |
| `Virtualize` | `void Virtualize(Viewport viewport)` | 空间虚拟化 |
| `Submit` | `void Submit(IWorkflowActionPair actionPair)` | 压入撤销栈 |
| `Redo` / `Undo` / `ClearHistory` | `void Redo()` / `void Undo()` / `void ClearHistory()` | 栈操作 |
| `MarkDirty` | `void MarkDirty()` | 标记树需要重新虚拟化 |

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowTreeViewModel.cs`。*

#### `IWorkflowNodeViewModel : IWorkflowViewModel`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Parent` | `IWorkflowTreeViewModel?` | 所属树 |
| `Anchor` | `Anchor` | 画布位置（X、Y、图层） |
| `Size` | `Size` | 宽 / 高 |
| `Slots` | `ObservableCollection<IWorkflowSlotViewModel>` | 所属槽位 |
| `MoveCommand` | `IVeloxCommand` | 参数 `Offset` |
| `SetAnchorCommand` | `IVeloxCommand` | 参数 `Anchor` |
| `SetSizeCommand` | `IVeloxCommand` | 参数 `Size` |
| `CreateSlotCommand` | `IVeloxCommand` | 参数 `IWorkflowSlotViewModel` |
| `DeleteCommand` | `IVeloxCommand` | 参数 null；级联删除槽位与连接 |
| `ReceiveCommand` | `IVeloxCommand` | 参数可空 `ITaskContext` |
| `BroadcastCommand` | `IVeloxCommand` | 正向广播，参数可空 |
| `ReverseBroadcastCommand` | `IVeloxCommand` | 反向广播，参数可空 |

**`IWorkflowNodeViewModelHelper : IWorkflowHelper`**

事件：`SlotAdded` / `SlotRemoved`（`EventHandler<IWorkflowSlotViewModel>`）。

| 方法 | 签名 | 说明 |
|---|---|---|
| `Install` / `Uninstall` | `void Install(IWorkflowNodeViewModel node)` / `void Uninstall(IWorkflowNodeViewModel node)` | 生命周期钩子 |
| `CreateSlot` | `void CreateSlot(IWorkflowSlotViewModel slot)` | → `StandardCreateSlot` |
| `Move` / `SetAnchor` / `SetSize` | `void Move(Offset)` / `void SetAnchor(Anchor)` / `void SetSize(Size)` | 变更几何 + `MarkDirty` |
| `ReceiveAsync` | `Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)` | **唯一执行入口**（可空 data/sender/receiver）；返回非空值让编译器链式传递结果 |
| `BroadcastAsync` | `Task BroadcastAsync(object? parameter, CancellationToken ct)` | 驱动所有下游 `ReceiveCommand` |
| `ReverseBroadcastAsync` | `Task ReverseBroadcastAsync(object? parameter, CancellationToken ct)` | 驱动所有上游 `ReceiveCommand` |
| `ValidateBroadcastAsync` | `Task<bool> ValidateBroadcastAsync(IWorkflowSlotViewModel sender, IWorkflowSlotViewModel receiver, object? parameter, CancellationToken ct)` | 逐连接广播门；默认 `true` |
| `Delete` | `void Delete()` | → `StandardDelete`（原子、可撤销） |

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`。*

#### `IWorkflowSlotViewModel : IWorkflowViewModel`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Targets` / `Sources` | `ObservableCollection<IWorkflowSlotViewModel>` | 已连接的同行（出向 / 入向） |
| `Parent` | `IWorkflowNodeViewModel?` | 所属节点 |
| `Channel` | `SlotChannel` | 连接容量（位标志） |
| `State` | `SlotState` | 连接状态（位标志） |
| `Anchor` | `Anchor` | 画布上的位置 |
| `SetChannelCommand` | `IVeloxCommand` | 参数 `SlotChannel` |
| `SendConnectionCommand` | `IVeloxCommand` | 作为发送端开始 |
| `ReceiveConnectionCommand` | `IVeloxCommand` | 作为接收端接受 |
| `DeleteCommand` | `IVeloxCommand` | 参数 null |

**`IWorkflowSlotViewModelHelper : IWorkflowHelper`** —— 事件 `TargetAdded/Removed`、`SourceAdded/Removed`；方法 `Install/Uninstall`、`SetChannel(SlotChannel)`、`UpdateState()`、`SendConnection()`、`ReceiveConnection()`、`Delete()`。

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowSlotViewModel.cs`。*

#### `IWorkflowLinkViewModel : IWorkflowViewModel`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Sender` | `IWorkflowSlotViewModel` | 源槽位 |
| `Receiver` | `IWorkflowSlotViewModel` | 目标槽位 |
| `IsVisible` | `bool` | 渲染可见性 |
| `DeleteCommand` | `IVeloxCommand` | 参数 null |

**`IWorkflowLinkViewModelHelper : IWorkflowHelper`** —— `Install/Uninstall(IWorkflowLinkViewModel)`、`Delete()`。

*源码：`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IWorkflowLinkViewModel.cs`。*

#### 其他接口

| 类型 | 签名 / 成员 |
|---|---|
| `IWorkflowActionPair` | `Action Redo { get; }`、`Action Undo { get; }` |
| `IWorkflowIdentifiable` | `string RuntimeId { get; }` —— 组件生命周期内唯一 |
| `IContext` | 空标记 —— 上下文体系根契约（`ITaskContext`、`IRuntimeContext`、`ICompileContext`） |
| `ITaskContext : IContext` | `object? Data`、`IWorkflowSlotViewModel? Sender`、`IWorkflowSlotViewModel? Receiver` —— 传给 `ReceiveCommand → ReceiveAsync` 的可空载荷 |
| `ISlotProvider` | `IEnumerable<SlotDefinition> GetSlots()` —— 以实例列表驱动 `SlotEnumerator` |
| `ISpatialMap<T>` | `T : class, ISpatialBoundsProvider`；`Insert(T)`、`Remove(T)`、`Query(Viewport)`、`Clear()`、`Bounds` |
| `ISpatialBoundsProvider` | `Viewport Bounds { get; }` + `INotifyPropertyChanged`；变更时引发 `PropertyChanged("Bounds")` |

*源码：`Interfaces/WorkflowSystem/IWorkflowActionPair.cs`、`IWorkflowIdentifiable.cs`、`IContext.cs`、`ITaskContext.cs`、`ISlotProvider.cs`、`ISpatialMap.cs`、`ISpatialBoundsProvider.cs`。*

### 值类型与枚举

| 类型 | 说明 |
|---|---|
| `Anchor(left, top, layer)` | 位置；`ICloneable`、`IEquatable<Anchor>`、`IInterpolable`；`==`/`!=`/`+`/`-` 运算符 |
| `Size(width, height)` | 尺寸；`ICloneable`、`IEquatable<Size>`、`IInterpolable` |
| `Offset(left, top)` | 增量向量；`ICloneable`、`IEquatable<Offset>`、`IInterpolable` |
| `Viewport(left, top, width, height)` | `readonly struct`；`Empty`、`Right`、`Bottom`、`IsEmpty`、`Contains`、`IntersectsWith`、`Union`、`==`/`!=` |
| `CanvasLayout` | `OriginSize`、`PositiveOffset`、`NegativeOffset`、`ActualSize`、`ActualOffset`、`ViewportOffset`；`AdaptTo(Size)`；`UpdateCommand` |
| `CellKey(x, y)` | `readonly struct` 网格单元坐标；`==`/`!=` |
| `TaskContext(data, sender, receiver)` | `readonly struct : ITaskContext`；`Deconstruct(out data, out sender, out receiver)` |
| `WorkflowActionPair(redo, undo)` | `readonly struct : IWorkflowActionPair` |
| `SlotChannel` | `[Flags] int`：`None=0`、`OneTarget=1`、`OneSource=2`、`OneBoth=3`、`MultipleTargets=4`、`MultipleSources=8`、`MultipleBoth=12` |
| `SlotState` | `[Flags] int`：`StandBy=1`、`PreviewSender=2`、`PreviewReceiver=4`、`Sender=8`、`Receiver=16` |

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/` 下的 `Anchor.cs`、`Size.cs`、`Offset.cs`、`Viewport.cs`、`CanvasLayout.cs`、`CellKey.cs`、`TaskContext.cs`、`WorkflowActionPair.cs`、`Enums/Slot.cs`。*

### 默认 ViewModel 与 Helper

| 默认 ViewModel | 默认 Helper | 用途 |
|---|---|---|
| `TreeDefaultViewModel` | `TreeHelper<T>` | 根容器；`CreateLink` 返回 `LinkDefaultViewModel` |
| `NodeDefaultViewModel` | `NodeHelper<T>` | 节点：`Move/SetAnchor/SetSize/CreateSlot/Receive/Broadcast/ReverseBroadcast/Delete` |
| `SlotDefaultViewModel` | `SlotHelper<T>` | 槽位：通道 / 状态处理 |
| `LinkDefaultViewModel` | `LinkHelper<T>` | 连接：`Delete` |

说明：

- `TreeHelper()` 关闭虚拟化；`TreeHelper(double cellSize)` 开启。类型标注 `[MonoBehaviour(channel: nameof(TreeHelper), fps: 10)]`，`Install` 时调用 `tree.EnableMap(CellSize, VisibleItems)`。`CellSize` 默认 `200`。
- `NodeHelper.SetAnchor/SetSize/Move` 在变更后调用 `Component.Parent.GetHelper().MarkDirty()`。
- `NodeDefaultViewModel.ReceiveCommand` 把参数包装成 `TaskContext` 并调用 `Helper.ReceiveAsync(ctx, ct)` —— 携带可空 data/sender/receiver 的唯一接收路径（`NodeDefaultViewModel.cs` 第 67-72 行）。
- 四个默认 ViewModel 都实现 `IWorkflowIdentifiable`（`RuntimeId = Guid.NewGuid().ToString("N")`）。

*源码：`Templates/ViewModels/*.cs`、`Templates/Helpers/*.cs`。*

### `NodeLayoutAttributes`

| 属性 | 效果 |
|---|---|
| `[DefaultAnchor(horizontal = 0, vertical = 0, layer = 0)]` | 源生成器把默认 `Anchor` 烘焙进后备字段初始化器 |
| `[DefaultSize(width = 0, height = 0)]` | 源生成器把默认 `Size` 烘焙进后备字段初始化器 |

*源码：`Templates/NodeLayoutAttributes.cs`。*

### 选择器系统（`SelectorEx`）

| 类型 | 说明 |
|---|---|
| `SlotEnumerator<TSlot>` | 动态槽位集合（`TSlot : IWorkflowSlotViewModel, new()`）。`SetSelector(object?)`（`Type`、类型名字符串或 `ISlotProvider`）、`TrySelect(object, out TSlot?)`、`Items`、`Count`、索引器、`CurrentValue`、`SelectorType`、`SelectorTypeName`、`Install(parent, memberName)`、`Uninstall()`。选择器切换以可撤销操作提交；各类型的槽位状态跨切换记忆。 |
| `ConditionalSlot<TSlot>` | `SlotEnumerator.Items` 中的一项：`Name`、`Value`、`Slot`。 |
| `SlotDefinition(value, label)` | `ISlotProvider` 产生的条目。 |
| `ISlotProvider` | `IEnumerable<SlotDefinition> GetSlots()` —— 以任意路由驱动枚举器。 |
| `[SlotSelectors(params Type[] or params string[])]` | `VeloxDev.AI` 属性，声明 `SlotEnumerator` 属性上允许的选择器类型。 |
| `IConditionalSlotProvider<TSlot>` | `SlotEnumerator<TSlot>` 实现的契约：`Parent`、`SelectorTypeName`、`Items`、`CurrentValue`、`TrySelect`、`SetSelector`、`Install`、`Uninstall`。 |

`TrySelect` 是在 `conditionMap` 上的字典查找（期望 `O(1)`）。`CurrentValue` 的 getter 返回字符串形式；setter 接受字符串 / 枚举 / 数值并归一化。

*源码：`SelectorEx/SlotEnumerator.cs`、`SelectorEx/ConditionalSlot.cs`、`SelectorEx/SlotDefinition.cs`、`Interfaces/WorkflowSystem/ISlotProvider.cs`、`Interfaces/WorkflowSystem/IConditionalSlotProvider.cs`、`Src/Core/VeloxDev.Core/AI/SlotSelectorsAttribute.cs`。*

### 空间系统

| 类型 | 说明 |
|---|---|
| `SpatialGridHashMap<T>` | 通用网格空间哈希（`T : class, ISpatialBoundsProvider`）。`Insert`、`Remove`、`Query(Viewport)`、`Clear`、`Bounds`。单元尺寸在构造时设置（`Math.Max(1d, cellSize)`）。 |
| `WorkflowSpatialManager` | 树级管理器，索引节点（`NodeBoundsProvider`）与节点对（`NodePairBoundsProvider`，表示连接）。`GlobalBounds`、`QueryNodes(Viewport)`、`QueryAgentBounds`（内部，深度展开）。 |
| `WorkflowSpatialEx` | 扩展：`EnableMap(tree, cellSize, observable)`、`Virtualize(tree, viewport)`、`QueryNodes(tree, viewport)`、`ClearMap(tree)`。 |
| `ISpatialMap<T>` / `ISpatialBoundsProvider` | 空间抽象（见上文「其他接口」）。 |

*源码：`WorkflowSystem/SpatialGridHashMap.cs`、`WorkflowSystem/WorkflowSpatialManager.cs`、`WorkflowSystem/NodeBoundsProvider.cs`、`WorkflowSystem/NodePairBoundsProvider.cs`、`StandardEx/WorkflowSpatialEx.cs`、`Interfaces/WorkflowSystem/ISpatialMap.cs`、`Interfaces/WorkflowSystem/ISpatialBoundsProvider.cs`。*

### 渲染就绪辅助（核心层，与 GUI 无关）

| 类型 | 说明 |
|---|---|
| `WorkflowSlotUpdateGate` | `IsLinkRenderReady(IWorkflowLinkViewModel)` —— 双端锚点均非 NaN（或未挂载）时为真 |
| `WorkflowLinkRenderEx` | `bool IsRenderReady(this IWorkflowLinkViewModel)` —— `IsVisible && WorkflowSlotUpdateGate.IsLinkRenderReady(link)` |
| `WorkflowGuard` | `[Conditional("DEBUG")] Fail(message)` —— 仅调试态的契约守卫，抛出 `InvalidOperationException` |

*源码：`WorkflowSlotUpdateGate.cs`、`WorkflowLinkRenderEx.cs`、`WorkflowGuard.cs`。*
