# View hosting

The concrete Avalonia layers behind `ViewSourcePipeline`. They are public so a host can replace one layer or compose its own pipeline.

## Namespace

`VeloxDev.WorkflowSystem.ViewHosting`, assembly `VeloxDev.Avalonia`.

## ViewFactory

**Signature:** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, Control>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewFactory(Panel panel, IDataTemplate? templateSelector)` | constructor | Creates views for one panel. |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | Always `true`. |
| `CreateView` | `Control? CreateView(IWorkflowComponent item)` | Applies the `IDataTemplate`; `null` when none matches. |

## ViewContainer

**Signature:** `sealed class ViewContainer : IViewContainer<Panel, Control, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Attach(Panel host, Control view)` | `void` | Adds the view to the panel. |
| `Detach(Panel host, Control view)` | `void` | Removes it. |
| `Activate(Control view, IWorkflowComponent item)` | `void` | Sets `DataContext`. |
| `Deactivate(Control view)` | `void` | Clears `DataContext` and hides the view. |
| `SetZOrder(Control view, int zIndex)` | `void` | No-op; the item templates bind the z-index themselves. |
| `Destroy(Panel host, Control view)` | `void` | Removes a view the pool refused to keep. |

## ViewArranger

**Signature:** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, Control>`

| Member | Signature | Description |
| --- | --- | --- |
| `Arrange(Control view, IWorkflowComponent item)` | `void` | No-op; Avalonia templates bind the geometry themselves. |

## ViewScheduler

**Signature:** `sealed class ViewScheduler : IViewScheduler<DispatcherPriority>`

| Member | Signature | Description |
| --- | --- | --- |
| `BatchPriority` | `DispatcherPriority` | `Background`. |
| `Schedule(Action batch, DispatcherPriority priority)` | `bool` | Posts to `Dispatcher.UIThread`; always returns `true`. |

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

**Signature:** `sealed class ViewMeasureHost : IViewMeasureHost<Panel, Control, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Measure(Panel host, Control view, IWorkflowComponent item)` | `void` | Runs a measure pass on the view. |

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
```

**Expected result:** the pipeline composes these layers without further configuration; replacing `ViewScheduler` changes which dispatcher priority carries materialization batches.
