# Workflow System — Design Patterns — Virtual Proxy

`WorkflowSpatialEx.Virtualize` computes the visible set on demand from the spatial hash map (a "virtual proxy" for the full node/link collection): it queries intersecting node-pair bounds with one depth of connection expansion, adds individually visible nodes, and reconciles `VisibleItems` in place. Re-entrancy is guarded by a per-tree flag so a `CollectionChanged → Viewport change` cascade bails in O(1):

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowSpatialEx.cs`, lines 99-117

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

`VirtualizeCore` (lines 119-192) performs `manager.QueryAgentBounds(query, expansionDepth: 1)` plus `manager.QueryNodes(query)`, builds the desired item set (VirtualLink + visible nodes + their resolved links), then removes stale items and adds missing ones in one pass. Callers never see the full collection: `TreeHelper<T>` raises a 10 fps MonoBehaviour `Update` that calls `Component.Virtualize(Viewport)` while the tree is dirty, and the `Viewport` setter calls it directly when the viewport changes.
