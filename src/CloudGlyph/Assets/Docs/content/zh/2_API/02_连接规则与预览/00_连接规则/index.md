# 连接规则

规则集是纯函数，预览与释放路径共用。通道决定方向与容量；检查会指出第一条拒绝该对的规则。

命名空间：`VeloxDev.WorkflowSystem`（类型）与 `VeloxDev.WorkflowSystem.StandardEx`（操作）。

## ConnectionRejectReason

**签名：** `enum ConnectionRejectReason`

| 值 | 含义 |
| --- | --- |
| `None = 0` | 检查通过。 |
| `SenderCannotSend = 1` | 发送端通道没有出方向。 |
| `ReceiverCannotReceive = 2` | 接收端通道没有入方向。 |
| `SameNode = 3` | 两端属于同一节点。 |
| `RejectedByRule = 4` | `ITreeHelper.ValidateConnection` 返回 `false`。 |
| `RejectedByHost = 5` | 某个 `WorkflowInput.PreviewValidating` 订阅者拒绝了本次预览。 |

## ConnectionCheck

**签名：** `readonly struct ConnectionCheck : IEquatable<ConnectionCheck>`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Valid` | `ConnectionCheck` | 通过的检查。 |
| `IsValid` | `bool` | 规则是否接受该对。 |
| `Reason` | `ConnectionRejectReason` | 失败原因，或 `None`。 |
| `Message` | `string?` | 可选宿主说明；框架原因时为 null。 |
| `Rejected(ConnectionRejectReason reason, string? message = null)` | `ConnectionCheck` | 构造失败检查。 |
| `Equals(ConnectionCheck)` / `Equals(object?)` / `GetHashCode()` | | 值语义。 |
| `ToString()` | `string` | `Valid`、`Rejected(Reason)` 或 `Rejected(Reason: message)`。 |

容量**不是**拒绝理由：完成连接时会按通道清理既有连线，因此通过的检查意为「可接受，可能在该清理之后」。

## SlotChannel

**签名：** `[Flags] enum SlotChannel : int`

| 值 | 位 | 含义 |
| --- | --- | --- |
| `None = 0` | — | 不允许连接。 |
| `OneTarget = 1` | 出 | 一条出连线。 |
| `OneSource = 2` | 入 | 一条入连线。 |
| `OneBoth = 3` | 双向各一 | 每个方向一条。 |
| `MultipleTargets = 4` | 出 | 任意多条出连线。 |
| `MultipleSources = 8` | 入 | 任意多条入连线。 |
| `MultipleBoth = 12` | 双向任意 | 每个方向任意多条。 |

生成的插槽起始为 `MultipleBoth`；默认视图模型起始为 `OneBoth`。

## SlotState

**签名：** `[Flags] enum SlotState : int`

| 值 | 含义 |
| --- | --- |
| `StandBy = 1` | 无连接、无拖拽。 |
| `PreviewSender = 2` | 本插槽是进行中拖拽的发送端。 |
| `PreviewReceiver = 4` | 本插槽是指针下的候选接收端。 |
| `Sender = 8` | 至少一条出连线。 |
| `Receiver = 16` | 至少一条入连线。 |

`Sender` 与 `Receiver` 可组合。预览位由 `WorkflowInput` 拥有，不由连接列表决定。

## StandardCheckConnection

**签名：** `static ConnectionCheck StandardCheckConnection(this ITreeComponent component, ISlotComponent sender, ISlotComponent receiver)`

纯查询：无事件、无状态变化、无预览。依次检查：发送端可发送、接收端可接收、不同父节点，最后是 `component.GetHelper().ValidateConnection`。

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `component` | `ITreeComponent` | 拥有两端插槽的树。 |
| `sender` | `ISlotComponent` | 拟议源。 |
| `receiver` | `ISlotComponent` | 拟议目标。 |

**返回：** `ConnectionCheck` —— 第一条拒绝，或 `Valid`。

**异常：** 任一参数为 null 时抛 `ArgumentNullException`。

该方法刻意不触发 `ITreeEvents.Connecting`；那个事件只在释放时逐次否决。

## StandardSendConnection

**签名：** `static void StandardSendConnection(this ITreeComponent component, ISlotComponent slot)`

从 `slot` 开始连线拖拽。若该插槽不能作发送端，则重置临时连线。否则按通道清理发送端既有连接，把插槽锚点复制到 `VirtualLink` 两端，设 `IsVisible = true`，标记 `SlotState.PreviewSender`，并在 `WorkflowInput.For(component)` 上记录发送端。未挂载到树的插槽调用 `WorkflowGuard.Fail`。

## StandardReceiveConnection

**签名：** `static void StandardReceiveConnection(this ITreeComponent component, ISlotComponent slot)`

在 `slot` 处完成拖拽。顺序为：接收端能力、`ITreeEvents.Connecting`（句柄 `PreventDefault` 则重置并停止）、同一规则集（跳过发送端检查）、同向清理、接收端通道清理、以一项撤销创建连线、`Connected`、重置。

若无进行中的拖拽（`WorkflowInput.ConnectionSender` 为 null），调用无操作。

## StandardResetVirtualLink

**签名：** `static void StandardResetVirtualLink(this ITreeComponent component)`

隐藏临时连线，两端移到 `Anchor(NaN, NaN, 0)`，并清空输入路由的拖拽状态与预览位。

## 清理语义

完成连接会移除通道不允许的连接，且属于同一个逻辑操作：

- 通道含 `OneTarget` 或 `OneBoth` 的发送端丢弃既有出连线；
- 通道含 `OneSource` 或 `OneBoth` 的接收端丢弃既有入连线；
- 同向连接同一对节点的既有连线被最新一条替换；
- 所有移除都作为撤销项提交，因此撤销新连接也会恢复被挤掉的连接。

## 示例

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel();
var b = new NodeDefaultViewModel();
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

var from = new SlotDefaultViewModel();
var to = new SlotDefaultViewModel();
a.CreateSlotCommand.Execute(from);
b.CreateSlotCommand.Execute(to);

from.SetChannelCommand.Execute(SlotChannel.OneTarget);
to.SetChannelCommand.Execute(SlotChannel.OneSource);

Console.WriteLine(tree.StandardCheckConnection(from, to)); // Valid
Console.WriteLine(tree.StandardCheckConnection(from, from)); // Rejected(SameNode)

tree.GetHelper().SendConnection(from);
tree.GetHelper().ReceiveConnection(to);
Console.WriteLine(tree.Links.Count); // 1
```
