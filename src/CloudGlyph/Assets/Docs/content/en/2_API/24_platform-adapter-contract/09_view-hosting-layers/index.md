# View hosting layers

The pool never touches a platform API directly. It asks one `IViewHost` for nine small layers; each adapter supplies its own implementations and exposes the closed composition. This page lists the contracts; the adapter pages list the concrete types.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## IViewHost

**Signature:** `interface IViewHost<THost, TView, TItem, TPriorityCore>` with `THost/TView/TItem : class`

| Member | Type | Description |
| --- | --- | --- |
| `Factory` | `IViewFactory<TItem, TView>` | Turns items into views. |
| `Container` | `IViewContainer<THost, TView, TItem>` | Owns visual-tree membership and bound state. |
| `Arranger` | `IViewArranger<TItem, TView>` | Applies item geometry. |
| `Scheduler` | `IViewScheduler<TPriorityCore>` | Carries batches to the host thread. |
| `Diagnostics` | `IViewDiagnostics<TItem>` | Reports failed view operations. |
| `PoolPolicy` | `IViewPoolPolicy` | Bounds batches and recycled views. |
| `LayerPolicy` | `IViewLayerPolicy<TItem>` | Decides z-order. |
| `LinkLayer` | `IViewLinkLayer<THost, TItem>` | Renders links itself when the platform does not use one view per link. |
| `MeasureHost` | `IViewMeasureHost<THost, TView, TItem>` | Optional post-arrange measure hook. |

## IViewFactory

**Signature:** `interface IViewFactory<TItem, TView>`

| Member | Signature | Description |
| --- | --- | --- |
| `WantsItem` | `bool WantsItem(TItem item)` | Whether this factory handles the item. |
| `CreateView` | `TView? CreateView(TItem item)` | Creates a view, or `null` when the item type is unsupported. |

## IViewContainer

**Signature:** `interface IViewContainer<THost, TView, TItem>`

| Member | Signature | Description |
| --- | --- | --- |
| `Attach` | `void Attach(THost host, TView view)` | Adds the view to the host. |
| `Detach` | `void Detach(THost host, TView view)` | Removes it. |
| `Activate` | `void Activate(TView view, TItem item)` | Binds item state. |
| `Deactivate` | `void Deactivate(TView view)` | Releases bound state. |
| `SetZOrder` | `void SetZOrder(TView view, int zIndex)` | Applies the layer order. |
| `Destroy` | `void Destroy(THost host, TView view)` | Destroys a view the pool refused to keep. |

## IViewArranger

**Signature:** `interface IViewArranger<TItem, TView>`

| Member | Signature | Description |
| --- | --- | --- |
| `Arrange` | `void Arrange(TView view, TItem item)` | Applies the item's geometry to the view. |

## IViewScheduler

**Signature:** `interface IViewScheduler<TPriorityCore>`

| Member | Signature | Description |
| --- | --- | --- |
| `BatchPriority` | `TPriorityCore` | The priority the pool uses for materialization batches. |
| `Schedule` | `bool Schedule(Action batch, TPriorityCore priority)` | Queues one batch; must not run it synchronously. Returns `false` when the dispatcher refused it. |

`TPriorityCore` is the platform's dispatcher-priority type, or `NonPriority` (`readonly struct`, `VeloxDev.Core.Threading`) where the platform has no priority concept.

## IViewDiagnostics

**Signature:** `interface IViewDiagnostics<TItem>`

| Member | Signature | Description |
| --- | --- | --- |
| `Failed` | `void Failed(TItem? item, ViewStage stage, Exception? exception)` | Reports a failed stage. |

## IViewLayerPolicy

**Signature:** `interface IViewLayerPolicy<TItem>`

| Member | Signature | Description |
| --- | --- | --- |
| `GetZOrder` | `int GetZOrder(TItem item)` | Z-order for one item. |

## IViewLinkLayer

**Signature:** `interface IViewLinkLayer<THost, TItem>`

| Member | Signature | Description |
| --- | --- | --- |
| `IsActive` | `bool` | Whether this layer handles any item at all; `false` lets the pool skip link rendering. |
| `Handles` | `bool Handles(TItem item)` | Whether this layer takes links away from the main pool. |
| `Render` | `void Render(THost host, IReadOnlyList<TItem> items)` | Draws the handled items; called whenever the visible set changes, including when it becomes empty. |

## IViewMeasureHost

**Signature:** `interface IViewMeasureHost<THost, TView, TItem>`

| Member | Signature | Description |
| --- | --- | --- |
| `Measure` | `void Measure(THost host, TView view, TItem item)` | Post-arrange measure hook. |

## ViewStage

**Signature:** `enum ViewStage`

| Members |
| --- |
| `Schedule`, `Link`, `Create`, `Activate`, `Attach`, `Arrange`, `Layer`, `Measure`, `Deactivate`, `Detach`, `Destroy` |

The enum names the pipeline layer that reported a failure, so one diagnostics sink can route all stages.

```csharp
sealed class Diagnostics : IViewDiagnostics<IWorkflowComponent>
{
    public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)
        => Console.WriteLine($"{stage}: {item?.GetType().Name}: {exception?.Message}");
}
```

**Expected result:** a selector that throws for an item type is reported once with `ViewStage.Create`; the pool skips that type on later batches.
