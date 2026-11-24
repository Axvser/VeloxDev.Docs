# 连接预览

`WorkflowInput` 是每棵树唯一的输入路由。连线拖拽期间，它拥有发送端、候选接收端与预览阶段；连线视图读取这份状态，而不是自行推导。

命名空间：`VeloxDev.WorkflowSystem`（类型）与 `VeloxDev.WorkflowSystem.StandardEx`（两个预览操作）。

## ConnectionPreviewState

**签名：** `enum ConnectionPreviewState`

| 值 | 含义 |
| --- | --- |
| `None = 0` | 无进行中的拖拽。 |
| `Started = 1` | 发送端已固定；指针不在候选上。 |
| `ValidTarget = 2` | 指针在可接收的插槽上。 |
| `InvalidTarget = 3` | 指针在会被拒绝的插槽上。 |

## IConnectionPreviewLink

**签名：** `interface IConnectionPreviewLink : ILinkComponent`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Preview` | `ConnectionPreviewState` | 当前拖拽阶段。 |
| `SetPreview(ConnectionPreviewState state)` | `void` | 由 `WorkflowInput` 调用；视图模型不自行调用。 |

该能力不放在 `ILinkComponent` 上，避免破坏既有实现者。`LinkDefaultViewModel` 实现了它。

## WorkflowInput

**签名：** `sealed class WorkflowInput`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `WorkflowInput(ITreeComponent tree)` | 构造函数 | 创建一个路由；null 抛 `ArgumentNullException`。 |
| `For(ITreeComponent tree)` | `WorkflowInput` | 该树的进程级实例，首次使用时创建，树存活期间保留。 |
| `Tree` | `ITreeComponent` | 本路由所属的树。 |
| `PointerTarget` | `IWorkflowComponent?` | 指针下的组件，空白画布为 null。 |
| `HoveredLink` | `ILinkComponent?` | `PointerTarget` 作为连线。 |
| `ConnectionSender` | `ISlotComponent?` | 拖拽源，或 null。 |
| `PreviewReceiver` | `ISlotComponent?` | 候选接收端，或 null。 |
| `PreviewState` | `ConnectionPreviewState` | 当前拖拽阶段。 |
| `PreviewCheck` | `ConnectionCheck?` | 候选的检查；无候选时为 null。 |
| `PreviewChanged` | `EventHandler<ConnectionPreviewEventArgs>` | 发送端、候选或阶段变化时触发。 |
| `PreviewValidating` | `EventHandler<ConnectionPreviewValidatingEventArgs>` | 每个框架会接受的新候选触发一次，显式刷新时再触发。 |
| `HitRadius` | `double` | 连线解析命中容差；默认 `LinkHitTestEx.DefaultHitRadius`。 |
| `IsSuspended` | `bool` | 置位后指针移动不再更新 `PointerTarget`。 |
| `Scroller` | `IWorkflowSurfaceScroller?` | 适配器注册的滚轮滚动能力。 |
| `Navigator` | `IWorkflowSurfaceNavigator?` | 适配器注册的居中能力。 |
| `Route(PointerEventArgs e)` | `void` | 把指针事件路由到目标及其祖先，再执行框架默认动作。null 抛 `ArgumentNullException`。 |
| `Route(KeyEventArgs e)` | `void` | 路由键盘事件；Core 中键盘没有默认动作。 |

`Route` 在投递事件本身之前，先向离开的组件发 `PointerExited`、向到达的组件发 `PointerEntered`。链路为 目标 → 所属节点（插槽时）→ 树。

## StandardSetPreviewReceiver

**签名：** `static void StandardSetPreviewReceiver(this ITreeComponent component, ISlotComponent? slot)`

报告指针下的候选。发送端永远不是自己的候选。重复同一候选开销很低：候选变化前不会再次询问宿主校验。`slot` 为 null 时预览回到 `Started`。

在候选上标记 `SlotState.PreviewReceiver`，并在临时连线实现 `IConnectionPreviewLink` 时更新其 `Preview`。

## StandardRefreshConnectionPreview

**签名：** `static void StandardRefreshConnectionPreview(this ITreeComponent component)`

对指针当前所在候选重跑检查，绕过同候选短路。适用于异步结论在指针到达候选之后才落地的情况。无进行中拖拽时无操作。

## ITreeEvents

**签名：** `interface ITreeEvents`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Connecting` | `EventHandler<ConnectionEventArgs>` | 在 `ValidateConnection` 之前触发，两者可组合。 |
| `Connected` | `EventHandler<ConnectionEventArgs>` | 连线存在后触发，携带同一句柄。 |
| `RaiseConnecting(ISlotComponent, ISlotComponent)` | `WorkflowEventHandle` | 询问宿主并返回供报告使用的句柄。 |
| `RaiseConnected(ISlotComponent, ISlotComponent, WorkflowEventHandle)` | `void` | 若句柄未停止传播则报告。 |

