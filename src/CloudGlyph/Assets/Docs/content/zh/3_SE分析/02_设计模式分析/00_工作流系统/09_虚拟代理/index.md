# Workflow System — 设计模式 — 虚拟代理

`WorkflowSpatialEx.Virtualize` 查询空间映射并原地调整 `VisibleItems`，使 UI 只渲染与视口相交的项目（外加一层的连接）。可重入由每个树的标志守卫：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSpatialEx.cs`，第 93-111 行

```csharp
public static void Virtualize(this IWorkflowTreeViewModel tree, Viewport viewport)
{
    if (viewport.Width <= 0 || viewport.Height <= 0) return;
    if (!Virtualizing.TryAdd(tree, 0)) return;
    try { VirtualizeCore(tree, viewport); }
    finally { Virtualizing.TryRemove(tree, out _); }
}
```
