# 组件契约

每个工作流类型都实现 `IWorkflowComponent`；四个角色在此基础上加入自己的状态与命令。助手是安装在组件上的独立对象，因此替换行为不必替换模型。

## 命名空间

`VeloxDev.WorkflowSystem`（程序集 `VeloxDev.Core`）。命令属性的类型是 `VeloxDev.MVVM` 的 `IVeloxCommand`。

## IWorkflowComponent

**签名：** `interface IWorkflowComponent : INotifyPropertyChanging, INotifyPropertyChanged`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `InitializeWorkflow()` | `void` | 安装组件助手并填充生成成员。 |
| `OnPropertyChanging(string)` | `void` | 为 `propertyName` 触发变更前通知。 |
| `OnPropertyChanged(string)` | `void` | 为 `propertyName` 触发变更后通知。 |
| `CloseCommand` | `IVeloxCommand` | 终止该组件拥有的全部运行中任务。 |

同命名空间的 `IRuntimeIdentifiable` 增加 `string RuntimeId { get; }`。默认视图模型在构造时分配新的 GUID 字符串；该标识在集合变动间保持稳定，也是检查点使用的节点键。

## ITreeComponent

**签名：** `interface ITreeComponent : IWorkflowComponent`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Layout` | `CanvasLayout` | 画布尺寸、偏移、缩放与缩放中心。 |
| `VirtualLink` | `ILinkComponent` | 连线拖拽期间显示的临时连线。 |
| `Nodes` | `ObservableCollection<INodeComponent>` | 工作区内的全部节点。 |
| `Links` | `ObservableCollection<ILinkComponent>` | 工作区内的全部连线。 |
| `LinksMap` | `Dictionary<ISlotComponent, Dictionary<ISlotComponent, ILinkComponent>>` | 发送端插槽 → 接收端插槽 → 连线。 |
| `CreateNodeCommand` | `IVeloxCommand` | 参数 `INodeComponent`；一步可撤销操作。 |
| `SetPointerCommand` | `IVeloxCommand` | 参数 `Anchor`；移动临时连线的接收端。 |
| `ResetVirtualLinkCommand` | `IVeloxCommand` | 清空临时连线。 |
| `SendConnectionCommand` | `IVeloxCommand` | 参数 `ISlotComponent`（发送端）。 |
| `ReceiveConnectionCommand` | `IVeloxCommand` | 参数 `ISlotComponent`（接收端）。 |
| `SubmitCommand` | `IVeloxCommand` | 参数 `IActionPair`。 |
| `RedoCommand` / `UndoCommand` | `IVeloxCommand` | 无参数。 |
| `GetHelper()` / `SetHelper(ITreeHelper)` | `ITreeHelper` / `void` | 读取或替换已安装的助手。 |

## ITreeHelper

**签名：** `interface ITreeHelper : IWorkflowHelper`

事件：`NodeAdded`、`NodeRemoved`（`EventHandler<INodeComponent>`）；`LinkAdded`、`LinkRemoved`（`EventHandler<ILinkComponent>`）；`VisibleItemAdded`、`VisibleItemRemoved`（`EventHandler<IWorkflowComponent>`）。

属性：`VisibleItems`（`ObservableCollection<IWorkflowComponent>`）、`Viewport`（`Viewport`）。

| 方法 | 返回 | 说明 |
| --- | --- | --- |
| `Install(ITreeComponent)` / `Uninstall(ITreeComponent)` | `void` | 绑定或解绑助手。 |
| `CreateNode(INodeComponent)` | `void` | 以一步可撤销操作加入节点。 |
| `CreateLink(ISlotComponent, ISlotComponent)` | `ILinkComponent` | 构造该树使用的连线类型。 |
| `SetPointer(Anchor)` | `void` | 移动临时接收端。 |
| `ValidateConnection(ISlotComponent, ISlotComponent)` | `bool` | 树自身的连接规则；默认 `true`。 |
| `SendConnection(ISlotComponent)` / `ReceiveConnection(ISlotComponent)` | `void` | 开始或完成一次连线拖拽。 |
| `ResetVirtualLink()` | `void` | 清空临时连线。 |
| `Virtualize(Viewport)` | `void` | 为视口重建 `VisibleItems`。 |
| `Submit(IActionPair)` / `Undo()` / `Redo()` / `ClearHistory()` | `void` | 撤销历史控制。 |
| `MarkDirty()` | `void` | 为虚拟化趟次标脏。 |

## INodeComponent

**签名：** `interface INodeComponent : IWorkflowComponent`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Parent` | `ITreeComponent?` | 所属树。 |
| `Anchor` | `Anchor` | 世界坐标；getter 返回按缩放坍缩后的视图值。 |
| `Size` | `Size` | 世界尺寸；getter 返回按缩放坍缩后的视图值。 |
| `Slots` | `ObservableCollection<ISlotComponent>` | 节点拥有的端口。 |
| `MoveCommand` | `IVeloxCommand` | 参数 `Offset`（视图空间增量）。 |
| `SetAnchorCommand` / `SetSizeCommand` | `IVeloxCommand` | 参数 `Anchor` / `Size`（世界值）。 |
| `CreateSlotCommand` | `IVeloxCommand` | 参数 `ISlotComponent`。 |
| `DeleteCommand` | `IVeloxCommand` | 以一步删除节点、插槽与连线。 |
| `ReceiveCommand` | `IVeloxCommand` | 参数 `ITaskContext?`；唯一执行入口。 |
| `BroadcastCommand` / `ReverseBroadcastCommand` | `IVeloxCommand` | 参数 `object?`；沿 `Targets` / `Sources` 传播数据。 |
| `GetHelper()` / `SetHelper(INodeHelper)` | `INodeHelper` / `void` | 读取或替换已安装的助手。 |

