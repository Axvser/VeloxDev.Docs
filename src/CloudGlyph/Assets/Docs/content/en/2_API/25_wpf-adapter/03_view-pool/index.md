# View pool

The WPF pool is closed once over `Panel`, `FrameworkElement` and `IWorkflowComponent`. Users attach `ViewPool.ItemsSource` and `ViewPool.TemplateSelector` to the canvas; the attached behavior builds one `ViewSourcePipeline` per panel and owns its lifetime.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (attachment) and `VeloxDev.WorkflowSystem.ViewHosting` (closed pipeline), assembly `VeloxDev.WPF`.

## ViewPool (attached)

**Signature:** `sealed class ViewPool : DependencyObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | The visible-item collection, normally `tree.GetHelper().VisibleItems`. |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | Chooses the view for each item type. |

Accessors: `GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)`, `GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, DataTemplateSelector?)`.

The attachment is only valid on a `Panel`. When either property changes, the behavior creates or replaces the pipeline; setting `ItemsSource` to `null` disposes it.

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**Expected result:** the pool materializes one view per visible item and recycles by runtime type; a selector that throws for an item type is reported through diagnostics rather than crashing the pass.

## ViewSourcePipeline

**Signature:** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewSourcePipeline(Panel panel, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | constructor | Builds the layers for `panel` and starts the pool. `poolPolicy` defaults to `AdaptiveViewPoolPolicy()`. |
| `Pool` | `ViewPool<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority>` | The running pool. |
| `Dispose()` | `override void` | Stops tracking and releases every view. |

The constructor composes `ViewScheduler(panel.Dispatcher)`, `ViewContainer()`, `ViewArranger()`, `ViewLayerPolicy()`, `ViewLinkLayer()` and `ViewMeasureHost()`.

**Expected result:** `pipeline.Pool.ActiveViewCount` equals the number of visible items that have a materialized view.
