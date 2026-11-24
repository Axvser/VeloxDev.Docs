# 组件助手

助手承载一个组件的行为，替换它不必替换模型。每个角色都有一个非泛型类（闭合到接口类型）和一个泛型类（`Component` 是宿主的具象视图模型）。

所有类型都在 `VeloxDev.WorkflowSystem`，并通过公开 `InputRelay Input` 实现 `IInputEvents`。

## `TreeHelper` 与 `TreeHelper<T>`

**签名：** `class TreeHelper<T> : ITreeHelper, ITreeEvents, IInputEvents, IWorkflowLayoutHost where T : class, ITreeComponent`

`TreeHelper` 即 `TreeHelper<ITreeComponent>`，有两个构造函数：`TreeHelper()`（关闭虚拟化）与 `TreeHelper(double cellSize)`（开启虚拟化并启动 tickable）。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Component` | `T?` | 已安装且匹配 `T` 的树；protected setter。 |
| `Input` | `InputRelay` | 本组件的指针与键盘事件。 |
| `VisibleItems` | `ObservableCollection<IWorkflowComponent>` | 当前可见集。 |
| `Viewport` | `Viewport` | 赋值时调用 `Component.Virtualize(value)`。 |
| `NodeAdded` / `NodeRemoved` | `EventHandler<INodeComponent>` | 由 `Nodes` 集合触发。 |
| `LinkAdded` / `LinkRemoved` | `EventHandler<ILinkComponent>` | 由 `Links` 集合触发。 |
| `VisibleItemAdded` / `VisibleItemRemoved` | `EventHandler<IWorkflowComponent>` | 由 `VisibleItems` 触发。 |
| `Connecting` / `Connected` | `EventHandler<ConnectionEventArgs>` | 连接否决与报告。 |
| `LayoutSolver` | `IWorkflowLayoutSolver` | 每树一份布局解；默认 `DefaultWorkflowLayoutSolver`。 |
| `Install(ITreeComponent)` / `Uninstall(ITreeComponent)` | `void` | 订阅集合变化；虚拟化助手还会启用空间索引。 |
| `WithSynchronizationContext(SynchronizationContext?)` | `TreeHelper<T>` | 把虚拟化趟次绑定到 UI 上下文；`null` 表示就地执行。 |
| `Closing()` / `CloseAsync()` / `Closed()` | `void` / `Task` / `void` | 锁定、关闭、解锁标准命令。 |
| `CreateLink(ISlotComponent, ISlotComponent)` | `ILinkComponent` | 默认返回 `LinkDefaultViewModel`。 |
| `CreateNode(INodeComponent)` / `SetPointer(Anchor)` / `Virtualize(Viewport)` | `void` | 转发到树的标准操作。 |
| `ValidateConnection(ISlotComponent, ISlotComponent)` | `bool` | 默认 `true`；覆写以声明整棵树的规则。 |
| `SendConnection` / `ReceiveConnection` / `ResetVirtualLink` | `void` | 连线拖拽生命周期。 |
| `RaiseConnecting(...)` / `RaiseConnected(...)` | `WorkflowEventHandle` / `void` | 逐次否决的管线。 |
| `Submit(IActionPair)` / `Undo()` / `Redo()` / `ClearHistory()` / `MarkDirty()` | `void` | 撤销与脏标记。 |
| `Arrange(INodeComponent?, WorkflowLayoutOptions?)` | `WorkflowLayoutResult` | 运行 `LayoutSolver.Arrange`；未安装时抛异常。 |

protected virtual 的 `OnVisibleItemsAdded/Removed`、`OnNodeAdded/Removed`、`OnLinkAdded/Removed` 触发对应事件。

## `NodeHelper` 与 `NodeHelper<T>`

**签名：** `class NodeHelper<T> : INodeHelper, INodeEvents, IInputEvents, IConditionalSlotProviders where T : class, INodeComponent`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Component` | `T?` | 已安装的节点。 |
| `Input` | `InputRelay` | 指针与键盘事件。 |
| `Providers` | `IList<IConditionalSlotProvider>` | 安装在节点上的插槽枚举器。 |
| `SlotAdded` / `SlotRemoved` | `EventHandler<ISlotComponent>` | 由 `Slots` 触发。 |
| `Moving` / `Moved` | `EventHandler<NodeMoveEventArgs>` | 放置前后。 |
| `Resizing` / `Resized` | `EventHandler<NodeResizeEventArgs>` | 尺寸变化前后。 |
| `Deleting` / `Deleted` | `EventHandler<NodeEventArgs>` | 删除前后。 |
| `Install` / `Uninstall` | `void` | 绑定助手。 |
| `Closing` / `CloseAsync` / `Closed` | 生命周期 | 命令锁定/关闭/解锁。 |
| `CreateSlot(ISlotComponent)` | `void` | 标准插槽创建。 |
| `BroadcastAsync(object?, CancellationToken)` / `ReverseBroadcastAsync(...)` | `Task` | 沿 `Targets` / `Sources` 传播。 |
| `ReceiveAsync(ITaskContext, CancellationToken)` | `Task<object?>` | 默认返回 `null`；覆写以定义节点行为。 |
| `AccessAsync(IAccessContext, CancellationToken)` | `Task<bool>` | 默认 `true`。 |
| `SetAnchor(Anchor)` / `SetSize(Size)` / `Move(Offset)` | `void` | 标准几何写入，随后对树 `MarkDirty`。 |
| `Delete()` | `void` | 标准删除。 |
| `RaiseMoving` / `RaiseResizing` / `RaiseDeleting` | `WorkflowEventHandle` | 询问宿主；返回的句柄传给对应的 `RaiseMoved`/`RaiseResized`/`RaiseDeleted`。 |

