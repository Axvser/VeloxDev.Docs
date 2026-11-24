# View host contract

The pool does not know a platform. It composes nine narrow layers, each a separate interface, and an adapter supplies one implementation per layer. `IViewPoolPolicy` is documented with the [view pool](../00_view-pool/index.md).

## Layer interfaces

All signatures below are `VeloxDev.WorkflowSystem` and public.

### IViewFactory<TItem, TView>

```csharp
public interface IViewFactory<TItem, TView> where TItem : class where TView : class
{
    bool WantsItem(TItem item);
    TView? CreateView(TItem item);
}
```

`WantsItem` decides whether the pool should materialise the item at all (an overlay-drawn link can return `false`). `CreateView` returns `null` when no template matches; the pool caches that answer by runtime type until disposal.

### IViewContainer<THost, TView, TItem>

```csharp
public interface IViewContainer<THost, TView, TItem>
    where THost : class where TView : class where TItem : class
{
    void Attach(THost host, TView view);
    void Detach(THost host, TView view);
    void Activate(TView view, TItem item);
    void Deactivate(TView view);
    void SetZOrder(TView view, int zIndex);
    void Destroy(THost host, TView view);
}
```

| Method | Contract |
|---|---|
| `Attach` | Makes the view a child of the host; must be idempotent. |
| `Detach` | Hides or removes a recycled view; it may be handed back later. |
| `Activate` | Binds the item and makes the view visible. |
| `Deactivate` | Releases the previous item and hides the view without destroying it. |
| `SetZOrder` | Applies a z-order; a no-op on platforms without one. |
| `Destroy` | Permanently removes a view the policy refused to keep. |

### IViewArranger<TItem, TView>

```csharp
public interface IViewArranger<TItem, TView> where TItem : class where TView : class
{
    void Arrange(TView view, TItem item);
}
```

Applies the item's geometry to the view, after `Attach`, so an imperative platform may assume the view is already in the tree.

### IViewScheduler<TPriorityCore>

```csharp
public interface IViewScheduler<TPriorityCore>
{
    TPriorityCore BatchPriority { get; }
    bool Schedule(Action batch, TPriorityCore priority);
}
```

`Schedule` posts one batch to the host thread and must not invoke it synchronously. It returns `false` when refused; the pool retries on the next visible-set change.

### IViewDiagnostics<TItem>

```csharp
public interface IViewDiagnostics<TItem> where TItem : class
{
    void Failed(TItem? item, ViewStage stage, Exception? exception);
}
```

Reports a failed or refused operation. `item` is null when the failure is not item-specific; `exception` is null for a refusal without an exception. Must be cheap and must not throw.

### IViewLayerPolicy<TItem>

```csharp
public interface IViewLayerPolicy<TItem> where TItem : class
{
    int GetZOrder(TItem item);
}
```

### IViewLinkLayer<THost, TItem>

```csharp
public interface IViewLinkLayer<THost, TItem> where THost : class where TItem : class
{
    bool IsActive { get; }
    bool Handles(TItem item);
    void Render(THost host, IReadOnlyList<TItem> items);
}
```

When `IsActive` is false the pool owns links like any other item. When it is true and `Handles` returns true, the layer draws the item itself; `Render` is called on every visible-set change, including the empty set, and must not mutate the collection.

### IViewMeasureHost<THost, TView, TItem>

```csharp
public interface IViewMeasureHost<THost, TView, TItem>
    where THost : class where TView : class where TItem : class
{
    void Measure(THost host, TView view, TItem item);
}
```

An optional post-arrange measure hook; the pool does not wait for it. A no-op implementation is valid.

### IViewBatchFeedback

```csharp
public interface IViewBatchFeedback
{
    void OnBatchCompleted(int processed, long elapsedTicks, int pending);
}
```

Reports a completed batch on the host thread immediately after it runs; implementations must be cheap and allocation-free.

### IViewHost<THost, TView, TItem, TPriorityCore>

