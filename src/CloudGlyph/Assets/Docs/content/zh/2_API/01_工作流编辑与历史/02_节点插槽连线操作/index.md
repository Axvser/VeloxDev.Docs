# 节点插槽连线操作

三个静态类承载各组件的标准操作。它们既是组件命令的实现，也是宿主可覆写的钩子。

命名空间：`VeloxDev.WorkflowSystem.StandardEx`。

## WorkflowNodeEx

### GetStandardCommands

**签名：** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this INodeComponent component)`

按顺序返回：`SetAnchorCommand`、`SetSizeCommand`、`CreateSlotCommand`、`DeleteCommand`、`ReceiveCommand`、`BroadcastCommand`、`ReverseBroadcastCommand`。

### StandardCreateSlot

**签名：** `static void StandardCreateSlot(this INodeComponent component, ISlotComponent slot)`

把 `slot` 加入 `component.Slots`。未挂载节点立即加入；已挂载节点则以一步可撤销操作提交。已以同一引用注册过的插槽会被忽略（幂等保护）。

### GetWorldAnchor / GetWorldSize

**签名：** `static Anchor GetWorldAnchor(this INodeComponent component)`、`static Size GetWorldSize(this INodeComponent component)`

撤销 getter 的缩放坍缩，返回存储的世界值。`component` 为 null 时抛 `ArgumentNullException`。凡是要写回的读取都用这两个方法；`Anchor`/`Size` getter 返回坍缩副本。

### StandardSetAnchor

**签名：** `static void StandardSetAnchor(this INodeComponent component, Anchor anchor)`

写入世界锚点。通知由属性 setter 负责；标准实现在 `Anchor` 上触发 `PropertyChanged`。

### StandardSetLayer

**签名：** `static void StandardSetLayer(this INodeComponent component, int layer)`

保留世界位置，只替换 `Layer`。

### StandardSetSize

**签名：** `static void StandardSetSize(this INodeComponent component, Size size)`

触发 `Resizing(from, to)`；该句柄上的 `PreventDefault` 会阻止写入。否则写入尺寸并触发 `Resized(from, to, handle)`。

### StandardMove

**签名：** `static void StandardMove(this INodeComponent component, Offset offset)`

`offset` 是**视图空间**的拖拽增量。方法展开坍缩锚点，算出 `to = (view + offset) * scale`，以包含层的完整世界锚点触发 `Moving(from, to)`，未被阻止则写入，随后触发 `Moved`。

### StandardBroadcastAsync / StandardReverseBroadcastAsync

**签名：** `static Task StandardBroadcastAsync(this INodeComponent component, object? parameter, CancellationToken ct = default)`，反向方法同名。

遍历 `Targets`（正向）或 `Sources`（反向），为每条边构建 `TaskContext`，调用节点助手的 `AccessAsync`，并对每个被接受的接收端派发 `ReceiveCommand`。被拒绝的边按未连接跳过。取不到助手时抛 `ArgumentException`。

### SearchForwardNodes / SearchReverseNodes / SearchAllRelativeNodes

**签名：** `static IEnumerable<INodeComponent> SearchForwardNodes(this INodeComponent component, Func<INodeComponent, bool>? predicate = null, int maxDepth = 0)`，`SearchReverseNodes` 同形，另有 `SearchAllRelativeNodes`。

沿 `Targets`（正向）、`Sources`（反向）或双向做广度优先遍历。`maxDepth = 0` 表示不限。起点不计入；`predicate` 过滤产出而不影响遍历。`SearchAllRelativeNodes` 在两个方向间共享一个已访问集。

### StandardDelete

**签名：** `static void StandardDelete(this INodeComponent component)`

触发 `Deleting()`；`PreventDefault` 会保留节点。否则收集两端都属于同一棵树的全部连线，并提交一个对：redo 移除连线、清空插槽父节点并移除节点，undo 全部恢复。未挂载节点调用 `WorkflowGuard.Fail`。

## WorkflowSlotEx

### GetStandardCommands

**签名：** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this ISlotComponent component)`

返回 `SendConnectionCommand`、`ReceiveConnectionCommand`、`DeleteCommand`。

### StandardSetChannel

**签名：** `static void StandardSetChannel(this ISlotComponent component, SlotChannel channel)`

触发 `ChannelChanging(from, to)`；`PreventDefault` 保留旧通道。否则删除新通道不允许的连线，写入通道，再触发 `ChannelChanged`。未挂载到树的插槽调用 `WorkflowGuard.Fail`。

### StandardUpdateState

**签名：** `static void StandardUpdateState(this ISlotComponent component)`

由 `Targets`/`Sources` 重算 `State`：`Sender`、`Receiver`、`Sender | Receiver` 或 `StandBy`。两个预览位（`PreviewSender`、`PreviewReceiver`）被保留，因为它们属于进行中的拖拽。

### StandardSendConnection / StandardReceiveConnection

**签名：** `static void StandardSendConnection(this ISlotComponent component)`、`static void StandardReceiveConnection(this ISlotComponent component)`

转发到所属树的助手。未挂载到树的插槽调用 `WorkflowGuard.Fail`。

### StandardDelete

**签名：** `static void StandardDelete(this ISlotComponent component)`

收集插槽的连线并提交一个对：redo 移除连线与插槽，undo 恢复。未挂载插槽调用 `WorkflowGuard.Fail`。

### StandardCanBeSender / StandardCanBeReceiver

**签名：** `static bool StandardCanBeSender(this ISlotComponent component)`、`static bool StandardCanBeReceiver(this ISlotComponent component)`

检查通道标志：可发送需要 `OneTarget`、`MultipleTargets`、`OneBoth` 或 `MultipleBoth`；可接收需要对应的 `...Source...` 项。

## WorkflowLinkEx

### GetStandardCommands

**签名：** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this ILinkComponent component)`

返回唯一的 `DeleteCommand`。

### StandardDelete

**签名：** `static void StandardDelete(this ILinkComponent component)`

提交一个对：redo 从 `Links`、`LinksMap`、发送端 `Targets` 与接收端 `Sources` 移除连线，undo 恢复；两种收尾都会重算插槽状态。发送端未挂载时调用 `WorkflowGuard.Fail`。

## 示例

```csharp
var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0), Size = new Size(220, 120) };
tree.GetHelper().CreateNode(node);

node.GetHelper().SetAnchor(new Anchor(100, 80, 0));
Console.WriteLine(node.GetWorldAnchor());          // Anchor(100,80,0)

var forward = node.SearchForwardNodes(maxDepth: 2).Select(n => n.GetType().Name);
Console.WriteLine(string.Join(",", forward));      // 叶节点为空

node.DeleteCommand.Execute(null);                  // 一项撤销
tree.GetHelper().Undo();
Console.WriteLine(tree.Nodes.Count);               // 1
```
