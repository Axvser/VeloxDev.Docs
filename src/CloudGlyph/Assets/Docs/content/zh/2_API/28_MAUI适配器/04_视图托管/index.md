# 视图托管

`ViewSourcePipeline` 背后的具体 MAUI 层。`ViewScheduler` 与 `ViewArranger` 可释放，并由管道拥有。

## 命名空间

`VeloxDev.WorkflowSystem.ViewHosting`，程序集 `VeloxDev.MAUI`。

## ViewFactory

**签名：** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, View>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewFactory(Layout host, DataTemplateSelector? selector)` | 公开构造函数 | 为一个布局创建视图。 |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | 始终为 `true`。 |
| `CreateView` | `View? CreateView(IWorkflowComponent item)` | 应用选择器；没有匹配时返回 `null`。 |

## ViewContainer

**签名：** `sealed class ViewContainer : IViewContainer<Layout, View, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewContainer()` | 公开构造函数 | 创建没有几何层可通知的容器。 |
| `ViewContainer(ViewArranger? arranger)` | 公开构造函数 | 视图离开池时释放 `arranger` 的条目订阅。 |
| `Attach(Layout host, View view)` | `void` | 把视图加入布局。 |
| `Detach(Layout host, View view)` | `void` | 移除视图。 |
| `Activate(View view, IWorkflowComponent item)` | `void` | 绑定条目状态。 |
| `Deactivate(View view)` | `void` | 释放绑定状态、隐藏视图并置于 `ZIndex −100`。 |
| `SetZOrder(View view, int zIndex)` | `void` | 设置 `ZIndex`。 |
| `Destroy(Layout host, View view)` | `void` | 移除池不愿保留的视图。 |

## ViewArranger

**签名：** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, View>, IDisposable`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewArranger(Layout host)` | 公开构造函数 | 为一个布局创建几何层。 |
| `Arrange(View view, IWorkflowComponent item)` | `void` | 应用条目几何并跟踪后续变化。 |
| `Dispose()` | `void` | 释放所有被跟踪的视图。 |

## ViewScheduler

**签名：** `sealed class ViewScheduler : IViewScheduler<NonPriority>, IDisposable`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewScheduler(Layout host)` | 公开构造函数 | 通过 `host` 的调度器投递批次；宿主为 null 时抛 `ArgumentNullException`。 |
| `BatchPriority` | `NonPriority` | `default`；MAUI 没有优先级概念。 |
| `Schedule(Action batch, NonPriority priority)` | `bool` | 排入一个批次；释放后返回 `false`。 |
| `Dispose()` | `void` | 停止定时器。 |

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

**签名：** `sealed class ViewLinkLayer : IViewLinkLayer<Layout, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `IsActive` | `bool` | 始终为 `true`。 |
| `Handles(IWorkflowComponent item)` | `bool` | `item is ILinkComponent`。 |
| `Render(Layout host, IReadOnlyList<IWorkflowComponent> items)` | `void` | 此处为空实现；覆盖层绘制连线。 |

## ViewMeasureHost

**签名：** `sealed class ViewMeasureHost : IViewMeasureHost<Layout, View, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Measure(Layout host, View view, IWorkflowComponent item)` | `void` | 执行一次测量。 |

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
```

**预期结果：** 管道自行创建这些层；替换 `ViewLinkLayer` 是改变覆盖层接管哪些条目类型的受支持方式。
