# 平台适配器契约

每个 GUI 闭包的这套契约，是围绕两个索引结构的一组常数时间转换。输入路由被一条写死的、至多三级的辅助链所界；虚拟化是空间哈希加视图池；视口恢复是一次延迟写入。这一层几乎一切都是 $O(1)$，例外是空间索引与视图池的集合重扫。下列界均从所引用的控制流读出；若集合的哈希或比较代价取决于条目自身提供的成员，该界为期望情况。

## 代价模型

| 符号 | 含义 |
|---|---|
| $n$ | 节点数 |
| $l$ | 连线数 |
| $v$ | 可见条目数 |
| $g$ | 查询视口覆盖的网格单元数 |
| $c_i$ | 条目 $i$ 的包围盒覆盖的单元数 |
| $s$ | 单元尺寸 |
| $P$ | 单次查询触及的节点对/节点数 |
| $H$ | 事件订阅者数 |
| $d$ | 输入链深度（$\le 3$） |

## 输入路由

`WorkflowInput.Route` 在指针目标变化时先合成退出/进入事件，然后沿固定链冒泡：插槽辅助器、所属节点辅助器、树辅助器；节点或连线辅助器再到树辅助器（`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:299-317`、`:358-378`）。

```csharp
private IEnumerable<IWorkflowHelper> Chain(IWorkflowComponent? target)
{
    switch (target)
    {
        case ISlotComponent slot:
            yield return slot.GetHelper();
            if (slot.Parent is { } owner) yield return owner.GetHelper();
            break;

        case INodeComponent node:
            yield return node.GetHelper();
            break;

        case ILinkComponent link:
            yield return link.GetHelper();
            break;
    }

    // 空白画布（target 为 null）与树本身也落到这里：链上只剩树一级。
    yield return tree.GetHelper();
}
```

单个事件的代价是

$$
T_{\text{route}} = O(d \cdot (1 + H_d)), \qquad d \le 3
$$

因此路由与图规模无关。目标变化会多两次冒泡并分配两个事件对象。滚动、导航以及网格/小地图契约都是单次适配器调用或属性包。

## 空间索引

`SpatialGridHashMap` 保存 `Dictionary<CellKey, HashSet<T>>`、一张被跟踪条目表和一个未索引集合（`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/SpatialGridHashMap.cs:14-25`）。`CellKey` 用 `HashCode.Combine` 哈希两个整数（`CellKey.cs:4-16`）。插入会把条目加入其包围盒覆盖的每个单元；包围盒为空的条目先搁置，等测量完成后再索引（`SpatialGridHashMap.cs:67-81`、`:147-151`、`:342-348`）。

$$
c_i = \left(\left\lceil \frac{w_i}{s} \right\rceil + 1\right)\left(\left\lceil \frac{h_i}{s} \right\rceil + 1\right)
$$

$$
T_{\text{insert}} = O(c_i) \text{（期望）}, \qquad S_{\text{grid}} = O\left(\sum_i c_i\right)
$$

一条长连线的包围盒可能覆盖巨大矩形，而代码没有单条目单元数上限。单元数随面积除以 $s^2$ 增长；单元尺寸越小，范围上的代价越是二次的。

```plot
{
  "title": "单个条目覆盖的单元数（单元尺寸 1、10、50）",
  "grid": true,
  "xAxis": { "domain": [0, 100] },
  "yAxis": { "domain": [0, 12000] },
  "data": [
    { "fn": "(x/1+1)^2", "color": "#f472b6", "title": "s = 1" },
    { "fn": "(x/10+1)^2", "color": "#a78bfa", "title": "s = 10" },
    { "fn": "(x/50+1)^2", "color": "#4a9eff", "title": "s = 50" }
  ]
}
```

查询枚举查询矩形内的单元，用共享临时集合去重，再做点或相交可见性判断（`SpatialGridHashMap.cs:111-125`）。

$$
T_{\text{query}} = O(g + k + U \cdot c)
$$

其中 $U$ 是尚未索引的条目数。由于 `Query` 是迭代器，`EnsureIndexed` 在第一次 `MoveNext` 时才运行：它最多执行四次完整 `ResyncGrid`，并重新检查所有未索引条目（`:250-256`）。一次完整重同步是 $O(n \cdot c)$，在重入的包围盒级联之后运行一次（`:158-237`）。

`WorkflowSpatialManager` 增加一张节点到节点对的反向索引，并在其上做有界 BFS 扩展（`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs:80-125`）。

$$
T_{\text{agent-query}} = O(P)
$$

视口较小时与全图规模无关。`RetryPendingLinks` 在每次节点加入时扫描待定集合，遇到不利的加入顺序可能累计 $O(n \cdot l)$。

## 视图池

`ViewPoolCore` 为每个运行时类型保留一条空闲视图队列，维护活动视图的引用映射，以及带去重集合的待处理队列（`Src/Core/VeloxDev.Core/WorkflowSystem/ViewHosting/ViewPool.cs:34-47`）。`ProcessNextBatch` 按 `BatchSize` 或帧预算排空；`Materialize` 复用队列中的视图或调用工厂，并对不支持的类型做负缓存（`ViewPool.cs:274-317`、`:319-378`）。

```csharp
if (pools.TryGetValue(itemType, out var pool) && pool.Count > 0)
{
    view = pool.Dequeue();
    reusedViewCount++;
}

if (view is null)
{
    view = host.Factory.CreateView(typedItem);
    if (view is null)
    {
        unsupportedTypes.Add(itemType);
```

获取与回收平均 $O(1)$；实现 $v$ 个条目是 $O(v)$，分摊到 $\lceil v / \text{BatchSize} \rceil$ 个调度轮次。默认策略是 `BatchSize = 3`、无帧预算、每类型无限回收（`ViewHosting/ViewHostCore.cs:91-100`），所以偏向延迟，回收集合可能增长到曾物化过的所有条目。

`RenderLinks` 是例外：链接层启用时，每次集合通知都会重扫整个源以收集链接条目，增/删/替换/重置各 $O(i)$（`ViewPool.cs:159-162`、`:238-250`）。默认空链接层会跳过这一步。

## 表面数学与视口恢复

所有转换、钳制、居中与小地图辅助函数都是 $O(1)$（`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:31-32`、`:58-67`、`:254-314`）。`SurfaceMetrics.Create` 从表面尺寸、标尺带与滚动条常数时间推导边角（`GUI/Surface/SurfaceMetrics.cs:73-104`）。

`SurfaceViewportRestoreCore.Capture` 对每个树实例只记录一次待恢复偏移；`Schedule` 只延迟一次回调，重新检查标志、读取平台最大值、钳制并应用（`GUI/Surface/SurfaceViewportRestoreCore.cs:39-95`）。

$$
T_{\text{restore}} = O(1)
$$

唯一例外是 `EnsureNegativeCover`：缩放时它扫描每个节点以保持负画布被覆盖，每次缩放 $O(n)$（`WorkflowSurfaceMath.cs:454-497`）。

## 一致性测试包

`TestGraph.Create` 通过同步辅助器构造固定的三节点一连线图，并把一个节点放在远离画布处，只有滚动后的视口才看得到（`Src/Test/Headless/VeloxDev.AdapterTestKit/TestGraph.cs:56-87`）。它是 $O(1)$，自身不包含池或空间行为。

## 相关

- [WPF适配器](../25_WPF适配器/index.md) —— 本契约的一种具体闭包。
- [无头CLI](../23_无头CLI/index.md) —— 没有窗口时对同一契约的使用。
