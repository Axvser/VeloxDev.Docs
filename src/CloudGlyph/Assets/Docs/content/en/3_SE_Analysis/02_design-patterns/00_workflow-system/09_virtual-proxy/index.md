# Workflow System — Design Patterns — Virtual Proxy

`WorkflowSpatialEx.Virtualize` queries the spatial map and reconciles `VisibleItems` in-place, so the UI only renders what intersects the viewport (plus one depth of connected links). Re-entrancy is guarded by a per-tree flag:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSpatialEx.cs`, lines 93-111

```csharp
public static void Virtualize(this IWorkflowTreeViewModel tree, Viewport viewport)
{
    if (viewport.Width <= 0 || viewport.Height <= 0) return;
    if (!Virtualizing.TryAdd(tree, 0)) return;
    try { VirtualizeCore(tree, viewport); }
    finally { Virtualizing.TryRemove(tree, out _); }
}
```
