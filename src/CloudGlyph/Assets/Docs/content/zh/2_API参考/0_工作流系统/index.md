# 工作流系统 — API 参考

## 命名空间：`VeloxDev.WorkflowSystem`

### 核心接口

#### `IWorkflowTreeViewModel`
工作空间的根容器，管理所有 Node、Slot 和 Link 组件。

| 属性 | 类型 | 描述 |
|---|---|---|
| `Layout` | `CanvasLayout` | 画布大小和偏移信息 |
| `VirtualLink` | `IWorkflowLinkViewModel` | 仅在建立连接过程中可见的临时连接 |
| `Nodes` | `ObservableCollection<IWorkflowNodeViewModel>` | 所有 Node 组件 |
| `Links` | `ObservableCollection<IWorkflowLinkViewModel>` | 所有 Link 组件 |
| `LinksMap` | `Dictionary<IWorkflowSlotViewModel, Dictionary<IWorkflowSlotViewModel, IWorkflowLinkViewModel>>` | Slot 之间的连接关系映射 |

| 命令 | 参数 | 描述 |
|---|---|---|
| `CreateNodeCommand` | `IWorkflowNodeViewModel` | 创建节点 |
| `SetPointerCommand` | `Anchor` | 更新触点位置 |
| `ResetVirtualLinkCommand` | `null` | 重置虚拟连接 |
| `SendConnectionCommand` | `IWorkflowSlotViewModel` | 发起连接构建 |
| `ReceiveConnectionCommand` | `IWorkflowSlotViewModel` | 接收连接构建 |
| `SubmitCommand` | `IWorkflowActionPair` | 提交可撤销的操作 |
| `RedoCommand` | `null` | 重做操作 |
| `UndoCommand` | `null` | 撤销操作 |

#### `IWorkflowNodeViewModel`
表示画布上的单个节点。

| 属性 | 类型 | 描述 |
|---|---|---|
| `Parent` | `IWorkflowTreeViewModel?` | 所属的 Tree 组件 |
| `Anchor` | `Anchor` | 在画布中的锚点坐标 |
| `Size` | `Size` | 节点的宽度和高度 |
| `Slots` | `ObservableCollection<IWorkflowSlotViewModel>` | 该节点拥有的所有 Slot 组件 |

| 命令 | 参数 | 描述 |
|---|---|---|
| `MoveCommand` | `Offset` | 按偏移量移动节点 |
| `SetAnchorCommand` | `Anchor` | 设置绝对锚点位置 |
| `SetSizeCommand` | `Size` | 设置节点尺寸 |
| `CreateSlotCommand` | `IWorkflowSlotViewModel` | 创建新槽位 |
| `DeleteCommand` | `null` | 删除此节点及相关 Slot 和 Link |
| `WorkCommand` | `object?` | 执行节点的工作逻辑 |
| `BroadcastCommand` | `object?` | 正向广播数据到连接节点 |
| `ReverseBroadcastCommand` | `object?` | 反向广播数据 |
| `CloseCommand` | `null` | 关闭节点 |

#### `IWorkflowSlotViewModel`
节点上的连接点。

| 属性 | 类型 | 描述 |
|---|---|---|
| `Parent` | `IWorkflowNodeViewModel?` | 所属的父节点 |
| `Targets` | `ObservableCollection<IWorkflowSlotViewModel>` | 连接的目标槽位 |
| `Sources` | `ObservableCollection<IWorkflowSlotViewModel>` | 连接的源槽位 |
| `Channel` | `SlotChannel` | 输入或输出通道 |
| `State` | `SlotState` | 当前连接状态 |
| `Anchor` | `Anchor` | 相对于父节点的位置 |

| 命令 | 参数 | 描述 |
|---|---|---|
| `SetChannelCommand` | `SlotChannel` | 更改槽位通道类型 |
| `SendConnectionCommand` | `IWorkflowSlotViewModel` | 连接到目标槽位 |
| `ReceiveConnectionCommand` | `IWorkflowSlotViewModel` | 接受来自源的连接 |
| `DeleteCommand` | `null` | 删除此槽位及其连接 |
| `CloseCommand` | `null` | 关闭槽位 |

#### `IWorkflowLinkViewModel`
表示两个槽位之间的视觉连接。

| 属性 | 类型 | 描述 |
|---|---|---|
| `Sender` | `IWorkflowSlotViewModel` | 源槽位 |
| `Receiver` | `IWorkflowSlotViewModel` | 目标槽位 |
| `IsVisible` | `bool` | 连接线是否可见 |
| `UsePolyline` | `bool` | 是否使用折线而非贝塞尔曲线渲染 |

---

### Helper 系统

Helper 定义了每个组件的生命周期和业务逻辑。

| 基类 | 类型参数 | 关键覆写方法 |
|---|---|---|
| `TreeHelper<T>` | `T : IWorkflowTreeViewModel` | `Install()`, `Uninstall()`, `CreateLink()`, `CreateNode()`, `ValidateConnection()` |
| `NodeHelper<T>` | `T : IWorkflowNodeViewModel` | `Install()`, `Uninstall()`, `WorkAsync()`, `ValidateBroadcastAsync()` |
| `SlotHelper<T>` | `T : IWorkflowSlotViewModel` | `Install()`, `Uninstall()`, `ValidateConnection()` |
| `LinkHelper<T>` | `T : IWorkflowLinkViewModel` | `Install()`, `Uninstall()` |

---

### 空间系统

#### `SpatialGridHashMap<T>`
用于高效视口查询的空间索引。

```csharp
var map = new SpatialGridHashMap<MyItem>(cellSize: 100);
map.Insert(item);
var results = map.Query(viewport).ToList();
map.Remove(item);
```

#### `WorkflowSpatialManager`
在 Tree 级别管理节点和节点对（连接线）的空间索引。

```csharp
var spatial = new WorkflowSpatialManager(tree, cellSize: 200);
Viewport bounds = spatial.GlobalBounds;
```

---

### 枚举和结构体

| 类型 | 描述 |
|---|---|
| `Anchor` | 包含 `Horizontal`、`Vertical`、`Layer`（Z 索引）的位置 |
| `Size` | 包含 `Width`、`Height` 的尺寸 |
| `Offset` | 包含 `Horizontal`、`Vertical` 的增量 |
| `Viewport` | 包含 `X`、`Y`、`Width`、`Height` 的矩形区域 |
| `CanvasLayout` | 包含 `ActualSize`、`OriginSize`、`ViewportOffset`、`ActualOffset` 的画布上下文 |
| `SlotChannel` | 枚举：`Input`、`Output` |
| `SlotState` | 枚举：槽位的连接状态 |
| `CellKey` | `SpatialGridHashMap` 使用的网格单元坐标 |

---

### 构建器属性（源生成器）

| 属性 | 应用目标 | 描述 |
|---|---|---|
| `[WorkflowBuilder.Tree<T>]` | 类 | 生成 Tree ViewModel 样板代码；`T` 需实现 `IWorkflowTreeViewModelHelper` |
| `[WorkflowBuilder.Node<T>]` | 类 | 生成 Node ViewModel 样板代码；`T` 需实现 `IWorkflowNodeViewModelHelper` |
| `[WorkflowBuilder.Slot<T>]` | 类 | 生成 Slot ViewModel 样板代码；`T` 需实现 `IWorkflowSlotViewModelHelper` |
| `[WorkflowBuilder.Link<T>]` | 类 | 生成 Link ViewModel 样板代码；`T` 需实现 `IWorkflowLinkViewModelHelper` |
