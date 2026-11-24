# 视图托管与虚拟化

虚拟化每个视口只回答一个问题：哪些节点与节点对和它相交？空间网格用与覆盖单元数和单元内候选数成正比的时间回答，而不是与文档规模成正比。随后池为每个可见项物化一个视图，并按运行时类型回收。薄弱处在于查询之后的集合同步——它对可见集呈二次；以及网格的延迟重建索引——它对被跟踪项线性。

记号：与查询重叠的网格单元 $C$，这些单元中的候选项 $k$，可见项 $V$，被跟踪项 $n$，视图类型 $T$。

## 代价模型

| 操作 | 时间 | 空间 | 出处 |
|---|---|---|---|
| 网格插入 / 删除 | $O(\text{覆盖单元数})$ | $O(\text{单元数})$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:61` |
| 网格查询 | $O(C + k)$ | 暂存 $O(C + k)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:98` |
| 全量重建索引 | $O(n)$ | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:224` |
| 包围盒脏时计算 | $O(n)$ | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:28` |
| 带深度展开的节点对查询 | $O(C + k + \text{深度} \cdot \text{前沿} \cdot d)$ | $O(V)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs:80` |
| 虚拟化同步 | 最坏 $O(V^2)$ | $O(V)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs:95` |
| 池集合变更 | $O(\text{变更数})$ | $O(\text{活跃} + \text{回收})$ | `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:125` |
| 物化 / 回收 | 各 $O(1)$ | — | `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:319` |
| 自适应策略反馈 | 每批 $O(1)$ | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/AdaptiveViewPoolPolicy.cs:80` |

## 网格查询

单元成员是哈希桶，每个候选通过共享暂存集去重，再与精确视口做精度过滤：

```csharp
foreach (var cell in GetCells(viewport))
    if (_grid.TryGetValue(cell, out var set))
        ...
        if (!_queryScratch.Add(item)) continue;
        ...
            ? viewport.Contains(itemBounds.Horizontal, itemBounds.Vertical)
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:110-122`

上界是 $O(C + k)$ 而非 $O(n)$。但 $k$ 没有与分布无关的保证：缩得很小时许多节点共享一个单元，稠密单元会把 $k$ 推向 $n$。模板宿主的默认单元尺寸是 200 画布局部单位，在 `TreeHelper.cs:63` 设置并传给 `TreeHelper.cs:188` 的 `EnableMap`。

查询是基于实例级暂存集的迭代器，所以同一映射的两次枚举无法安全重叠。这是实现属性，不是文档化契约。

## 同步回可观察集合是二次的

可见列表是 `ObservableCollection`，同步时先线性 `Contains` 再添加缺失项，随后在 `while` 循环中同样调用 `Contains` 删除重复：

```csharp
private static void AddIfMissing(Collection<IWorkflowComponent> observable, IWorkflowComponent item)
{
    if (!observable.Contains(item))
        observable.Add(item);
}

private static void RemoveAll(Collection<IWorkflowComponent> observable, IWorkflowComponent item)
{
    while (observable.Contains(item))
        observable.Remove(item);
}
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs:355-377`

对每个期望项执行一次会使协调步骤最坏 $O(V^2)$，可能压过它前面的 $O(C + k)$ 查询。可见集通常只有几十项，常数很小——但这就是虚拟化一轮并非渐近线性的原因。

$$
T_{\text{virtualize}} = O(C + k) + O(V^2)
$$

```plot
{
  "title": "虚拟化：查询与集合同步",
  "grid": true,
  "xAxis": { "domain": [0, 120] },
  "yAxis": { "domain": [0, 14400] },
  "data": [
    { "fn": "2*x", "color": "#4a9eff", "title": "网格查询，O(C + k)" },
    { "fn": "x*x", "color": "#f472b6", "title": "同步，最坏 O(V^2)" }
  ]
}
```

## 池与可见性成正比，而非与文档成正比

一次集合变更对每个变更项花费一次哈希操作。物化时从按类型队列弹出或请求工厂；回收时压回，直到策略的每类型上限：

```csharp
while (processed < batchSize && pending.Count > 0)
{
    var item = pending.Dequeue();
    if (!pendingSet.Remove(item))
        continue;
    Materialize(item);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:290-299`

```csharp
if (pools.TryGetValue(itemType, out var pool) && pool.Count > 0)
    view = pool.Dequeue();
...
active[item] = view;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:338-366`

批次受 `BatchSize` 与帧时间预算限制，因此大视口跨多帧填充，而不是在一帧内完成。自适应策略每完成一批以常数时间根据测得吞吐更新批大小。

## 内存

网格为每个项在每个覆盖单元保存一个条目，外加被跟踪项字典，即 $O(\text{项} \times \text{跨越单元})$。池保存 $O(\text{活跃})$ 个视图，加上至多每类型回收上限；`MaxRecycledViewsPerType <= 0` 表示无限回收，用内存换更少的工厂调用。可见列表本身是 $O(V)$。
