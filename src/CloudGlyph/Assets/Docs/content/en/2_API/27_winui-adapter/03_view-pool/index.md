# View pool

The WinUI pool is closed over `Panel`, `FrameworkElement` and `IWorkflowComponent`. Its container and arranger share an internal `ViewLayoutTracker`, so later geometry changes follow the item without the host wiring anything.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (attachment) and `VeloxDev.WorkflowSystem.ViewHosting` (pipeline), assembly `VeloxDev.WinUI`.

## ViewPool (attached)

**Signature:** `sealed class ViewPool : DependencyObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | Visible-item collection. |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | Selects the view for each item type. |

Accessors: `GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)`, `GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, DataTemplateSelector?)`.

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**Expected result:** one view per visible item; a deactivated view stays on the panel with `Visibility.Collapsed`.

## ViewSourcePipeline

**Signature:** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent, DispatcherQueuePriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewSourcePipeline(Panel panel, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | constructor | Builds the layers and starts the pool. `poolPolicy` defaults to `AdaptiveViewPoolPolicy()`. |
| `Pool` | `ViewPool<Panel, FrameworkElement, IWorkflowComponent, DispatcherQueuePriority>` | The running pool. |
| `Dispose()` | `override void` | Stops tracking and releases every view. |

The public constructor creates one `ViewLayoutTracker` and passes it to both `ViewContainer` and `ViewArranger`, which is why they take it through their internal constructors.

**Expected result:** the pipeline materializes views on `DispatcherQueuePriority.Low` and follows a node's later `Anchor`/`Size` changes without extra host code.
