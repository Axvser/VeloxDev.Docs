# Surface and Input

The surface is not a collection of per-platform gestures. It is a small set of Core objects: one input route, two scroll capability interfaces, the metrics/decorator/minimap data exchange, and a view-pool composition. An adapter implements the interfaces; a host calls the route and the capabilities.

## The input route

`WorkflowInput` has one instance per tree. An adapter creates exactly one argument object per action and calls `Route`; the route delivers it to the target, then its ancestors, then the tree. Every subscriber sees the same argument and the same `WorkflowEventHandle`.

```csharp
var input = WorkflowInput.For(tree);          // one instance per tree
input.Route(pointerArgs);                     // adapter, once per action
input.Route(keyArgs);                         // keys bubble; Core has no default key action

if (tree.GetHelper() is IInputEvents events)  // how a component subscribes
{
    events.Input.PointerEntered += (_, e) => Console.WriteLine(e.Target?.GetType().Name);
}
```

| Member | Meaning |
| --- | --- |
| `PointerTarget` / `HoveredLink` | the component or link the pointer is on; `null` over empty canvas |
| `ConnectionSender` / `PreviewReceiver` / `PreviewState` / `PreviewCheck` | the live connection preview |
| `PreviewChanged` / `PreviewValidating` | a preview snapshot, and a chance to refuse a candidate for this drag only |
| `HitRadius` | reach for link hit-testing; `LinkHitTestEx.DefaultHitRadius` (6) by default |
| `IsSuspended` | pauses hover bookkeeping while a popup is open |
| `Scroller` / `Navigator` | capabilities the adapter registers while attached; both nullable |

**Expected result:** a handler on the tree's `Input.KeyDown` hears a key wherever the pointer is, because the tree is the last element of every route.

## Scroll and navigation capabilities

The adapter owns the platform's wheel and registers two interfaces on the route while attached.

```csharp
// IWorkflowSurfaceScroller
input.Scroller?.ScrollBy(deltaX, deltaY);

// IWorkflowSurfaceNavigator
input.Navigator?.CenterOn(localX, localY);
```

`ScrollBy` takes **wheel deltas**, not scroll offsets. Positive X moves towards the content on the right; positive Y moves towards the content above. A zero delta leaves that axis alone. `CenterOn` takes a canvas-local point and puts it at the viewport centre; Core's `WorkflowNavigationEx` produces that point from a component:

```csharp
using VeloxDev.WorkflowSystem.StandardEx;

node.Locate();   // the node rectangle's center
slot.Locate();   // the parent node's center
link.Locate();   // the midpoint of the two endpoint nodes' centers
```

`Locate()` reads model data only, so an unmeasured or off-screen element still reaches the centre. It pans; it never zooms.

**Expected result:** `Scroller` is non-null after the surface attaches and `null` again after it detaches; `ScrollBy(0, 0)` changes nothing.

## Grid, minimap and metrics

The surface pushes the same numbers into two Core interfaces each pass.

| Interface | Members the surface pushes |
| --- | --- |
| `IWorkflowGridDecorator` | `ScrollOffsetX`, `ScrollOffsetY`, `ContentOffsetX`, `ContentOffsetY`; reads `RulerBand` |
| `IWorkflowMinimapOverlay` | everything above, plus `ViewportWidth`, `ViewportHeight`, `WorkflowTree`, `IsMinimapVisible`, `AvailableRight/Top/Bottom`, `MinimapMargin` |

`RulerBand` is the one value that affects more than drawing: the surface forwards it to the virtualizer, so nodes under a floating ruler are not culled.

`SurfaceMetrics.Create` derives the available overlay corner from the surface size, ruler band and visible scrollbars. `SurfaceViewport` is the immutable snapshot of scroll/content offsets and viewport size; `SurfaceCanvas` is the computed canvas size passed to a content fragment.

**Expected result:** after a scroll, the decorator's `ScrollOffsetX` and the tree's `Viewport.Horizontal` move together.

## Viewport restore

`SurfaceViewportRestoreCore` owns the save/restore state machine. Capture the tree's saved viewport **before** the surface writes its own first viewport, then schedule one deferred restore:

```csharp
var restore = new SurfaceViewportRestoreCore();
restore.Capture(tree);                 // reads Layout.ViewportOffset once per tree
restore.Schedule(host);                // host defers and applies; one restore per tree
```

Capture is keyed on the tree instance, so repeated refreshes never move the user back. If the adapter is not ready, the pending position stays and the next surface pass retries.

**Expected result:** a tree with a non-zero `Layout.ViewportOffset` opens at that offset; a tree without one stays at the origin.

## The view pool composition

An adapter closes `ViewSourcePipelineCore` once and exposes the short type its users see. The Core type takes nine type arguments — host, view, item, priority, factory, container, arranger, scheduler, diagnostics — and constructs the pool from them.

```csharp
public sealed class ViewPool : INotifyCollectionChangedSource
{
    // The adapter's composition point; users only set ItemsSource and TemplateSelector.
}
```

The pool's bounds are policy, not platform code:

| `IViewPoolPolicy` member | Meaning |
| --- | --- |
| `BatchSize` | maximum views one materialization batch may create |
| `FrameBudgetMilliseconds` | wall-clock budget for one batch; zero or negative means no limit |
| `MaxRecycledViewsPerType` | recycled views kept per runtime type; zero or negative means unlimited |

`AdaptiveViewPoolPolicy()` starts at 64 views and an 8 ms budget, then tunes from measured throughput. It is the default on every adapter that uses the pool.

**Expected result:** the pool creates one view per visible item, recycles by runtime type, and leaves a deactivated view on the panel with `Visibility.Collapsed` rather than removing it.
