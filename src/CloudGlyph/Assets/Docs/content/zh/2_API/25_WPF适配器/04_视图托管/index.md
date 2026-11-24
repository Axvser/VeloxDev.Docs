# 视图托管

`ViewSourcePipeline` 背后的具体 WPF 层。它们公开，以便宿主替换某一层或组合自己的管道；多数用户不会直接命名它们。

## 命名空间

`VeloxDev.WorkflowSystem.ViewHosting`，程序集 `VeloxDev.WPF`。

## ViewFactory

**签名：** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, FrameworkElement>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewFactory(Panel panel, DataTemplateSelector? templateSelector)` | 构造函数 | 为一个面板创建视图。 |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | 始终为 `true`。 |
| `CreateView` | `FrameworkElement? CreateView(IWorkflowComponent item)` | 应用选择器；没有模板匹配时返回 `null`。 |

## ViewContainer

**签名：** `sealed class ViewContainer : IViewContainer<Panel, FrameworkElement, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Attach(Panel host, FrameworkElement view)` | `void` | 把视图加入面板子元素。 |
| `Detach(Panel host, FrameworkElement view)` | `void` | 移除视图。 |
| `Activate(FrameworkElement view, IWorkflowComponent item)` | `void` | 把 `DataContext` 设为条目。 |
| `Deactivate(FrameworkElement view)` | `void` | 清空 `DataContext` 并折叠视图。 |
| `SetZOrder(FrameworkElement view, int zIndex)` | `void` | 空实现；条目模板自行绑定 `Panel.ZIndex`。 |
| `Destroy(Panel host, FrameworkElement view)` | `void` | 释放并移除池不愿保留的视图。 |

## ViewArranger

**签名：** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, FrameworkElement>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Arrange(FrameworkElement view, IWorkflowComponent item)` | `void` | 空实现；条目模板自行绑定 `Canvas.Left`、`Canvas.Top` 与尺寸。 |

## ViewScheduler

**签名：** `sealed class ViewScheduler : IViewScheduler<DispatcherPriority>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewScheduler(Dispatcher dispatcher)` | 构造函数 | 在给定调度器上调度。 |
| `BatchPriority` | `DispatcherPriority` | `Background`。 |
| `Schedule(Action batch, DispatcherPriority priority)` | `bool` | 通过 `BeginInvoke` 投递；始终返回 `true`。 |

## ViewDiagnostics

**签名：** `sealed class ViewDiagnostics : IViewDiagnostics<IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)` | `void` | 把失败阶段报告到调试/跟踪输出。 |

## ViewLayerPolicy

**签名：** `sealed class ViewLayerPolicy : IViewLayerPolicy<IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `GetZOrder(IWorkflowComponent item)` | `int` | 返回 `0`；WPF 池把层叠交给模板。 |

## ViewLinkLayer

**签名：** `sealed class ViewLinkLayer : IViewLinkLayer<Panel, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `IsActive` | `bool` | 始终为 `false`。 |
| `Handles(IWorkflowComponent item)` | `bool` | 始终为 `false`；WPF 上连线是池化视图。 |
| `Render(Panel host, IReadOnlyList<IWorkflowComponent> items)` | `void` | 空实现。 |

## ViewMeasureHost

**签名：** `sealed class ViewMeasureHost : IViewMeasureHost<Panel, FrameworkElement, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Measure(Panel host, FrameworkElement view, IWorkflowComponent item)` | `void` | 对刚排列的视图执行一次测量。 |

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
var diagnostics = new ViewDiagnostics();
```

**预期结果：** 把 `ViewLinkLayer` 替换为 `Handles` 接受 `ILinkComponent` 的实现，会把连线从池化视图转交给该层。
