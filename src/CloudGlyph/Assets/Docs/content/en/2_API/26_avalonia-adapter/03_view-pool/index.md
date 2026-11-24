# View pool

The Avalonia pool is closed over `Panel`, `Control` and `IWorkflowComponent`. Its selector is an `IDataTemplate`, which both selects and builds. Users attach `ViewPool.ItemsSource` and `ViewPool.TemplateSelector`; the attached behavior owns the pipeline.

## Namespace

`VeloxDev.WorkflowSystem.AttachedBehaviors` (attachment) and `VeloxDev.WorkflowSystem.ViewHosting` (pipeline and policy), assembly `VeloxDev.Avalonia`.

## ViewPool (attached)

**Signature:** `sealed class ViewPool : AvaloniaObject`

| Attached property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | Visible-item collection. |
| `TemplateSelector` | `IDataTemplate?` | `null` | Selects and builds the view for each item type. |

Accessors: `GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)`, `GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, IDataTemplate?)`.

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**Expected result:** the pool materializes one view per visible item; a selector whose `Build` throws for a type is reported through diagnostics.

## ViewSourcePipeline

**Signature:** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, Control, IWorkflowComponent, DispatcherPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewSourcePipeline(Panel panel, IDataTemplate? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | constructor | Builds the layers and starts the pool. `poolPolicy` defaults to `AdaptiveViewPoolPolicy()`. |
| `Pool` | `ViewPool<Panel, Control, IWorkflowComponent, DispatcherPriority>` | The running pool. |
| `Dispose()` | `override void` | Stops tracking and releases every view. |

The constructor composes `ViewScheduler()`, `ViewContainer()`, `ViewArranger()`, `ViewLayerPolicy()`, `ViewLinkLayer()` and `ViewMeasureHost()`.

## ViewPoolPolicy

**Signature:** `sealed class ViewPoolPolicy : IViewPoolPolicy`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewPoolPolicy(int batchSize = 1024, double frameBudgetMilliseconds = 16d)` | constructor | A large batch bounded by one frame. |
| `BatchSize` | `int` | Maximum views per batch; values below one are treated as one. |
| `FrameBudgetMilliseconds` | `double` | Wall-clock budget; zero or negative means no limit. |
| `MaxRecycledViewsPerType` | `int` | Always `0` (unlimited recycling). |

```csharp
var pipeline = new ViewSourcePipeline(
    canvas, selector, tree.GetHelper().VisibleItems, new ViewPoolPolicy(batchSize: 512));

Console.WriteLine(pipeline.Pool.ActiveViewCount);
pipeline.Dispose();
```

**Expected result:** the pool uses the supplied policy instead of the adaptive default, and `Dispose` releases every active view.
