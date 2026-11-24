# View pool

The MAUI pool is closed over `Layout`, `View` and `IWorkflowComponent`. Its link layer takes `ILinkComponent` out of the pool and hands it to `WorkflowLinkOverlay`, so the pool only materializes node views.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (attachment) and `VeloxDev.WorkflowSystem.ViewHosting` (pipeline), assembly `VeloxDev.MAUI`.

## ViewPool (attached)

**Signature:** `sealed class ViewPool` (a static attached-property class)

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | Visible-item collection. |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | Selects the view for each item type. |

Accessors: `GetItemsSource(BindableObject)` / `SetItemsSource(BindableObject, INotifyCollectionChanged?)`, `GetTemplateSelector(BindableObject)` / `SetTemplateSelector(BindableObject, DataTemplateSelector?)`.

```xml
<AbsoluteLayout x:Name="PART_Canvas" BackgroundColor="Transparent"
                behaviors:ViewPool.ItemsSource="{Binding BindingContext.Helper.VisibleItems, Source={x:Reference Root}}"
                behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**Expected result:** the pool materializes node views and skips links, because `ViewLinkLayer.Handles` accepts `ILinkComponent`.

## ViewSourcePipeline

**Signature:** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Layout, View, IWorkflowComponent, NonPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewSourcePipeline(Layout host, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | constructor | Builds the layers and starts the pool. `poolPolicy` defaults to `AdaptiveViewPoolPolicy(initialBatchSize: 32, initialBudgetMilliseconds: 8d)`. |
| `Pool` | `ViewPool<Layout, View, IWorkflowComponent, NonPriority>` | The running pool. |
| `Dispose()` | `override void` | Disposes the pool, then the scheduler and arranger. |

The lower default batch (32 rather than 64) keeps a cold scroll on a phone-sized viewport from stalling a frame while the policy is still learning this device's view cost.

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
Console.WriteLine(pipeline.Pool.ActiveViewCount);
pipeline.Dispose();
```

**Expected result:** node views are pooled; links are rendered by the overlay, and disposing the pipeline releases both the scheduler timer and the arranger subscriptions.
