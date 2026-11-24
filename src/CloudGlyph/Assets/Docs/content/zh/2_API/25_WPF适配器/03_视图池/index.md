# 视图池

WPF 的池在 `Panel`、`FrameworkElement` 与 `IWorkflowComponent` 上闭合一次。用户把 `ViewPool.ItemsSource` 与 `ViewPool.TemplateSelector` 附着到画布；附着行为为每个面板构建一个 `ViewSourcePipeline` 并管理其生命周期。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（附着）与 `VeloxDev.WorkflowSystem.ViewHosting`（闭合管道），程序集 `VeloxDev.WPF`。

## ViewPool（附着）

**签名：** `sealed class ViewPool : DependencyObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | 可见条目集合，通常是 `tree.GetHelper().VisibleItems`。 |
| `TemplateSelector` | `DataTemplateSelector?` | `null` | 为每个条目类型选择视图。 |

访问器：`GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)`、`GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, DataTemplateSelector?)`。

附着仅对 `Panel` 有效。任一属性变化时，行为创建或替换管道；把 `ItemsSource` 设为 `null` 会释放它。

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**预期结果：** 池为每个可见条目物化一个视图并按运行时类型回收；对某条目类型抛异常的选择器会经诊断报告，而不会让整次刷新崩溃。

## ViewSourcePipeline

**签名：** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewSourcePipeline(Panel panel, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | 构造函数 | 为 `panel` 构建各层并启动池。`poolPolicy` 默认 `AdaptiveViewPoolPolicy()`。 |
| `Pool` | `ViewPool<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority>` | 运行中的池。 |
| `Dispose()` | `override void` | 停止跟踪并释放所有视图。 |

构造函数组合 `ViewScheduler(panel.Dispatcher)`、`ViewContainer()`、`ViewArranger()`、`ViewLayerPolicy()`、`ViewLinkLayer()` 与 `ViewMeasureHost()`。

**预期结果：** `pipeline.Pool.ActiveViewCount` 等于已物化视图的可见条目数。