`TreeHelper<T>` 实现了该接口，因此常用 `(ITreeEvents)tree.GetHelper()`。

## ITreeEventSink

**签名：** `interface ITreeEventSink`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `OnConnecting(ConnectionEventArgs e)` | `void` | 连接前调用；用句柄拒绝。 |
| `OnConnected(ConnectionEventArgs e)` | `void` | 连线存在后调用。 |

sink 是宿主实现的形式；`WorkflowEventRelay` 是平台适配它的方式。

## ConnectionEventArgs

**签名：** `sealed class ConnectionEventArgs : EventArgs`

成员：构造函数 `(ISlotComponent sender, ISlotComponent receiver, WorkflowEventHandle handle)`；只读 `Sender`、`Receiver`、`Handle`。

## ConnectionPreviewEventArgs

**签名：** `sealed class ConnectionPreviewEventArgs : EventArgs`

成员：构造函数 `(ISlotComponent? sender, ISlotComponent? receiver, ConnectionPreviewState state, ConnectionCheck? check)`；只读 `Sender`、`Receiver`、`State`、`Check`。

## ConnectionPreviewValidatingEventArgs

**签名：** `sealed class ConnectionPreviewValidatingEventArgs : EventArgs`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Sender` / `Receiver` | `ISlotComponent` | 拖拽源与候选。 |
| `Check` | `ConnectionCheck` | 当前结论；初值为框架的结论。 |
| `Reject(string? message = null)` | `void` | 用 `RejectedByHost` 替换 `Check`。 |

预览只能收紧框架规则：框架已拒绝的候选不会送到这里。释放时的 `Connecting` 仍是最终决定。

## WorkflowEventHandle

**签名：** `sealed class WorkflowEventHandle`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `PreventDefault` | `bool` | 对 `…ing` 动作：拒绝它。对路由输入：让框架自身反应停下。对 `…ed` 报告：无效果。 |
| `StopPropagation` | `bool` | 阻止事件继续传播（祖先链或后续报告订阅者）。 |

同一个逻辑动作携带同一句柄实例，因此祖先或报告上的订阅者能看到更近订阅者的决定。

## 示例

```csharp
var tree = new TreeDefaultViewModel();
var input = WorkflowInput.For(tree);
input.PreviewChanged += (_, e) =>
    Console.WriteLine($"{e.State} reason={e.Check?.Reason}");

var from = new SlotDefaultViewModel();
var to = new SlotDefaultViewModel();
var nodeA = new NodeDefaultViewModel();
var nodeB = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(nodeA);
tree.GetHelper().CreateNode(nodeB);
nodeA.CreateSlotCommand.Execute(from);
nodeB.CreateSlotCommand.Execute(to);

tree.GetHelper().SendConnection(from);   // Started
tree.StandardSetPreviewReceiver(to);     // ValidTarget
input.PreviewValidating += (_, e) => e.Reject("policy");
tree.StandardRefreshConnectionPreview(); // InvalidTarget / RejectedByHost
tree.GetHelper().ResetVirtualLink();     // None
```
