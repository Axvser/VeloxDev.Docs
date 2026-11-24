# 视图池

WinUI 的池在 `Panel`、`FrameworkElement` 与 `IWorkflowComponent` 上闭合。其容器与排列器共享一个内部 `ViewLayoutTracker`，因此后续几何变化会跟随条目，宿主无需接线。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（附着）与 `VeloxDev.WorkflowSystem.ViewHosting`（管道），程序集 `VeloxDev.WinUI`。

## ViewPool（附着）

**签名：** `sealed class ViewPool : DependencyObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | 可见条目集合。 |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | 为每个条目类型选择视图。 |

访问器：`GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)`、`GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, DataTemplateSelector?)`。

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**预期结果：** 每个可见条目一个视图；停用的视图以 `Visibility.Collapsed` 留在面板上。

## ViewSourcePipeline

**签名：** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent, DispatcherQueuePriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewSourcePipeline(Panel panel, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | 构造函数 | 构建各层并启动池。`poolPolicy` 默认 `AdaptiveViewPoolPolicy()`。 |
| `Pool` | `ViewPool<Panel, FrameworkElement, IWorkflowComponent, DispatcherQueuePriority>` | 运行中的池。 |
| `Dispose()` | `override void` | 停止跟踪并释放所有视图。 |

公开构造函数创建一个 `ViewLayoutTracker` 并传给 `ViewContainer` 与 `ViewArranger`，它们因此通过内部构造函数接收它。

**预期结果：** 管道在 `DispatcherQueuePriority.Low` 上物化视图，并跟随节点的后续 `Anchor`/`Size` 变化，无需额外宿主代码。
