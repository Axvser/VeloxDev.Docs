# View hosting

Namespace: `VeloxDev.WorkflowSystem.ViewHosting`.

These types close the Core view-pool and minimap pipelines for Jalium. `ViewSourcePipeline` composes them; a host normally configures the attached `ViewPool`.

## Class: ViewSourcePipeline

`public sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

### Constructor

`public ViewSourcePipeline(Panel host, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)`

| Parameter | Type | Description |
| --- | --- | --- |
| `host` | `Panel` | Panel that owns the materialized views. |
| `templateSelector` | `DataTemplateSelector?` | Consulted first; `null` searches resources only. |
| `source` | `INotifyCollectionChanged` | Visible-item collection. |
| `poolPolicy` | `IViewPoolPolicy?` | Batch/recycle policy; defaults to `AdaptiveViewPoolPolicy`. |

## Class: ViewFactory

`public sealed class ViewFactory : IViewFactory<IWorkflowComponent, FrameworkElement>`

| Signature | Returns | Description |
| --- | --- | --- |
| `ViewFactory(Panel host, DataTemplateSelector? templateSelector)` | — | Throws `ArgumentNullException` for a `null` host. |
| `WantsItem(IWorkflowComponent item)` | `bool` | Always `true`. |
| `CreateView(IWorkflowComponent item)` | `FrameworkElement?` | Resolves a `DataTemplate` and calls `LoadContent()`. |

Lookup order is the selector, then each visual-tree ancestor's resources by `DataType`, then `Application` resources. The template is cached by the item's runtime type; a failed lookup is `null` and the pool remembers it per type.

## Class: ViewContainer

`public sealed class ViewContainer : IViewContainer<Panel, FrameworkElement, IWorkflowComponent>`

| Signature | Returns | Description |
| --- | --- | --- |
| `Attach(Panel host, FrameworkElement view)` | `void` | Adds the view to `host.Children` once. |
| `Detach(Panel host, FrameworkElement view)` | `void` | No-op: a recycled view stays in `Children`, hidden and unbound. |
| `Activate(FrameworkElement view, IWorkflowComponent item)` | `void` | Sets the data context and makes the view visible. |
| `Deactivate(FrameworkElement view)` | `void` | Clears the data context and collapses the view. |
| `SetZOrder(FrameworkElement view, int zIndex)` | `void` | No-op: templates bind `Panel.ZIndex`. |
| `Destroy(Panel host, FrameworkElement view)` | `void` | Removes the view from `Children`. |

## Class: ViewArranger

`public sealed class ViewArranger : IViewArranger<IWorkflowComponent, FrameworkElement>`

`public void Arrange(FrameworkElement view, IWorkflowComponent item)` is a no-op. Node templates bind `Canvas.Left` / `Canvas.Top`; link views move their own box through `WorkflowLinkBounds`.

## Class: ViewScheduler

`public sealed class ViewScheduler : IViewScheduler<DispatcherPriority>`

| Signature | Returns | Description |
| --- | --- | --- |
| `ViewScheduler(Panel host)` | — | Throws `ArgumentNullException` for a `null` host. |
| `BatchPriority` | `DispatcherPriority` | `DispatcherPriority.Background`. |
| `Schedule(Action batch, DispatcherPriority priority)` | `bool` | Posts through `host.Dispatcher.BeginInvoke`; always `true`. |

## Class: ViewDiagnostics

`public sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

`public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` writes to `Debug.WriteLine` and does not interrupt the batch.

## Class: ViewLayerPolicy

`public sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

`public int GetZOrder(IWorkflowComponent item)` returns `0`.

## Class: ViewLinkLayer

`public sealed class ViewLinkLayer : IViewLinkLayer<Panel, IWorkflowComponent>`

| Member | Type / signature | Value |
| --- | --- | --- |
| `IsActive` | `bool` | Always `false`. |
| `Handles(IWorkflowComponent item)` | `bool` | Always `false`. |
| `Render(Panel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | No-op. |

## Class: ViewMeasureHost

`public sealed class ViewMeasureHost : IViewMeasureHost<Panel, FrameworkElement, IWorkflowComponent>`

`public void Measure(Panel host, FrameworkElement view, IWorkflowComponent item)` is a no-op.

## Class: MinimapPipeline

`public sealed class MinimapPipeline : MinimapPipelineCore<DrawingContext, IMinimapRenderer<DrawingContext>, IMinimapViewportHost, IMinimapInputHost>`

`public MinimapPipeline(IMinimapRenderer<DrawingContext> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)`

## Class: MinimapRenderer

`public sealed class MinimapRenderer : IMinimapRenderer<DrawingContext>`

| Signature | Returns | Description |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | — | Throws `ArgumentNullException` for `null`. |
| `Render(DrawingContext surface, MinimapDrawContext context)` | `void` | Delegates to the owner's protected `DrawMinimap` hook. |

## Class: MinimapViewportHost

`public sealed class MinimapViewportHost : IMinimapViewportHost`

| Signature / member | Type | Description |
| --- | --- | --- |
| `MinimapViewportHost(ScrollViewer scrollViewer)` | — | Standalone host that reads and scrolls the viewer directly. Throws `ArgumentNullException` for `null`. |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Owner offset, else viewer offset. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Owner content offset, else `0`. |
| `ViewportWidth` / `ViewportHeight` | `double` | Owner viewport, else viewer viewport. |
| `ScrollableWidth` / `ScrollableHeight` | `double` | Viewer scrollable extent. |
| `ApplyScroll(double x, double y)` | `void` | Writes to the owner overlay, else `ScrollToHorizontalOffset` / `ScrollToVerticalOffset`. |

The overlay-backed constructor is internal; hosts use the `ScrollViewer` form or the surface pushes values.

## Class: MinimapInputHost

`public sealed class MinimapInputHost : IMinimapInputHost`

| Signature / member | Type | Description |
| --- | --- | --- |
| `MinimapInputHost()` | — | Detached host for tests. |
| `PointerPosition` | `(double X, double Y)` | Pointer position in overlay-local space. |
| `IsPressed` | `bool` | Whether the pointer is down. |
| `IsCaptured` | `bool` (get) | Whether capture was taken. |
| `ClampRect` | `WorkflowBounds` | Clamp rectangle. |
| `Capture()` | `bool` | Calls the owner's `CaptureMouse`; a detached host reports `true`. |
| `Release()` | `void` | Calls `ReleaseMouseCapture`. |
