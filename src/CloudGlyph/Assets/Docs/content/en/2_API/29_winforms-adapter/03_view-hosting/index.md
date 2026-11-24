# View hosting

Namespace: `VeloxDev.WorkflowSystem.ViewHosting`.

These types close the Core view-pool and minimap pipelines for Easel. They are composed by `ViewSourcePipeline`; a host normally configures the attached `ViewPool` instead of constructing them directly.

## Class: ViewSourcePipeline

`public sealed class ViewSourcePipeline : ViewSourcePipelineCore<VisualPanel, VisualElement, IWorkflowComponent, NonPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

### Constructor

`public ViewSourcePipeline(VisualPanel host, VisualTemplateSelector? templateSelector, INotifyCollectionChanged source, Action? batchCompleted = null, IViewPoolPolicy? poolPolicy = null)`

| Parameter | Type | Description |
| --- | --- | --- |
| `host` | `VisualPanel` | Canvas that owns the materialized views. |
| `templateSelector` | `VisualTemplateSelector?` | Creates one view per item; `null` refuses every item. |
| `source` | `INotifyCollectionChanged` | Visible-item collection. |
| `batchCompleted` | `Action?` | Invoked after a batch that created or reused views. |
| `poolPolicy` | `IViewPoolPolicy?` | Batch/recycle policy; defaults to `AdaptiveViewPoolPolicy`. |

**Returns:** a running pipeline.

`public override void Dispose()` releases the views the container attached, then the Core bookkeeping. The canvas itself stays in the tree.

## Class: ViewFactory

`public sealed class ViewFactory : IViewFactory<IWorkflowComponent, VisualElement>`

| Signature | Returns | Description |
| --- | --- | --- |
| `ViewFactory(VisualTemplateSelector? selector)` | — | Stores the selector. |
| `WantsItem(IWorkflowComponent item)` | `bool` | Always `true`. |
| `CreateView(IWorkflowComponent item)` | `VisualElement?` | Calls `selector.SelectTemplate(item)`; `null` with no selector. |

## Class: ViewContainer

`public sealed class ViewContainer : IViewContainer<VisualPanel, VisualElement, IWorkflowComponent>`

| Signature | Returns | Description |
| --- | --- | --- |
| `Attach(VisualPanel host, VisualElement view)` | `void` | Adds the view at its template z-order and binds the pending item. |
| `Detach(VisualPanel host, VisualElement view)` | `void` | No-op: pooled views stay parented, hidden and unbound. |
| `Activate(VisualElement view, IWorkflowComponent item)` | `void` | Binds immediately when attached; otherwise defers until `Attach`. |
| `Deactivate(VisualElement view)` | `void` | Clears the data context and collapses the view. |
| `SetZOrder(VisualElement view, int zIndex)` | `void` | No-op: templates bind their own z-order. |
| `Destroy(VisualPanel host, VisualElement view)` | `void` | Removes and disposes the view. |
| `ReleaseAll(VisualPanel host)` | `void` | Removes and disposes every view this container attached. |

## Class: ViewArranger

`public sealed class ViewArranger : IViewArranger<IWorkflowComponent, VisualElement>`

`public void Arrange(VisualElement view, IWorkflowComponent item)` is a no-op: the visual templates own geometry.

## Class: ViewScheduler

`public sealed class ViewScheduler : IViewScheduler<NonPriority>`

| Signature | Returns | Description |
| --- | --- | --- |
| `ViewScheduler(VisualPanel host)` | — | Throws `ArgumentNullException` for a `null` host. |
| `BatchPriority` | `NonPriority` | `default`. |
| `Schedule(Action batch, NonPriority priority)` | `bool` | Runs through `BeginInvoke` when a message loop exists; otherwise runs inline. Throws `ArgumentNullException` for a `null` batch. |

## Class: ViewDiagnostics

`public sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

`public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` writes to `Debug.WriteLine` and does not interrupt the batch.

## Class: ViewLayerPolicy

`public sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

`public int GetZOrder(IWorkflowComponent item)` returns `0`. Templates bind their own layer.

## Class: ViewLinkLayer

`public sealed class ViewLinkLayer : IViewLinkLayer<VisualPanel, IWorkflowComponent>`

| Member | Type / signature | Value |
| --- | --- | --- |
| `IsActive` | `bool` | Always `false`. |
| `Handles(IWorkflowComponent item)` | `bool` | Always `false`. |
| `Render(VisualPanel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | No-op. |

Links are one pooled view each, not a viewport-level overlay.

## Class: ViewMeasureHost

`public sealed class ViewMeasureHost : IViewMeasureHost<VisualPanel, VisualElement, IWorkflowComponent>`

`public void Measure(VisualPanel host, VisualElement view, IWorkflowComponent item)` is a no-op.

## Class: MinimapPipeline

`public sealed class MinimapPipeline : MinimapPipelineCore<Graphics, IMinimapRenderer<Graphics>, IMinimapViewportHost, IMinimapInputHost>`

`public MinimapPipeline(IMinimapRenderer<Graphics> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)`

| Parameter | Type | Description |
| --- | --- | --- |
| `renderer` | `IMinimapRenderer<Graphics>` | Draws one pass. |
| `viewport` | `IMinimapViewportHost` | Reports and applies scroll state. |
| `input` | `IMinimapInputHost` | Reports pointer state and owns capture. |
| `metrics` | `MinimapMetrics?` | Initial sizing/placement; defaults to `MinimapMetrics.Default`. |

## Class: MinimapRenderer

`public sealed class MinimapRenderer : IMinimapRenderer<Graphics>`

| Signature | Returns | Description |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | — | Throws `ArgumentNullException` for `null`. |
| `Render(Graphics surface, MinimapDrawContext context)` | `void` | Delegates to the owner's protected `DrawMinimap` hook. |

## Class: MinimapViewportHost

`public sealed class MinimapViewportHost : IMinimapViewportHost` (constructor is internal)

| Member | Type | Description |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | Owner offset plus a `1e9` shift that keeps the Core clamp inert. |
| `ContentOffsetX` / `ContentOffsetY` | `double` | Owner content offset plus the same shift. |
| `ViewportWidth` / `ViewportHeight` | `double` | Owner viewport size. |
| `ScrollableWidth` / `ScrollableHeight` | `double` | `double.MaxValue`; navigation never writes the tree's layout offsets. |
| `ApplyScroll(double x, double y)` | `void` | Subtracts the shifted content offset and hands the surface the signed world origin. |

## Class: MinimapInputHost

`public sealed class MinimapInputHost : IMinimapInputHost`

| Signature / member | Type | Description |
| --- | --- | --- |
| `MinimapInputHost()` | — | Creates a detached host for tests and custom surfaces. |
| `PointerPosition` | `(double X, double Y)` | Pointer position in overlay-local space. |
| `IsPressed` | `bool` | Whether the pointer is down. |
| `IsCaptured` | `bool` (get) | Whether capture was taken. |
| `ClampRect` | `WorkflowBounds` | Clamp rectangle. |
| `Capture()` | `bool` | Captures the owning surface; `false` when detached. |
| `Release()` | `void` | Releases capture. |
