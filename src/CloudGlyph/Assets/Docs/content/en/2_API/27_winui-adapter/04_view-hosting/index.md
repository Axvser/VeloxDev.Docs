# View hosting

The concrete WinUI layers behind `ViewSourcePipeline`. `ViewContainer` and `ViewArranger` are public types with **internal** constructors: they are constructed by the pipeline, which shares one internal `ViewLayoutTracker` between them. `ViewFactory` and the policy layers are directly constructible.

## Namespace

`VeloxDev.WorkflowSystem.ViewHosting`, assembly `VeloxDev.WinUI`.

## ViewFactory

**Signature:** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, FrameworkElement>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewFactory(Panel panel, DataTemplateSelector? templateSelector)` | public constructor | Creates views for one panel. |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | Always `true`. |
| `CreateView` | `FrameworkElement? CreateView(IWorkflowComponent item)` | Applies the selector; `null` when no template matches. |

## ViewContainer

**Signature:** `sealed class ViewContainer : IViewContainer<Panel, FrameworkElement, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Attach(Panel host, FrameworkElement view)` | `void` | Adds the view to the panel. |
| `Detach(Panel host, FrameworkElement view)` | `void` | Removes it. |
| `Activate(FrameworkElement view, IWorkflowComponent item)` | `void` | Binds item state. |
| `Deactivate(FrameworkElement view)` | `void` | Releases bound state and unsubscribes the arranger. |
| `SetZOrder(FrameworkElement view, int zIndex)` | `void` | No-op; `ViewArranger` writes `Canvas.ZIndex` from `Anchor.Layer`. |
| `Destroy(Panel host, FrameworkElement view)` | `void` | Removes a view the pool refused to keep. |

The constructor is `internal ViewContainer(ViewLayoutTracker layout)`; the pipeline supplies the tracker.

## ViewArranger

**Signature:** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, FrameworkElement>`

| Member | Signature | Description |
| --- | --- | --- |
| `Arrange(FrameworkElement view, IWorkflowComponent item)` | `void` | Applies geometry and subscribes to later geometry changes. |

The constructor is `internal ViewArranger(ViewLayoutTracker layout)`.

## ViewScheduler

**Signature:** `sealed class ViewScheduler : IViewScheduler<DispatcherQueuePriority>`

| Member | Signature | Description |
| --- | --- | --- |
| `BatchPriority` | `DispatcherQueuePriority` | `Low`. |
| `Schedule(Action batch, DispatcherQueuePriority priority)` | `bool` | `TryEnqueue`; returns `false` when the queue is shutting down. |

The constructor is `internal ViewScheduler(DispatcherQueue? queue)`; the pipeline passes the panel's queue.

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

**Signature:** `sealed class ViewLinkLayer : IViewLinkLayer<Panel, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `IsActive` | `bool` | Always `false`. |
| `Handles(IWorkflowComponent item)` | `bool` | Always `false`; links are pooled views. |
| `Render(Panel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | No-op. |

## ViewMeasureHost

**Signature:** `sealed class ViewMeasureHost : IViewMeasureHost<Panel, FrameworkElement, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Measure(Panel host, FrameworkElement view, IWorkflowComponent item)` | `void` | Runs a measure pass. |

## ViewLayoutTracker

`internal sealed class ViewLayoutTracker` (not public). It keeps the shared subscription table used by `ViewContainer` and `ViewArranger`, so a deactivated view unsubscribes the handler the arranger attached. It is not part of the public API.

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
```

**Expected result:** the internal tracker is shared by construction; a host that replaces one layer is responsible for keeping a matching pair.
