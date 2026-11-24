# 动作与命令

编辑以一对重做/撤销动作提交。树保存两个并发栈；组件命令只是构建这对动作并调用 `Submit` 的薄包装。

命名空间：`VeloxDev.WorkflowSystem`（`IActionPair`、`ActionPair`）与 `VeloxDev.WorkflowSystem.StandardEx`（`WorkflowCommandEx`）。

## IActionPair

**签名：** `interface IActionPair`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Redo` | `Action` | 应用改动。 |
| `Undo` | `Action` | 恢复先前状态。 |

## ActionPair

**签名：** `readonly struct ActionPair(Action redo, Action undo) : IActionPair`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ActionPair(Action redo, Action undo)` | 构造函数 | 保存两个委托。 |
| `Redo` / `Undo` | `Action` | 已保存的委托。 |

```csharp
var before = node.GetWorldAnchor();
var after = new Anchor(before.Horizontal + 40, before.Vertical, before.Layer);
tree.GetHelper().Submit(new ActionPair(
    () => node.Anchor = after,
    () => node.Anchor = before));
```

## 命令集

每个参数都是普通模型值，因此同一条命令同时服务手势、菜单项与智能体工具调用。

| 组件 | 命令 | 参数 | 撤销项 |
| --- | --- | --- | --- |
| `ITreeComponent` | `CreateNodeCommand` | `INodeComponent` | 一 |
| `ITreeComponent` | `SendConnectionCommand` | `ISlotComponent` | 拖拽时的清理（若有）一项 |
| `ITreeComponent` | `ReceiveConnectionCommand` | `ISlotComponent` | 新连线一项，外加清理 |
| `ITreeComponent` | `SubmitCommand` | `IActionPair` | 所提交的对 |
| `ITreeComponent` | `UndoCommand` / `RedoCommand` | 无 | 移动一项 |
| `ITreeComponent` | `SetPointerCommand` | `Anchor` | 无 |
| `ITreeComponent` | `ResetVirtualLinkCommand` | 无 | 无 |
| `INodeComponent` | `SetAnchorCommand` / `SetSizeCommand` | `Anchor` / `Size` | 无 |
| `INodeComponent` | `MoveCommand` | `Offset` | 无 |
| `INodeComponent` | `CreateSlotCommand` | `ISlotComponent` | 挂载时一 |
| `INodeComponent` | `DeleteCommand` | 无 | 一（节点、插槽与连线） |
| `INodeComponent` | `ReceiveCommand` | `ITaskContext?` | 无 |
| `INodeComponent` | `BroadcastCommand` / `ReverseBroadcastCommand` | `object?` | 无 |
| `ISlotComponent` | `SetChannelCommand` | `SlotChannel` | 无 |
| `ISlotComponent` | `SendConnectionCommand` / `ReceiveConnectionCommand` | 无 | 经树 |
| `ISlotComponent` | `DeleteCommand` | 无 | 一（插槽与连线） |
| `ILinkComponent` | `DeleteCommand` | 无 | 一 |

`SetChannelCommand` 刻意不写撤销项：通道决定插槽能持有多少连接，改变它可能拆掉既有连线，而那次拆除不是可编辑步骤。请在连线前设置通道。

宿主自己的控制器（`CompileCommand`、`RunCommand`、`StopCommand` 等）由其视图模型上的 `[VeloxCommand]` 方法生成，而不是由工作流模型生成；见 [MVVM 视图模型生成](../../../1_快速开始/11_MVVM视图模型生成/index.md)。

## WorkflowCommandEx

**签名：** `static class WorkflowCommandEx` —— 针对命令集合的生命周期操作。

| 方法 | 返回 | 说明 |
| --- | --- | --- |
| `StandardClosing(this IReadOnlyCollection<IVeloxCommand>)` | `void` | 对每条命令调用 `Lock()`。 |
| `StandardClosingAsync(...)` | `Task` | 逐条 `await LockAsync()`。 |
| `StandardClose(...)` | `void` | 对每条命令调用 `Clear()`。 |
| `StandardCloseAsync(...)` | `Task` | 逐条 `await ClearAsync()`。 |
| `StandardClosed(...)` | `void` | 对每条命令调用 `Unlock()`。 |
| `StandardClosedAsync(...)` | `Task` | 逐条 `await UnlockAsync()`。 |

助手的 `Closing` / `CloseAsync` / `Closed` 使用的就是这些；它们不用于逐次编辑。

## 历史语义

- `StandardSubmit(pair)` 立即调用 `pair.Redo` 并把对压入撤销栈；抛异常的动作会被记录且不入栈。
- `StandardUndo` 弹出撤销栈、调用 `Undo` 并压入重做栈；`StandardRedo` 与之镜像。
- 两个栈每树一份，存于 `ConditionalWeakTable`，因此被回收的树会释放其历史。
- 历史是每个逻辑操作一项，而不是每次内部集合变动的日志：带连线的节点删除是一项，已挂载节点创建插槽也是一项。

## 示例

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0) };
var b = new NodeDefaultViewModel { Anchor = new Anchor(420, 80, 0) };
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

tree.GetHelper().Undo();
Console.WriteLine(tree.Nodes.Count);   // 1
tree.GetHelper().Redo();
Console.WriteLine(tree.Nodes.Count);   // 2

tree.GetHelper().ClearHistory();       // 两个栈都清空
```