```csharp
public interface IViewHost<THost, TView, TItem, TPriorityCore>
    where THost : class where TView : class where TItem : class
{
    IViewFactory<TItem, TView> Factory { get; }
    IViewContainer<THost, TView, TItem> Container { get; }
    IViewArranger<TItem, TView> Arranger { get; }
    IViewScheduler<TPriorityCore> Scheduler { get; }
    IViewDiagnostics<TItem> Diagnostics { get; }
    IViewPoolPolicy PoolPolicy { get; }
    IViewLayerPolicy<TItem> LayerPolicy { get; }
    IViewLinkLayer<THost, TItem> LinkLayer { get; }
    IViewMeasureHost<THost, TView, TItem> MeasureHost { get; }
}
```

## ViewStage

```csharp
public enum ViewStage
{
    Schedule = 0, Link = 1, Create = 2, Activate = 3, Attach = 4,
    Arrange = 5, Layer = 6, Measure = 7, Deactivate = 8, Detach = 9, Destroy = 10
}
```

| Member | Failure it names |
|---|---|
| `Schedule` | The scheduler refused a batch. |
| `Link` | The link layer could not render. |
| `Create` | The factory could not create a view. |
| `Activate` | The container could not bind or show a view. |
| `Attach` | The container could not attach a view. |
| `Arrange` | The arranger could not apply geometry. |
| `Layer` | The layer policy could not apply a z-order. |
| `Measure` | The measure host could not measure. |
| `Deactivate` | The container could not release or hide. |
| `Detach` | The container could not detach. |
| `Destroy` | The container could not destroy. |

## ViewHostCore

```csharp
public abstract class ViewHostCore<THost, TView, TItem, TPriorityCore>
    : IViewHost<THost, TView, TItem, TPriorityCore>
    where THost : class where TView : class where TItem : class
```

| Signature / member | Description |
|---|---|
| `protected ViewHostCore(IViewFactory<TItem,TView> factory, IViewContainer<THost,TView,TItem> container, IViewArranger<TItem,TView> arranger, IViewScheduler<TPriorityCore> scheduler, IViewDiagnostics<TItem>? diagnostics = null, IViewPoolPolicy? poolPolicy = null, IViewLayerPolicy<TItem>? layerPolicy = null, IViewLinkLayer<THost,TItem>? linkLayer = null, IViewMeasureHost<THost,TView,TItem>? measureHost = null)` | Groups the layers. Required layers throw `ArgumentNullException` when null. |
| `Factory`, `Container`, `Arranger`, `Scheduler` | The four required layers. |
| `Diagnostics` | Defaults to an internal no-op diagnostics. |
| `PoolPolicy` | Defaults to an internal policy: batch 3, no budget, unlimited recycling. |
| `LayerPolicy` | Defaults to constant z-order 0. |
| `LinkLayer` | Defaults to inactive. |
| `MeasureHost` | Defaults to a no-op. |

## ViewSourcePipelineCore

```csharp
public class ViewSourcePipelineCore<THost, TView, TItem, TPriorityCore,
    TFactory, TContainer, TArranger, TScheduler, TDiagnostics>
    : ViewHostCore<THost, TView, TItem, TPriorityCore>, IDisposable
    where THost : class where TView : class where TItem : class
    where TFactory : class, IViewFactory<TItem,TView>
    where TContainer : class, IViewContainer<THost,TView,TItem>
    where TArranger : class, IViewArranger<TItem,TView>
    where TScheduler : class, IViewScheduler<TPriorityCore>
    where TDiagnostics : class, IViewDiagnostics<TItem>
```

| Member | Description |
|---|---|
| `ViewSourcePipelineCore(THost hostElement, TFactory factory, TContainer container, TArranger arranger, TScheduler scheduler, TDiagnostics diagnostics, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null, IViewLayerPolicy<TItem>? layerPolicy = null, IViewLinkLayer<THost,TItem>? linkLayer = null, IViewMeasureHost<THost,TView,TItem>? measureHost = null)` | Composes the layer instances and starts the shared pool. |
| `Pool` | The running `ViewPool<THost,TView,TItem,TPriorityCore>`. Dispose the pipeline to stop it. |
| `Dispose()` | Stops tracking and releases every active view. Virtual. |

## Notes

- The Core defaults are deliberately minimal. An adapter that wants adaptive batching passes an `AdaptiveViewPoolPolicy`.
- `IViewScheduler.Schedule` posting is the only thread boundary in the whole pipeline.
- A failure is reported through `Diagnostics.Failed`; the rest of the batch continues.
