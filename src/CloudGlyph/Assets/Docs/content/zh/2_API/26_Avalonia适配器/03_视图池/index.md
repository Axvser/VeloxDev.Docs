# 视图池

Avalonia 的池在 `Panel`、`Control` 与 `IWorkflowComponent` 上闭合。它的选择器是 `IDataTemplate`，既选择也构建。用户附着 `ViewPool.ItemsSource` 与 `ViewPool.TemplateSelector`；附着行为拥有管道。

## 命名空间

`VeloxDev.WorkflowSystem.AttachedBehaviors`（附着）与 `VeloxDev.WorkflowSystem.ViewHosting`（管道与策略），程序集 `VeloxDev.Avalonia`。

## ViewPool（附着）

**签名：** `sealed class ViewPool : AvaloniaObject`

| 附着属性 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `ItemsSource` | `INotifyCollectionChanged?` | `null` | 可见条目集合。 |
| `TemplateSelector` | `IDataTemplate?` | `null` | 为每个条目类型选择并构建视图。 |

访问器：`GetItemsSource(Panel)` / `SetItemsSource(Panel, INotifyCollectionChanged?)`、`GetTemplateSelector(Panel)` / `SetTemplateSelector(Panel, IDataTemplate?)`。

```xml
<Canvas x:Name="PART_Canvas"
        behaviors:ViewPool.ItemsSource="{Binding Helper.VisibleItems}"
        behaviors:ViewPool.TemplateSelector="{StaticResource WorkflowTemplateSelector}" />
```

**预期结果：** 池为每个可见条目物化一个视图；`Build` 对某类型抛异常的选择器会经诊断报告。

## ViewSourcePipeline

**签名：** `sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, Control, IWorkflowComponent, DispatcherPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewSourcePipeline(Panel panel, IDataTemplate? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)` | 构造函数 | 构建各层并启动池。`poolPolicy` 默认 `AdaptiveViewPoolPolicy()`。 |
| `Pool` | `ViewPool<Panel, Control, IWorkflowComponent, DispatcherPriority>` | 运行中的池。 |
| `Dispose()` | `override void` | 停止跟踪并释放所有视图。 |

构造函数组合 `ViewScheduler()`、`ViewContainer()`、`ViewArranger()`、`ViewLayerPolicy()`、`ViewLinkLayer()` 与 `ViewMeasureHost()`。

## ViewPoolPolicy

**签名：** `sealed class ViewPoolPolicy : IViewPoolPolicy`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewPoolPolicy(int batchSize = 1024, double frameBudgetMilliseconds = 16d)` | 构造函数 | 以一帧为界的大批次。 |
| `BatchSize` | `int` | 一批最多物化的视图数；小于一按一处理。 |
| `FrameBudgetMilliseconds` | `double` | 墙钟预算；零或负表示不限。 |
| `MaxRecycledViewsPerType` | `int` | 始终为 `0`（不限回收）。 |

```csharp
var pipeline = new ViewSourcePipeline(
    canvas, selector, tree.GetHelper().VisibleItems, new ViewPoolPolicy(batchSize: 512));

Console.WriteLine(pipeline.Pool.ActiveViewCount);
pipeline.Dispose();
```

**预期结果：** 池使用给定策略而非自适应默认值；`Dispose` 释放所有活动视图。
