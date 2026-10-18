# 工作流系统 — 设计模式 — 虚拟代理

`WorkflowSpatialEx.Virtualize` 按需从空间哈希图计算可见集（对完整节点/连线集合的「虚拟代理」）：它查询相交的节点对边界并做一层连接扩展，加入单独可见的节点，然后就地调和 `VisibleItems`。重入由每棵树一个标志守卫，使 `CollectionChanged → Viewport change` 级联在 O(1) 内退出：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialEx.cs`，97-115 行

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

`VirtualizeCore`（117-190 行）执行 `manager.QueryAgentBounds(query, expansionDepth: 1)` 加 `manager.QueryNodes(query)`，构建期望条目集（VirtualLink + 可见节点 + 它们解析出的连线），然后一遍移除过期条目、加入缺失条目。调用方永远看不到完整集合：`TreeHelper<T>` 在树变脏时以 10 fps 的 Tickable `Update` 调用 `Component.Virtualize(Viewport)`，视口变化时 `Viewport` setter 直接调用它。
