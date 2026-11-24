# View hosting

The concrete WPF layers behind `ViewSourcePipeline`. They are public so a host can replace one layer or compose its own pipeline; most users never name them.

## Namespace

`VeloxDev.WorkflowSystem.ViewHosting`, assembly `VeloxDev.WPF`.

## ViewFactory

**Signature:** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, FrameworkElement>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewFactory(Panel panel, DataTemplateSelector? templateSelector)` | constructor | Creates views for one panel. |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | Always `true`. |
| `CreateView` | `FrameworkElement? CreateView(IWorkflowComponent item)` | Applies the selector; returns `null` when no template matches. |

## ViewContainer

**Signature:** `sealed class ViewContainer : IViewContainer<Panel, FrameworkElement, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Attach(Panel host, FrameworkElement view)` | `void` | Adds the view to the panel's children. |
| `Detach(Panel host, FrameworkElement view)` | `void` | Removes it. |
| `Activate(FrameworkElement view, IWorkflowComponent item)` | `void` | Sets `DataContext` to the item. |
| `Deactivate(FrameworkElement view)` | `void` | Clears `DataContext` and collapses the view. |
| `SetZOrder(FrameworkElement view, int zIndex)` | `void` | No-op; the item templates bind `Panel.ZIndex` themselves. |
| `Destroy(Panel host, FrameworkElement view)` | `void` | Disposes and removes a view the pool refused to keep. |

## ViewArranger

**Signature:** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, FrameworkElement>`

| Member | Signature | Description |
| --- | --- | --- |
| `Arrange(FrameworkElement view, IWorkflowComponent item)` | `void` | No-op; the item template binds `Canvas.Left`, `Canvas.Top` and its size itself. |

## ViewScheduler

**Signature:** `sealed class ViewScheduler : IViewScheduler<DispatcherPriority>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewScheduler(Dispatcher dispatcher)` | constructor | Schedules on the given dispatcher. |
| `BatchPriority` | `DispatcherPriority` | `Background`. |
| `Schedule(Action batch, DispatcherPriority priority)` | `bool` | Posts via `BeginInvoke`; always returns `true`. |

## ViewDiagnostics

**Signature:** `sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` | `void` | Reports the failed stage to the debugger/trace output. |

## ViewLayerPolicy

**Signature:** `sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `GetZOrder(IWorkflowComponent item)` | `int` | Returns `0`; the WPF pool leaves stacking to the template. |

## ViewLinkLayer

**Signature:** `sealed class ViewLinkLayer : IViewLinkLayer<Panel, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `IsActive` | `bool` | Always `false`. |
| `Handles(IWorkflowComponent item)` | `bool` | Always `false`; links are pooled views on WPF. |
| `Render(Panel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | No-op. |

## ViewMeasureHost

**Signature:** `sealed class ViewMeasureHost : IViewMeasureHost<Panel, FrameworkElement, IWorkflowComponent>`

| Member | Signature | Description |
| --- | --- | --- |
| `Measure(Panel host, FrameworkElement view, IWorkflowComponent item)` | `void` | Runs a measure pass on a freshly arranged view. |

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
var diagnostics = new ViewDiagnostics();
```

**Expected result:** replacing `ViewLinkLayer` with one whose `Handles` accepts `ILinkComponent` routes links away from the pooled views to that layer.
