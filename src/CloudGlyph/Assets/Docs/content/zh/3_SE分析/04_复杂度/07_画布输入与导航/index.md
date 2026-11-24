# 画布输入与导航

输入路由是常数时间：指针事件最多经过三个助手（插槽、节点、树）冒泡。代价在命中选择。连线命中没有空间索引——它遍历已实现的可见项，把每条连线与 128 段折线比较，命中后再重扫可见项检查节点遮挡。插槽命中则遍历整个模型。

记号：已实现连线 $L$，曲线采样 $S$（默认 128），可见节点 $N$，树中插槽总数 $P$。

## 代价模型

| 操作 | 时间 | 出处 |
|---|---|---|
| 路由一次指针事件 | $O(1)$——链长至多 3 | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:267` |
| 向处理器冒泡 | $O(1)$ 个助手，订阅者代价 | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:324` |
| 构建连线曲线 | 时间与内存 $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:286` |
| 曲线包含判定 | $O(1)$ 包围盒剔除，随后最坏 $O(S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:318` |
| 按弧长取点 | $O(\log S)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:342` |
| 连线命中，全部可见 | 最坏 $O(L S + L N)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkHitTestEx.cs:76` |
| 插槽命中 | $O(P)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/SlotHitTestEx.cs:29` |
| 滚轮滚动 / 居中 | $O(1)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Surface/SurfaceScrollerCore.cs:49` |
| 负坐标覆盖扫描 | $O(n)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs:454` |

## 路由是一条三步链

`Chain` 依次产出插槽助手、所属节点助手、树助手；`Bubble` 在某处理器设置 `StopPropagation` 时停止：

```csharp
foreach (var helper in Chain(e.Target))
{
    if (helper is not IInputEvents events) continue;
    events.Input.Raise(e);
    if (e.Handle.StopPropagation) break;
}
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Events/WorkflowInput.cs:324-331`

链固定不超过三项，所以无论图多大，路由都是 $O(1)$。

## 连线命中是昂贵路径

命中检测从最上层可见连线往下扫，对每条曲线采样，再检查是否有节点覆盖命中点：

```csharp
for (var i = items.Count - 1; i >= 0; i--)
{
    if (items[i] is not ILinkComponent link) continue;
    if (!link.HitTest(x, y, radius)) continue;
    if (IsCoveredByANode(items, link, x, y, radius)) continue;
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkHitTestEx.cs:83-88`

`HitTest` 本身先做包围盒剔除，再遍历采样：

```csharp
for (var i = 1; i < _xs.Length; i++)
    if (DistanceToSegment(x, y, _xs[i - 1], _ys[i - 1], _xs[i], _ys[i]) <= radius)
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Interaction/LinkCurve.cs:327-329`

遮挡检查又是对同一可见列表的线性扫描，所以每次指针移动的最坏代价为：

$$
T_{\text{hit}} = O(L\,S + L\,N)
$$

```plot
{
  "title": "每次指针移动的连线命中",
  "grid": true,
  "xAxis": { "domain": [0, 40] },
  "yAxis": { "domain": [0, 5200] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "O(L)，每条一次比较" },
    { "fn": "128*x", "color": "#f472b6", "title": "O(L*S)，每条 128 个采样" }
  ]
}
```

由于 $L$ 是虚拟化给出的*已实现*连线数，实际代价随视口而非文档规模伸缩。不过在稠密视口中，它仍是一次带 128 采样常数的逐移动线性扫描。

## 曲线、滚动与其余部分

`PointAtLength` 用预计算的累计长度数组与二分查找，所以沿曲线取位置是 $O(\log S)$——输入路径中唯一的对数操作。滚轮滚动与居中是当前布局上的算术，$O(1)$，至多触发一次画布扩展。负坐标覆盖扫描会遍历每个节点以扩展画布，$O(n)$，但只在布局要求时执行。

## 内存

`WorkflowInput` 每棵树持有固定几个字段，通过 `ConditionalWeakTable` 惰性创建。一条曲线拥有三个长度 $S$ 的 `double[]` 以及长度与包围盒——每条曲线 $O(S)$，按引用发布，因此命中路径每次移动不分配。适配器侧拖拽处理器每次鼠标移动发出一个 `MoveCommand`；下游重建索引与虚拟化的代价属于视图托管，不属于输入。
