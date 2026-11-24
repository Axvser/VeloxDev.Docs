# 工作流编辑与历史

每次编辑都表示为一个 `ActionPair`——redo 委托与 undo 委托——压入树助手缓存持有的两个 `ConcurrentStack` 之一。历史机制本身是常数时间；一次撤销的代价等于它重放的那个操作的代价，而不是查找它的代价。

记号：$K$ 条已记录操作，单次批量编辑 $k$ 条连线，$N$ 个节点，每节点 $S$ 个插槽，度 $d$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| `StandardSubmit` | $O(1)$ + redo 代价 | 每条操作 $O(1)$ 加捕获状态 | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:352` |
| `StandardUndo` | $O(1)$ + undo 代价 | — | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:367` |
| `StandardRedo` | $O(1)$ + redo 代价 | — | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:334` |
| `StandardClearHistory` | $O(1)$ | 释放 $O(K)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:385` |
| 一次批量编辑 $k$ 条连线 | $O(k)$ 入栈 + $O(k)$ 重放 | $O(k)$ 闭包 | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:544` |
| 撤销一次节点删除 | $O(N)$ | — | 先 `Nodes.Contains` 再 `Nodes.Add` |
| 历史内存 | — | $O(K)$ | 两个不设上限的栈 |

`ActionPair` 是含两个委托的 readonly 结构体，所以压入一条只分配一个栈节点：

```csharp
if (cache.RedoStack.TryPop(out var pair))
{
    try
    {
        pair.Redo.Invoke();
        cache.UndoStack.Push(pair);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:337-342`

## 真正决定上界的关系

撤销和重做并非"廉价"意义上的常数，而是"无需搜索"意义上的常数。被记录的操作是就地重放的：

$$
T_{\text{undo}} = O(1) + T_{\text{action}}
$$

对一条连线，它是 $O(1) + O(d) + O(L)$；对一次节点删除，它是 $O(N)$，因为重新加入要先查 `Nodes.Contains`。批量包装让一次多连线编辑只占一条历史记录：

```csharp
component.StandardSubmit(new ActionPair(
    () =>
    {
        foreach (var (_, _, link) in connectionsToRemove)
            WorkflowLinkEx.RemoveLinkFromTree(component, link);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:544-548`

## 历史没有深度上限

`StandardSubmit`、`StandardUndo` 与 `StandardRedo` 都没有深度上限。两个栈随每次提交增长，每个条目通过委托保活其捕获参数。因此内存随自上次清空以来的编辑数线性增长；捕获的状态——插槽、连线，以及在插槽枚举场景下整个 `SelectorState` 快照——是活对象保留，而不只是一个栈节点。

```plot
{
  "title": "历史内存随记录操作增长",
  "grid": true,
  "xAxis": { "domain": [0, 200] },
  "yAxis": { "domain": [0, 200] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(K) 个栈节点" },
    { "fn": "2*x", "color": "#f472b6", "title": "O(K)，含捕获状态" }
  ]
}
```

栈操作本身是 $O(1)$，因为 `ConcurrentStack` 是无锁链表；缓存放在 `ConditionalWeakTable` 中，随树一起回收，无需显式清理。