## `SlotHelper` 与 `SlotHelper<T>`

**签名：** `class SlotHelper<T> : ISlotHelper, ISlotEvents, IInputEvents where T : class, ISlotComponent`

成员：`Component`（`T?`）、`Input`，事件 `TargetAdded`、`TargetRemoved`、`SourceAdded`、`SourceRemoved`；`Install`、`Uninstall`、`Closing`、`CloseAsync`、`Closed`；`SetChannel(SlotChannel)`、`UpdateState()`、`SendConnection()`、`ReceiveConnection()`、`Delete()`。

`ChannelChanging` / `ChannelChanged`（`EventHandler<SlotChannelEventArgs>`）经 `RaiseChannelChanging(SlotChannel from, SlotChannel to)` 与 `RaiseChannelChanged(...)` 运行。在 changing 句柄上设置 `PreventDefault` 会保留旧通道。

## `LinkHelper` 与 `LinkHelper<T>`

**签名：** `class LinkHelper<T> : ILinkHelper, ILinkHitTestable, IInputEvents where T : class, ILinkComponent`

成员：`Component`（`T?`）、`Input`、`Install`、`Uninstall`、`Closing`、`CloseAsync`、`Closed`、`Delete()`。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Visual` | `object?` | 发布曲线的控件；private setter。 |
| `Curve` | `LinkCurve?` | 视图最近一次发布的曲线。 |
| `SetCurve(LinkCurve?, object?)` | `void` | 保存曲线与控件；曲线清空时两者都清空。 |
| `Contains(double x, double y, double radius)` | `bool` | 对已发布曲线做命中测试。 |

## 示例

```csharp
// 替换整树规则而无需替换树。
public sealed class NoSelfLinks : TreeHelper<TreeDefaultViewModel>
{
    public override bool ValidateConnection(ISlotComponent sender, ISlotComponent receiver)
        => !ReferenceEquals(sender.Parent, receiver.Parent);
}

var tree = new TreeDefaultViewModel();
var helper = (TreeHelper<TreeDefaultViewModel>)tree.GetHelper();
helper.CreateNode(new NodeDefaultViewModel { Anchor = new Anchor(10, 20, 0) });
```

助手由生成组件的 `[WorkflowBuilder.*<THelper>]` 安装，或通过 `SetHelper` 传入。`NodeHelper<T>.Component` 只在已安装节点可赋给 `T` 时非空；`T` 不匹配的助手能观察节点，但访问不到其强类型成员。
