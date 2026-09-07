# Workflow System — 设计模式 — 虚拟代理

`WorkflowSpatialEx.Virtualize` 按需从空间哈希映射计算可见集（对完整节点/连接集合而言是一个“虚拟代理”）：查询相交的节点对边界并做一层连接扩展、加入单独可见的节点、就地调和 `VisibleItems`。可重入由每树标志守卫，因此 `CollectionChanged → Viewport 变化` 的级联以 O(1) 退出：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`，第 99-117 行

```csharp
public static void Virtualize(this IWorkflowTreeViewModel tree, Viewport viewport)
{
    if (viewport.Width <= 0 || viewport.Height <= 0)
        return;

    // Re-entrancy guard: suppress nested Virtualize calls that arise when
    // updating VisibleItems fires CollectionChanged → event handler → Viewport change
    // → another Virtualize.  The outermost call already reaches the correct final state.
    if (!Virtualizing.TryAdd(tree, 0))
        return;
    try
    {
        VirtualizeCore(tree, viewport);
    }
    finally
    {
        Virtualizing.TryRemove(tree, out _);
    }
}
```

`VirtualizeCore`（第 119-192 行）先按 `SetVirtualizeInset` 的可选内边距膨胀查询窗口，然后执行 `manager.QueryAgentBounds(query, expansionDepth: 1)` 加 `manager.QueryNodes(query)`，构建期望条目集（`tree.VirtualLink` + 可见节点 + 解析出的连接），最后一遍剔除陈旧条目、补齐缺失条目。调用方永远看不到完整集合：`TreeHelper<T>` 以 10 fps MonoBehaviour `Update` 在树脏时调用 `Component.Virtualize(Viewport)`，`Viewport` 属性变化也直接触发（`TreeHelper.cs` 第 56-64、96-100 行）。
