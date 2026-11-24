# 树操作

`WorkflowTreeEx` 包含树的标准操作：命令束、节点创建、临时连线指针、撤销历史与度/拓扑查询。

命名空间：`VeloxDev.WorkflowSystem.StandardEx`。

## GetStandardCommands

**签名：** `static IReadOnlyCollection<IVeloxCommand> GetStandardCommands(this ITreeComponent component)`

按此顺序返回树助手驱动的八条命令：`CreateNodeCommand`、`SetPointerCommand`、`ResetVirtualLinkCommand`、`SendConnectionCommand`、`ReceiveConnectionCommand`、`SubmitCommand`、`RedoCommand`、`UndoCommand`。

**返回：** `IReadOnlyCollection<IVeloxCommand>` —— 供 `Closing`/`CloseAsync`/`Closed` 使用的命令束。

## StandardCreateNode

**签名：** `static void StandardCreateNode(this ITreeComponent component, INodeComponent node)`

先把 `node` 从原树分离（若有），再提交一个 `ActionPair`：redo 设置 `node.Parent = component` 并加入 `Nodes`；undo 移除它并恢复原父节点。

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `component` | `ITreeComponent` | 目标树。 |
| `node` | `INodeComponent` | 要加入的节点；它可能已属于另一棵树。 |

**返回：** `void`。重复创建没有保护：同一节点加入两次会产生两个撤销项与两个集合项。

## StandardSetPointer

**签名：** `static void StandardSetPointer(this ITreeComponent component, Anchor anchor)`

把临时连线的接收端移到 `anchor`，保留发送端的层。`VirtualLink` 没有发送端或接收端时，调用无操作。

## StandardCloseAsync

**签名：** `static Task StandardCloseAsync(this ITreeComponent component)`

对树及每个节点、插槽、连线执行三段式关闭：`Closing()`（锁定命令）、`CloseAsync()`（排空）、`Closed()`（解锁）。逐个 `await` 每个助手。

**返回：** `Task` —— 所有助手关闭后完成。

## StandardSubmit

**签名：** `static void StandardSubmit(this ITreeComponent component, IActionPair actionPair)`

调用 `actionPair.Redo` 并把对压入撤销栈。`Redo` 抛出的异常写入 `Debug`，该对不入栈。

## StandardUndo / StandardRedo

**签名：** `static void StandardUndo(this ITreeComponent component)`、`static void StandardRedo(this ITreeComponent component)`

从对应栈弹出一个对、调用它并压入相反栈。异常被记录，该对不转移。

## StandardClearHistory

**签名：** `static void StandardClearHistory(this ITreeComponent component)`

清空撤销栈与重做栈，不触碰模型。

## 度与拓扑查询

六个方法对 null 树都抛 `ArgumentNullException`；两个按索引的方法还会在索引超出 `Nodes` 时抛 `ArgumentOutOfRangeException`。

| 方法 | 返回 | 说明 |
| --- | --- | --- |
| `GetNodeInDegree(this ITreeComponent tree, int nodeIndex)` | `int` | 节点所有插槽的 `Sources.Count` 之和。 |
| `GetNodeOutDegree(this ITreeComponent tree, int nodeIndex)` | `int` | 节点所有插槽的 `Targets.Count` 之和。 |
| `FindEntryNodeIndices(this ITreeComponent tree)` | `IReadOnlyList<int>` | 入度为 `0` 的索引。 |
| `FindExitNodeIndices(this ITreeComponent tree)` | `IReadOnlyList<int>` | 出度为 `0` 的索引。 |
| `FindNodesByInDegree(this ITreeComponent tree, int degree)` | `IReadOnlyList<int>` | 入度等于 `degree` 的索引。 |
| `FindNodesByOutDegree(this ITreeComponent tree, int degree)` | `IReadOnlyList<int>` | 出度等于 `degree` 的索引。 |

## 示例

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel { Anchor = new Anchor(0, 0, 0) };
var b = new NodeDefaultViewModel { Anchor = new Anchor(300, 0, 0) };
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

Console.WriteLine($"entries={string.Join(",", tree.FindEntryNodeIndices())}");
Console.WriteLine($"exits={string.Join(",", tree.FindExitNodeIndices())}");

tree.GetHelper().Undo();
Console.WriteLine($"after undo nodes={tree.Nodes.Count}");
```
