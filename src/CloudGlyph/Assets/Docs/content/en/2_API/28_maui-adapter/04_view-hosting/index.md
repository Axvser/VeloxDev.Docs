# View hosting

The concrete MAUI layers behind `ViewSourcePipeline`. `ViewScheduler` and `ViewArranger` are disposable and owned by the pipeline.

## Namespace

`VeloxDev.WorkflowSystem.ViewHosting`, assembly `VeloxDev.MAUI`.

## ViewFactory

**Signature:** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, View>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewFactory(Layout host, DataTemplateSelector? selector)` | public constructor | Creates views for one layout. |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | Always `true`. |
| `CreateView` | `View? CreateView(IWorkflowComponent item)` | Applies the selector; `null` when no template matches. |

## ViewContainer

**Signature:** `sealed class ViewContainer : IViewContainer<Layout, View, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewContainer()` | public constructor | Creates a container with no geometry layer to notify. |
| `ViewContainer(ViewArranger? arranger)` | public constructor | Releases `arranger`'s item subscription when a view leaves the pool. |
| `Attach(Layout host, View view)` | `void` | Adds the view to the layout. |
| `Detach(Layout host, View view)` | `void` | Removes it. |
| `Activate(View view, IWorkflowComponent item)` | `void` | Binds item state. |
| `Deactivate(View view)` | `void` | Releases bound state, hides the view and parks it at `ZIndex −100`. |
| `SetZOrder(View view, int zIndex)` | `void` | Sets `ZIndex`. |
| `Destroy(Layout host, View view)` | `void` | Removes a view the pool refused to keep. |

## ViewArranger

**Signature:** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, View>, IDisposable`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewArranger(Layout host)` | public constructor | Creates the geometry layer for one layout. |
| `Arrange(View view, IWorkflowComponent item)` | `void` | Applies the item's geometry and tracks later changes. |
| `Dispose()` | `void` | Releases every tracked view. |

## ViewScheduler

**Signature:** `sealed class ViewScheduler : IViewScheduler<NonPriority>, IDisposable`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewScheduler(Layout host)` | public constructor | Posts batches through `host`'s dispatcher; throws `ArgumentNullException` for a null host. |
| `BatchPriority` | `NonPriority` | `default`; MAUI has no priority concept. |
| `Schedule(Action batch, NonPriority priority)` | `bool` | Queues one batch; `false` after disposal. |
| `Dispose()` | `void` | Stops the timer. |

## ViewDiagnostics

**Signature:** `sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` | `void` | Reports the failed stage. |

## ViewLayerPolicy

**Signature:** `sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `GetZOrder(IWorkflowComponent item)` | `int` | Returns `0`. |

## ViewLinkLayer

**Signature:** `sealed class ViewLinkLayer : IViewLinkLayer<Layout, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `IsActive` | `bool` | Always `true`. |
| `Handles(IWorkflowComponent item)` | `bool` | `item is ILinkComponent`. |
| `Render(Layout host, IReadOnlyList<IWorkflowComponent> items)` | `void` | No-op here; the overlay draws links. |

## ViewMeasureHost

**Signature:** `sealed class ViewMeasureHost : IViewMeasureHost<Layout, View, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Measure(Layout host, View view, IWorkflowComponent item)` | `void` | Runs a measure pass. |

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
```

**Expected result:** the pipeline creates these layers itself; replacing `ViewLinkLayer` is the supported way to change which item types the overlay owns.
