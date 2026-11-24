# 视图池

MAUI 的池在 `Layout`、`View` 与 `IWorkflowComponent` 上闭合。其连线层把 `ILinkComponent` 从池中接管并交给 `WorkflowLinkOverlay`，因此池只物化节点视图。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（附着）与 `VeloxDev.WorkflowSystem.ViewHosting`（管道），程序集 `VeloxDev.MAUI`。

## ViewPool（附着）

**签名：** `sealed class ViewPool`（静态附着属性类）

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | 可见条目集合。 |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | 为每个条目类型选择视图。 |

访问器：`GetItemsSource(BindableObject)` / `SetItemsSource(BindableObject, INotifyCollectionChanged?)`、`GetTemplateSelector(BindableObject)` / `SetTemplateSelector(BindableObject, DataTemplateSelector?)`。

```xml
<AbsoluteLayout x:Name="PART_Canvas" BackgroundColor="Transparent"
                behaviors:ViewPool.ItemsSource="{Binding BindingContext.Helper.VisibleItems, Source={x:Reference Root}}"
                behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**预期结果：** 池物化节点视图并跳过连线，因为 `ViewLinkLayer.Handles` 接受 `ILinkComponent`。

## ViewSourcePipeline

**签名：** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Layout, View, IWorkflowComponent, NonPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewSourcePipeline(Layout host, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | 构造函数 | 构建各层并启动池。`poolPolicy` 默认 `AdaptiveViewPoolPolicy(initialBatchSize: 32, initialBudgetMilliseconds: 8d)`。 |
| `Pool` | `ViewPool<Layout, View, IWorkflowComponent, NonPriority>` | 运行中的池。 |
| `Dispose()` | `override void` | 先释放池，再释放调度器与排列器。 |

较小的默认批次（32 而非 64）避免手机尺寸视口在策略仍学习本机视图成本时，冷启动滚动卡住一帧。

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
Console.WriteLine(pipeline.Pool.ActiveViewCount);
pipeline.Dispose();
```

**预期结果：** 节点视图被池化；连线由覆盖层渲染，释放管道会同时释放调度器定时器与排列器订阅。
