# 视图托管

`ViewSourcePipeline` 背后的具体 Avalonia 层。它们公开，以便宿主替换某一层或组合自己的管道。

## 命名空间

`VeloxDev.WorkflowSystem.ViewHosting`，程序集 `VeloxDev.Avalonia`。

## ViewFactory

**签名：** `sealed class ViewFactory : IViewFactory<IWorkflowComponent, Control>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewFactory(Panel panel, IDataTemplate? templateSelector)` | 构造函数 | 为一个面板创建视图。 |
| `WantsItem` | `bool WantsItem(IWorkflowComponent item)` | 始终为 `true`。 |
| `CreateView` | `Control? CreateView(IWorkflowComponent item)` | 应用 `IDataTemplate`；没有匹配时返回 `null`。 |

## ViewContainer

**签名：** `sealed class ViewContainer : IViewContainer<Panel, Control, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Attach(Panel host, Control view)` | `void` | 把视图加入面板。 |
| `Detach(Panel host, Control view)` | `void` | 移除视图。 |
| `Activate(Control view, IWorkflowComponent item)` | `void` | 设置 `DataContext`。 |
| `Deactivate(Control view)` | `void` | 清空 `DataContext` 并隐藏视图。 |
| `SetZOrder(Control view, int zIndex)` | `void` | 空实现；条目模板自行绑定 z 顺序。 |
| `Destroy(Panel host, Control view)` | `void` | 移除池不愿保留的视图。 |

## ViewArranger

**签名：** `sealed class ViewArranger : IViewArranger<IWorkflowComponent, Control>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Arrange(Control view, IWorkflowComponent item)` | `void` | 空实现；Avalonia 模板自行绑定几何。 |

## ViewScheduler

**签名：** `sealed class ViewScheduler : IViewScheduler<DispatcherPriority>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `BatchPriority` | `DispatcherPriority` | `Background`。 |
| `Schedule(Action batch, DispatcherPriority priority)` | `bool` | 投递到 `Dispatcher.UIThread`；始终返回 `true`。 |

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

**签名：** `sealed class ViewMeasureHost : IViewMeasureHost<Panel, Control, IWorkflowComponent>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Measure(Panel host, Control view, IWorkflowComponent item)` | `void` | 对视图执行一次测量。 |

```csharp
var pipeline = new ViewSourcePipeline(canvas, selector, tree.GetHelper().VisibleItems);
```

**预期结果：** 管道无需额外配置即可组合这些层；替换 `ViewScheduler` 会改变承载物化批次的调度器优先级。
