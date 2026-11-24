# 工作流图模型

图模型由四组协作的集合构成：树上的 `Nodes` 与 `Links`、每个节点上的 `Slots`，以及一张以发送方插槽和接收方插槽为键的两级 `LinksMap`。下面几乎所有代价都来自同一个事实：这些集合是 `ObservableCollection<T>`（底层为 `List<T>`），所以按下标访问和 `Add` 是常数时间，而 `Contains` 与 `Remove` 是线性扫描。`LinksMap` 是模型中唯一的哈希索引。

记号：$N$ 个节点，每个节点 $S$ 个插槽，单个插槽的度为 $d$，树中有 $L$ 条连线，$V$ 与 $E$ 表示可达子图的节点与插槽边。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| `StandardCreateNode`，独立节点 | 均摊 $O(1)$ | $O(1)$ + $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:28` |
| `StandardCreateNode`，重新挂载 | $O(S d + N)$ | — | 首次会从旧树删除 |
| `StandardCreateSlot` | 每次 $O(S)$，构建一个节点 $O(S^2)$ | $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:24` |
| 删除节点 | $O(S d + N)$ | 临时 $O(S d)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:295` |
| 添加 / 删除连线 | $O(1) + O(d) + O(L)$ | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowLinkEx.cs:17` |
| 单节点入度 / 出度 | $O(S)$ | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:592` |
| 查找入口 / 出口节点 | $O(N S)$ | $O(N)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:625` |
| 正向 / 反向 BFS | $O(V + E)$ | $O(V)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:227` |
| 按端点查找连线 | $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowLinkEx.cs:42` |
| 按下标查找节点 | $O(1)$ | — | `Nodes` 为列表，支持下标 |
| 按 `RuntimeId` 查找节点 | $O(N)$ — *推断* | — | Core 中没有该索引 |
| 空间查询（虚拟化树） | $O(C + H)$ | $O(C)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:98` |

`LinksMap` 的探测让连线操作尽量保持常数时间：

```csharp
if (tree.LinksMap.TryGetValue(sender, out var receivers))
{
    receivers.Remove(receiver);
    if (receivers.Count == 0) tree.LinksMap.Remove(sender);
}
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowLinkEx.cs:42-45`

## 连线为什么不是纯常数

映射项本身是常数，但同一条连线还出现在发送方的 `Targets`、接收方的 `Sources` 以及树的 `Links` 中。从这些列表移除要经过线性的 `Contains` / `Remove`：

$$
T_{\text{link}} = O(1) + O(d) + O(L)
$$

节点度是对其邻接表求和，因此是 $O(S)$ 而不是 $O(1)$：

```csharp
foreach (var slot in node.Slots)
    degree += slot.Sources.Count;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs:600-601`

## 遍历是模型中唯一渐近高效的环节

广度优先遍历用 `HashSet` 标记已访问节点，每个节点和每条邻接记录只检查一次，因此得到标准上界：

$$
T_{\text{BFS}}(V,E) = O(V + E)
$$

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs:275-281`

实际中最关键的对比是按容器查找：两级映射是常数，而所有基于列表的操作都是线性：

```plot
{
  "title": "按容器划分的查找代价",
  "grid": true,
  "xAxis": { "domain": [0, 50] },
  "yAxis": { "domain": [0, 500] },
  "data": [
    { "fn": "1", "color": "#4a9eff", "title": "LinksMap、下标、度" },
    { "fn": "x", "color": "#a78bfa", "title": "列表的 Contains / Remove" },
    { "fn": "x*log(x+1)", "color": "#e5c07b", "title": "有序操作，用于对比" }
  ]
}
```

## 内存

每个节点保存对象本身加上每个插槽一个引用；每个插槽保存每条关联连线一个引用；每条连线保存四个引用（映射项、发送方 `Targets`、接收方 `Sources`、树的 `Links`）。总计 $O(N + S + E + L)$，除这四处引用外没有复制。此外每棵树无条件分配一条虚拟连线和两个占位插槽，即每棵树恒定的三个对象。
