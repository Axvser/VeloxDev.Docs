# Enable virtualization

Virtualization is a property of the helper, not of the tree. A helper built with a cell size installs a spatial map and maintains the visible set; a helper built with the parameterless constructor renders everything and never updates `VisibleItems`.

## Pick the helper

```csharp
using VeloxDev.WorkflowSystem;

// Virtualization off. VisibleItems stays empty.
public sealed class PlainHelper : TreeHelper { }

// Virtualization on. The cell size is the spatial grid's cell, in canvas units.
internal sealed class VirtualizeHelper : TreeHelper
{
    public VirtualizeHelper() : base(200) { }
}
```

The generator picks the helper through the tree attribute:

```csharp
[WorkflowBuilder.Tree<VirtualizeHelper>]
internal partial class TreeViewModel
{
    public TreeViewModel() => InitializeWorkflow();
}
```

`TreeHelper(double)` also starts the `TreeHelper` tick channel at 10 fps if it is not already running. The tick only checks a dirty flag; it does no visible-set work on its own thread.

## What the visible set contains

`Helper.VisibleItems` is an `ObservableCollection<IWorkflowComponent>` maintained by `WorkflowSpatialEx.VirtualizeCore`. It contains:

- the tree's `VirtualLink` (always, so the drag preview has a view),
- every node the spatial query returns,
- every link whose two endpoint nodes are both in the query.

The query is the current `Viewport` expanded by one graph layer (`expansionDepth: 1`), so a node just outside the viewport is still included when a link needs to cross into it. The result is not a list of node views; links are items too.

## What moves the viewport

`WorkflowInput` is not involved here. The surface behavior measures the `ScrollViewer` and calls `SurfaceMetricsPush.PushViewport`, which writes `tree.GetHelper().Viewport` and persists `tree.Layout.ViewportOffset`. Assigning a new `Viewport` runs `Virtualize` synchronously on the calling thread.

```csharp
tree.GetHelper().Viewport = new Viewport(localX, localY, viewportWidth, viewportHeight);
```

Node geometry changes do **not** mark the visible set dirty. Dragging a node repaints its card, but the visible set waits for the next scroll, zoom or explicit `MarkDirty()`. During a drag, recomputing the query every frame costs more than a visible set one frame late.

## Marking dirty

`MarkDirty()` requests one pass on the tick channel. The pass is merged: many calls before the next tick cost one `Virtualize` plus one `BroadcastVisibleItemLayout`, which re-raises `Anchor` and `Size` for visible nodes so bound views refresh.

```csharp
tree.GetHelper().MarkDirty();
```

## The thread rule

`VisibleItems` is bound to UI, and the pool removes from it synchronously. The tick thread must not touch it. The helper captures `SynchronizationContext.Current` when installed and posts the pass back to that context; a helper installed off the UI thread must be given the context explicitly:

```csharp
var helper = new TreeHelper(200).WithSynchronizationContext(uiContext);
```

Passing `null` is an explicit "run inline on the tick thread" and is the correct choice for a service, a console host or a headless test. Every `Install` re-captures the context unless it was set explicitly, so moving a helper to another UI thread rebinds it.

## Before querying, the index must be complete

`SpatialGridHashMap.Query` runs `EnsureIndexed()` first: it flushes a deferred resync and re-reads bounds for entries that were registered while empty. An item measured after registration is therefore found by the next query. Skipping this makes such an item invisible permanently — moving the viewport cannot recover it.

## Expected result

- With eight nodes spread across a world larger than the viewport, `Helper.VisibleItems.Count` is smaller than `tree.Nodes.Count`.
- Scrolling brings new nodes into the set and removes the ones that left.
- A node dragged just outside the viewport keeps its card until the next scroll; then it is removed.
- With the parameterless `TreeHelper`, `VisibleItems.Count` stays 0 and every node must be bound directly.

## Next

[Host views](../02_host-views/index.md) turns this visible set into views.
