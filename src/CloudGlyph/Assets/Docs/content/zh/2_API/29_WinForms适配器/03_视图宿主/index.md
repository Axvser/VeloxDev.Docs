# 视图宿主

命名空间：`VeloxDev.WorkflowSystem.ViewHosting`。

这些类型为 Easel 闭合 Core 的视图池与小地图流水线。它们由 `ViewSourcePipeline` 组合；宿主通常配置附着的 `ViewPool`，而不是直接构造它们。

## 类：ViewSourcePipeline

`public sealed class ViewSourcePipeline : ViewSourcePipelineCore<VisualPanel, VisualElement, IWorkflowComponent, NonPriority, ViewFactory, ViewContainer, ViewArranger, ViewScheduler, ViewDiagnostics>`

### 构造函数

`public ViewSourcePipeline(VisualPanel host, VisualTemplateSelector? templateSelector, INotifyCollectionChanged source, Action? batchCompleted = null, IViewPoolPolicy? poolPolicy = null)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `host` | `VisualPanel` | 拥有物化视图的画布。 |
| `templateSelector` | `VisualTemplateSelector?` | 为每项创建一个视图；`null` 拒绝所有项。 |
| `source` | `INotifyCollectionChanged` | 可见项集合。 |
| `batchCompleted` | `Action?` | 完成一次创建或复用视图的批次后调用。 |
| `poolPolicy` | `IViewPoolPolicy?` | 批次/回收策略；默认 `AdaptiveViewPoolPolicy`。 |

**返回：** 一个运行中的流水线。

`public override void Dispose()` 先释放容器挂上的视图，再释放 Core 记账。画布本身留在树里。

## 类：ViewFactory

`public sealed class ViewFactory : IViewFactory<IWorkflowComponent, VisualElement>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `ViewFactory(VisualTemplateSelector? selector)` | — | 存储选择器。 |
| `WantsItem(IWorkflowComponent item)` | `bool` | 恒为 `true`。 |
| `CreateView(IWorkflowComponent item)` | `VisualElement?` | 调用 `selector.SelectTemplate(item)`；无选择器时为 `null`。 |

## 类：ViewContainer

`public sealed class ViewContainer : IViewContainer<VisualPanel, VisualElement, IWorkflowComponent>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `Attach(VisualPanel host, VisualElement view)` | `void` | 按模板的 z 序加入视图，并绑定待定项。 |
| `Detach(VisualPanel host, VisualElement view)` | `void` | 空操作：池化视图保持父子关系，只隐藏并解绑。 |
| `Activate(VisualElement view, IWorkflowComponent item)` | `void` | 已挂上则立即绑定；否则推迟到 `Attach`。 |
| `Deactivate(VisualElement view)` | `void` | 清空数据上下文并折叠视图。 |
| `SetZOrder(VisualElement view, int zIndex)` | `void` | 空操作：模板自己绑定 z 序。 |
| `Destroy(VisualPanel host, VisualElement view)` | `void` | 移除并释放视图。 |
| `ReleaseAll(VisualPanel host)` | `void` | 移除并释放本容器挂上的所有视图。 |

## 类：ViewArranger

`public sealed class ViewArranger : IViewArranger<IWorkflowComponent, VisualElement>`

`public void Arrange(VisualElement view, IWorkflowComponent item)` 是空操作：几何由视觉模板负责。

## 类：ViewScheduler

`public sealed class ViewScheduler : IViewScheduler<NonPriority>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `ViewScheduler(VisualPanel host)` | — | 宿主为 `null` 时抛 `ArgumentNullException`。 |
| `BatchPriority` | `NonPriority` | `default`。 |
| `Schedule(Action batch, NonPriority priority)` | `bool` | 有消息循环时走 `BeginInvoke`，否则内联执行。批次为 `null` 时抛 `ArgumentNullException`。 |

## 类：ViewDiagnostics

`public sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

`public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` 写入 `Debug.WriteLine`，不打断批次。

## 类：ViewLayerPolicy

`public sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

`public int GetZOrder(IWorkflowComponent item)` 返回 `0`。模板自己绑定层号。

## 类：ViewLinkLayer

`public sealed class ViewLinkLayer : IViewLinkLayer<VisualPanel, IWorkflowComponent>`

| 成员 | 类型 / 签名 | 值 |
| --- | --- | --- |
| `IsActive` | `bool` | 恒为 `false`。 |
| `Handles(IWorkflowComponent item)` | `bool` | 恒为 `false`。 |
| `Render(VisualPanel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | 空操作。 |

连线是一视图一项，不是视口级覆盖层。

## 类：ViewMeasureHost

`public sealed class ViewMeasureHost : IViewMeasureHost<VisualPanel, VisualElement, IWorkflowComponent>`

`public void Measure(VisualPanel host, VisualElement view, IWorkflowComponent item)` 是空操作。

## 类：MinimapPipeline

`public sealed class MinimapPipeline : MinimapPipelineCore<Graphics, IMinimapRenderer<Graphics>, IMinimapViewportHost, IMinimapInputHost>`

`public MinimapPipeline(IMinimapRenderer<Graphics> renderer, IMinimapViewportHost viewport, IMinimapInputHost input, MinimapMetrics? metrics = null)`

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `renderer` | `IMinimapRenderer<Graphics>` | 绘制一趟。 |
| `viewport` | `IMinimapViewportHost` | 报告并应用滚动状态。 |
| `input` | `IMinimapInputHost` | 报告指针状态并持有捕获。 |
| `metrics` | `MinimapMetrics?` | 初始尺寸/放置；默认 `MinimapMetrics.Default`。 |

## 类：MinimapRenderer

`public sealed class MinimapRenderer : IMinimapRenderer<Graphics>`

| 签名 | 返回 | 说明 |
| --- | --- | --- |
| `MinimapRenderer(WorkflowMinimapOverlay owner)` | — | `null` 时抛 `ArgumentNullException`。 |
| `Render(Graphics surface, MinimapDrawContext context)` | `void` | 委托给所有者的受保护 `DrawMinimap` 钩子。 |

## 类：MinimapViewportHost

`public sealed class MinimapViewportHost : IMinimapViewportHost`（构造函数为 internal）

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ScrollOffsetX` / `ScrollOffsetY` | `double` | 所有者偏移加 `1e9` 位移，使 Core 的夹取失效。 |
| `ContentOffsetX` / `ContentOffsetY` | `double` | 所有者内容偏移加同一位移。 |
| `ViewportWidth` / `ViewportHeight` | `double` | 所有者视口尺寸。 |
| `ScrollableWidth` / `ScrollableHeight` | `double` | `double.MaxValue`；导航永不写树的布局偏移。 |
| `ApplyScroll(double x, double y)` | `void` | 减回位移后的内容偏移，把原带符号世界原点交给表面。 |

## 类：MinimapInputHost

`public sealed class MinimapInputHost : IMinimapInputHost`

| 签名 / 成员 | 类型 | 说明 |
| --- | --- | --- |
| `MinimapInputHost()` | — | 创建分离宿主，供测试与自定义表面使用。 |
| `PointerPosition` | `(double X, double Y)` | 覆盖层本地空间的指针位置。 |
| `IsPressed` | `bool` | 指针是否按下。 |
| `IsCaptured` | `bool`（get） | 是否已取得捕获。 |
| `ClampRect` | `WorkflowBounds` | 夹取矩形。 |
| `Capture()` | `bool` | 捕获所属表面；分离时返回 `false`。 |
| `Release()` | `void` | 释放捕获。 |
