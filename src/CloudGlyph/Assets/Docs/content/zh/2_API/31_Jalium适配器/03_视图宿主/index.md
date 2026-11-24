# 视图宿主

命名空间：`VeloxDev.WorkflowSystem.ViewHosting`。

这些类型为 Jalium 闭合 Core 的视图池与小地图流水线。`ViewSourcePipeline` 组合它们；宿主通常配置附着的 `ViewPool`。

## 类：ViewSourcePipeline

`public sealed class ViewSourcePipeline : ViewSourcePipelineCore<Panel, FrameworkElement, IWorkflowComponent, DispatcherPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

### 构造函数

`public ViewSourcePipeline(Panel host, DataTemplateSelector? templateSelector, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `host` | `Panel` | 拥有物化视图的面板。 |
| `templateSelector` | `DataTemplateSelector?` | 优先查询；`null` 时只查资源。 |
| `source` | `INotifyCollectionChanged` | 可见项集合。 |
| `poolPolicy` | `IViewPoolPolicy?` | 批次/回收策略；默认 `AdaptiveViewPoolPolicy`。 |

## 类：ViewFactory

`public sealed class ViewFactory : IViewFactory<IWorkflowComponent, FrameworkElement>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `ViewFactory(Panel host, DataTemplateSelector? templateSelector)` | — | 宿主为 `null` 时抛 `ArgumentNullException`。 |
| `WantsItem(IWorkflowComponent item)` | `bool` | 恒为 `true`。 |
| `CreateView(IWorkflowComponent item)` | `FrameworkElement?` | 解析 `DataTemplate` 并调用 `LoadContent()`。 |

查找顺序是选择器、沿可视树上溯的 `DataType` 资源、`Application` 资源。模板按项的运行时类型缓存；查找失败返回 `null`，池按类型记住这个结果。

## 类：ViewContainer

`public sealed class ViewContainer : IViewContainer<Panel, FrameworkElement, IWorkflowComponent>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Attach(Panel host, FrameworkElement view)` | `void` | 把视图加入 `host.Children`（一次）。 |
| `Detach(Panel host, FrameworkElement view)` | `void` | 空操作：复用的视图留在 `Children` 里，只隐藏并解绑。 |
| `Activate(FrameworkElement view, IWorkflowComponent item)` | `void` | 设置数据上下文并让视图可见。 |
| `Deactivate(FrameworkElement view)` | `void` | 清空数据上下文并折叠视图。 |
| `SetZOrder(FrameworkElement view, int zIndex)` | `void` | 空操作：模板绑 `Panel.ZIndex`。 |
| `Destroy(Panel host, FrameworkElement view)` | `void` | 从 `Children` 移除视图。 |

## 类：ViewArranger

`public sealed class ViewArranger : IViewArranger<IWorkflowComponent, FrameworkElement>`

`public void Arrange(FrameworkElement view, IWorkflowComponent item)` 是空操作。节点模板绑 `Canvas.Left` / `Canvas.Top`；连线视图通过 `WorkflowLinkBounds` 自己挪盒子。

## 类：ViewScheduler

`public sealed class ViewScheduler : IViewScheduler<DispatcherPriority>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `ViewScheduler(Panel host)` | — | 宿主为 `null` 时抛 `ArgumentNullException`。 |
| `BatchPriority` | `DispatcherPriority` | `DispatcherPriority.Background`。 |
| `Schedule(Action batch, DispatcherPriority priority)` | `bool` | 经 `host.Dispatcher.BeginInvoke` 投递；恒为 `true`。 |

## 类：ViewDiagnostics

`public sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

`public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` 写入 `Debug.WriteLine`，不打断批次。

## 类：ViewLayerPolicy

`public sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

`public int GetZOrder(IWorkflowComponent item)` 返回 `0`。

## 类：ViewLinkLayer

`public sealed class ViewLinkLayer : IViewLinkLayer<Panel, IWorkflowComponent>`

| 成员 | 类型 / 签名 | 值 |
| --- | --- | --- |
| `IsActive` | `bool` | 恒为 `false`。 |
| `Handles(IWorkflowComponent item)` | `bool` | 恒为 `false`。 |
| `Render(Panel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | 空操作。 |

## 类：ViewMeasureHost

`public sealed class ViewMeasureHost : IViewMeasureHost<Panel, FrameworkElement, IWorkflowComponent>`

`public void Measure(Panel host, FrameworkElement view, IWorkflowComponent item)` 是空操作。

## 类：MinimapPipeline

`public sealed class MinimapPipeline : MinimapPipelineCore<DrawingContext, IMinimapRenderer<DrawingContext>, IMinimapViewportHost, IMinimapInputHost>`

`public MinimapPipeline(IMinimapRenderer<DrawingContext> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)`

## 类：MinimapRenderer

`public sealed class MinimapRenderer : IMinimapRenderer<DrawingContext>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | — | `null` 时抛 `ArgumentNullException`。 |
| `Render(DrawingContext surface, MinimapDrawContext context)` | `void` | 委托给所有者的受保护 `DrawMinimap` 钩子。 |

## 类：MinimapViewportHost

`public sealed class MinimapViewportHost : IMinimapViewportHost`

| 签名 / 成员 | 类型 | 说明 |
| --- | --- | --- |
| `MinimapViewportHost(ScrollViewer scrollViewer)` | — | 直接读取并滚动查看器的独立宿主。`null` 时抛 `ArgumentNullException`。 |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | 所有者偏移，否则查看器偏移。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | 所有者内容偏移，否则 `0`。 |
| `ViewportWidth` / `ViewportHeight` | `double` | 所有者视口，否则查看器视口。 |
| `ScrollableWidth` / `ScrollableHeight` | `double` | 查看器可滚动范围。 |
| `ApplyScroll(double x, double y)` | `void` | 写到所有者覆盖层，否则 `ScrollToHorizontalOffset` / `ScrollToVerticalOffset`。 |

覆盖层形式的构造函数是 internal；宿主使用 `ScrollViewer` 形式，或由表面推送值。

## 类：MinimapInputHost

`public sealed class MinimapInputHost : IMinimapInputHost`

| 签名 / 成员 | 类型 | 说明 |
| --- | --- | --- |
| `MinimapInputHost()` | — | 供测试使用的分离宿主。 |
| `PointerPosition` | `(double X, double Y)` | 覆盖层本地空间的指针位置。 |
| `IsPressed` | `bool` | 指针是否按下。 |
| `IsCaptured` | `bool`（get） | 是否已取得捕获。 |
| `ClampRect` | `WorkflowBounds` | 夹取矩形。 |
| `Capture()` | `bool` | 调用所有者的 `CaptureMouse`；分离宿主返回 `true`。 |
| `Release()` | `void` | 调用 `ReleaseMouseCapture`。 |