## INodeHelper

**签名：** `interface INodeHelper : IWorkflowHelper`

事件：`SlotAdded`、`SlotRemoved`（`EventHandler<ISlotComponent>`）。

| 方法 | 返回 | 说明 |
| --- | --- | --- |
| `Install(INodeComponent)` / `Uninstall(INodeComponent)` | `void` | 绑定或解绑助手。 |
| `CreateSlot(ISlotComponent)` | `void` | 加入端口。 |
| `Move(Offset)` / `SetAnchor(Anchor)` / `SetSize(Size)` | `void` | 几何变更。 |
| `ReceiveAsync(ITaskContext, CancellationToken)` | `Task<object?>` | 执行节点；非空结果链式传给下一节点。 |
| `BroadcastAsync(object?, CancellationToken)` | `Task` | 沿每条出边发送。 |
| `ReverseBroadcastAsync(object?, CancellationToken)` | `Task` | 沿每条入边发送。 |
| `AccessAsync(IAccessContext, CancellationToken)` | `Task<bool>` | 编译期与运行期复用的边访问检查。 |
| `Delete()` | `void` | 删除节点。 |

`AccessAsync` 收到 `IAccessContext`：`Sender` 与 `Receiver` 是边的两端插槽，`Data` 是载荷（编译期为 null），`IsCompilePhase` 区分两个阶段。返回 `false` 表示该边按未连接处理。

## ISlotComponent

**签名：** `interface ISlotComponent : IWorkflowComponent`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Targets` | `ObservableCollection<ISlotComponent>` | 本插槽连出的插槽。 |
| `Sources` | `ObservableCollection<ISlotComponent>` | 连入本插槽的插槽。 |
| `Parent` | `INodeComponent?` | 所属节点。 |
| `Channel` | `SlotChannel` | 方向与容量（见[连接规则](../../02_连接规则与预览/00_连接规则/index.md)）。 |
| `State` | `SlotState` | 连接与拖拽状态标志。 |
| `Anchor` | `Anchor` | 端口在画布上的位置。 |
| `SetChannelCommand` | `IVeloxCommand` | 参数 `SlotChannel`；不产生撤销项。 |
| `SendConnectionCommand` / `ReceiveConnectionCommand` | `IVeloxCommand` | 以本插槽开始或接受连线。 |
| `DeleteCommand` | `IVeloxCommand` | 删除插槽及其连线。 |
| `GetHelper()` / `SetHelper(ISlotHelper)` | `ISlotHelper` / `void` | 读取或替换已安装的助手。 |

## ISlotHelper

**签名：** `interface ISlotHelper : IWorkflowHelper`

事件：`TargetAdded`、`TargetRemoved`、`SourceAdded`、`SourceRemoved`（`EventHandler<ISlotComponent>`）。

方法：`Install(ISlotComponent)`、`Uninstall(ISlotComponent)`、`SetChannel(SlotChannel)`、`UpdateState()`、`SendConnection()`、`ReceiveConnection()`、`Delete()`。

## ILinkComponent

**签名：** `interface ILinkComponent : IWorkflowComponent`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Sender` | `ISlotComponent` | 源端口。 |
| `Receiver` | `ISlotComponent` | 目标端口。 |
| `IsVisible` | `bool` | 是否绘制。 |
| `DeleteCommand` | `IVeloxCommand` | 以一步删除连线。 |
| `GetHelper()` / `SetHelper(ILinkHelper)` | `ILinkHelper` / `void` | 读取或替换已安装的助手。 |

## ILinkHelper

**签名：** `interface ILinkHelper : IWorkflowHelper`

方法：`Install(ILinkComponent)`、`Uninstall(ILinkComponent)`、`Delete()`。

## IWorkflowHelper

**签名：** `interface IWorkflowHelper`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Closing()` | `void` | 关闭前锁定助手的命令。 |
| `CloseAsync()` | `Task` | 安全关闭组件。 |
| `Closed()` | `void` | 关闭后解锁助手的命令。 |

## 示例

```csharp
ITreeComponent tree = new TreeDefaultViewModel();
INodeComponent node = new NodeDefaultViewModel
{
    Anchor = new Anchor(60, 80, 0),
    Size = new Size(220, 120),
};
tree.GetHelper().CreateNode(node);

// 未挂载的节点仍报告自己的标识与助手。
Console.WriteLine($"{node.RuntimeId.Length} {node.GetHelper().GetType().Name}");
```
