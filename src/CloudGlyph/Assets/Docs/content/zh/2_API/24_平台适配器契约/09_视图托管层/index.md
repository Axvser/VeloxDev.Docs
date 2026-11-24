# 视图托管层

池从不直接触碰平台 API。它向一个 `IViewHost` 索取九个小层；每个适配器提供自己的实现并暴露闭合组合。本页列出契约；具体类型在各适配器页。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## IViewHost

**签名：** `interface IViewHost<THost, TView, TItem, TPriorityCore>`，`THost/TView/TItem : class`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Factory` | `IViewFactory<TItem, TView>` | 把条目变成视图。 |
| `Container` | `IViewContainer<THost, TView, TItem>` | 拥有可视树成员关系与绑定状态。 |
| `Arranger` | `IViewArranger<TItem, TView>` | 应用条目几何。 |
| `Scheduler` | `IViewScheduler<TPriorityCore>` | 把批次送到宿主线程。 |
| `Diagnostics` | `IViewDiagnostics<TItem>` | 报告失败的视图操作。 |
| `PoolPolicy` | `IViewPoolPolicy` | 限制批次与回收视图。 |
| `LayerPolicy` | `IViewLayerPolicy<TItem>` | 决定 z 顺序。 |
| `LinkLayer` | `IViewLinkLayer<THost, TItem>` | 当平台不为每条连线建视图时自行渲染连线。 |
| `MeasureHost` | `IViewMeasureHost<THost, TView, TItem>` | 可选的排列后测量钩子。 |

## IViewFactory

**签名：** `interface IViewFactory<TItem, TView>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `WantsItem` | `bool WantsItem(TItem item)` | 该工厂是否处理此条目。 |
| `CreateView` | `TView? CreateView(TItem item)` | 创建视图；条目类型不受支持时返回 `null`。 |

## IViewContainer

**签名：** `interface IViewContainer<THost, TView, TItem>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Attach` | `void Attach(THost host, TView view)` | 把视图加入宿主。 |
| `Detach` | `void Detach(THost host, TView view)` | 移除视图。 |
| `Activate` | `void Activate(TView view, TItem item)` | 绑定条目状态。 |
| `Deactivate` | `void Deactivate(TView view)` | 释放绑定状态。 |
| `SetZOrder` | `void SetZOrder(TView view, int zIndex)` | 应用层序。 |
| `Destroy` | `void Destroy(THost host, TView view)` | 销毁池不愿保留的视图。 |

## IViewArranger

**签名：** `interface IViewArranger<TItem, TView>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Arrange` | `void Arrange(TView view, TItem item)` | 把条目几何应用到视图。 |

## IViewScheduler

**签名：** `interface IViewScheduler<TPriorityCore>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `BatchPriority` | `TPriorityCore` | 池用于物化批次的优先级。 |
| `Schedule` | `bool Schedule(Action batch, TPriorityCore priority)` | 排入一个批次；不得同步执行。调度器拒绝时返回 `false`。 |

`TPriorityCore` 是平台的调度优先级类型，或平台没有优先级概念时的 `NonPriority`（`readonly struct`，`VeloxDev.Core.Threading`）。

## IViewDiagnostics

**签名：** `interface IViewDiagnostics<TItem>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Failed` | `void Failed(TItem? item, ViewStage stage, Exception? exception)` | 报告失败的阶段。 |

## IViewLayerPolicy

**签名：** `interface IViewLayerPolicy<TItem>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `GetZOrder` | `int GetZOrder(TItem item)` | 一个条目的 z 顺序。 |

## IViewLinkLayer

**签名：** `interface IViewLinkLayer<THost, TItem>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `IsActive` | `bool` | 该层是否处理任何条目；`false` 让池完全跳过连线渲染。 |
| `Handles` | `bool Handles(TItem item)` | 该层是否从主池接管连线。 |
| `Render` | `void Render(THost host, IReadOnlyList<TItem> items)` | 绘制接管的条目；可见集合变化时调用，包括变为空时。 |

## IViewMeasureHost

**签名：** `interface IViewMeasureHost<THost, TView, TItem>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `Measure` | `void Measure(THost host, TView view, TItem item)` | 排列后的测量钩子。 |

## ViewStage

**签名：** `enum ViewStage`

| 成员 |
| --- |
| `Schedule`、`Link`、`Create`、`Activate`、`Attach`、`Arrange`、`Layer`、`Measure`、`Deactivate`、`Detach`、`Destroy` |

该枚举标明报告失败的管道层，使一个诊断接收器能路由所有阶段。

```csharp
sealed class Diagnostics : IViewDiagnostics<IWorkflowComponent>
{
    public void Failed(IWorkflowComponent? item, ViewStage stage, Exception? exception)
        => Console.WriteLine($"{stage}: {item?.GetType().Name}: {exception?.Message}");
}
```

**预期结果：** 对某条目类型抛异常的选择器只以 `ViewStage.Create` 报告一次；池在后续批次跳过该类型。
