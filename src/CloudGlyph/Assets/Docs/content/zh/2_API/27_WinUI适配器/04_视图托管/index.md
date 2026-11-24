# 视图托管

`ViewSourcePipeline` 背后的具体 WinUI 层。`ViewContainer` 与 `ViewArranger` 是公开类型，但构造函数为 **internal**：它们由管道构造，并在两者之间共享一个内部 `ViewLayoutTracker`。`ViewFactory` 与各策略层可直接构造。

## 命名空间

`VeloxDev.WorkflowSystem.ViewHosting`，程序集 `VeloxDev.WinUI`。

## ViewFactory

**签名：** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, FrameworkElement>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewFactory(Panel panel, DataTemplateSelector? templateSelector)` | 公开构造函数 | 为一个面板创建视图。 |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | 始终为 `true`。 |
| `CreateView` | `FrameworkElement? CreateView(IWorkflowComponent item)` | 应用选择器；没有模板匹配时返回 `null`。 |

## ViewContainer

**签名：** `sealed class ViewContainer : IViewContainer<Panel, FrameworkElement, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Attach(Panel host, FrameworkElement view)` | `void` | 把视图加入面板。 |
| `Detach(Panel host, FrameworkElement view)` | `void` | 移除视图。 |
| `Activate(FrameworkElement view, IWorkflowComponent item)` | `void` | 绑定条目状态。 |
| `Deactivate(FrameworkElement view)` | `void` | 释放绑定状态并退订排列器。 |
| `SetZOrder(FrameworkElement view, int zIndex)` | `void` | 空实现；由 `ViewArranger` 按 `Anchor.Layer` 写入 `Canvas.ZIndex`。 |
| `Destroy(Panel host, FrameworkElement view)` | `void` | 移除池不愿保留的视图。 |

构造函数为 `internal ViewContainer(ViewLayoutTracker layout)`；由管道提供跟踪器。

## ViewArranger

**签名：** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, FrameworkElement>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Arrange(FrameworkElement view, IWorkflowComponent item)` | `void` | 应用几何并订阅后续几何变化。 |

构造函数为 `internal ViewArranger(ViewLayoutTracker layout)`。

## ViewScheduler

**签名：** `sealed class ViewScheduler : IViewScheduler<DispatcherQueuePriority>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `BatchPriority` | `DispatcherQueuePriority` | `Low`。 |
| `Schedule(Action batch, DispatcherQueuePriority priority)` | `bool` | `TryEnqueue`；队列关闭时返回 `false`。 |

构造函数为 `internal ViewScheduler(DispatcherQueue? queue)`；由管道传入面板的队列。

## ViewDiagnostics

**签名：** `sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` | `void` | 报告失败阶段。 |

## ViewLayerPolicy

**签名：** `sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `GetZOrder(IWorkflowComponent item)` | `int` | 返回 `0`。 |

## ViewLinkLayer

**签名：** `sealed class ViewLinkLayer : IViewLinkLayer<Panel, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `IsActive` | `bool` | 始终为 `false`。 |
| `Handles(IWorkflowComponent item)` | `bool` | 始终为 `false`；连线是池化视图。 |
| `Render(Panel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | 空实现。 |

## ViewMeasureHost

**签名：** `sealed class ViewMeasureHost : IViewMeasureHost<Panel, FrameworkElement, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Measure(Panel host, FrameworkElement view, IWorkflowComponent item)` | `void` | 执行一次测量。 |

## ViewLayoutTracker

`internal sealed class ViewLayoutTracker`（非公开）。它维护 `ViewContainer` 与 `ViewArranger` 共用的订阅表，使停用的视图退订排列器挂上的处理器。它不属于公开 API。

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
```

**预期结果：** 内部跟踪器在构造时共享；替换某一层的宿主需要自己保持成对。
