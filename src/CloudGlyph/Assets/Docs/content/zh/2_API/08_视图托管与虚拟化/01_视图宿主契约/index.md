# 视图宿主契约

池不认识任何平台。它组合九个窄层，每层一个接口，适配器为每层提供一个实现。`IViewPoolPolicy` 随[视图池](../00_视图池/index.md)一起说明。

## 层接口

以下签名都在 `VeloxDev.WorkflowSystem`，均为 public。

### IViewFactory<TItem, TView>

```csharp
public interface IViewFactory<TItem, TView> where TItem : class where TView : class
{
    bool WantsItem(TItem item);
    TView? CreateView(TItem item);
}
```

`WantsItem` 决定池是否要物化该项（由覆盖层绘制的连线可以返回 `false`）。`CreateView` 在没有匹配模板时返回 `null`；池按运行时类型把这个答案缓存到销毁为止。

### IViewContainer<THost, TView, TItem>

```csharp
public interface IViewContainer<THost, TView, TItem>
    where THost : class where TView : class where TItem : class
{
    void Attach(THost host, TView view);
    void Detach(THost host, TView view);
    void Activate(TView view, TItem item);
    void Deactivate(TView view);
    void SetZOrder(TView view, int zIndex);
    void Destroy(THost host, TView view);
}
```

| 方法 | 契约 |
|---|---|
| `Attach` | 让视图成为宿主的子元素；必须幂等。 |
| `Detach` | 隐藏或移除被回收的视图；之后可能再次交给池。 |
| `Activate` | 绑定项并让视图可见。 |
| `Deactivate` | 释放上一个项并隐藏视图，但不销毁。 |
| `SetZOrder` | 应用 z 序；没有 z 序的平台是空操作。 |
| `Destroy` | 永久移除策略拒绝保留的视图。 |

### IViewArranger<TItem, TView>

```csharp
public interface IViewArranger<TItem, TView> where TItem : class where TView : class
{
    void Arrange(TView view, TItem item);
}
```

把项的几何写到视图上，在 `Attach` 之后调用，所以命令式平台可以假定视图已在树中。

### IViewScheduler<TPriorityCore>

```csharp
public interface IViewScheduler<TPriorityCore>
{
    TPriorityCore BatchPriority { get; }
    bool Schedule(Action batch, TPriorityCore priority);
}
```

`Schedule` 把一个批次投递到宿主线程，绝不能同步调用。被拒绝时返回 `false`；池会在下一次可见集变化时重试。

### IViewDiagnostics<TItem>

```csharp
public interface IViewDiagnostics<TItem> where TItem : class
{
    void Failed(TItem? item, ViewStage stage, Exception? exception);
}
```

报告失败或被拒绝的操作。失败与具体项无关时 `item` 为 null；没有异常的拒绝 `exception` 为 null。实现必须廉价且不得抛异常。

### IViewLayerPolicy<TItem>

```csharp
public interface IViewLayerPolicy<TItem> where TItem : class
{
    int GetZOrder(TItem item);
}
```

### IViewLinkLayer<THost, TItem>

```csharp
public interface IViewLinkLayer<THost, TItem> where THost : class where TItem : class
{
    bool IsActive { get; }
    bool Handles(TItem item);
    void Render(THost host, IReadOnlyList<TItem> items);
}
```

`IsActive` 为 false 时池像普通项一样拥有连线。为 true 且 `Handles` 返回 true 时，该层自己绘制项；每次可见集变化都会调用 `Render`（包括空集），且它不得修改集合。

### IViewMeasureHost<THost, TView, TItem>

```csharp
public interface IViewMeasureHost<THost, TView, TItem>
    where THost : class where TView : class where TItem : class
{
    void Measure(THost host, TView view, TItem item);
}
```

可选的摆位后测量钩子；池不会等待它。空实现是合法的。

### IViewBatchFeedback

```csharp
public interface IViewBatchFeedback
{
    void OnBatchCompleted(int processed, long elapsedTicks, int pending);
}
```

在批次执行后立刻于宿主线程报告；实现必须廉价且不分配。

### IViewHost<THost, TView, TItem, TPriorityCore>

```csharp
public interface IViewHost<THost, TView, TItem, TPriorityCore>
    where THost : class where TView : class where TItem : class
{
    IViewFactory<TItem, TView> Factory { get; }
    IViewContainer<THost, TView, TItem> Container { get; }
    IViewArranger<TItem, TView> Arranger { get; }
    IViewScheduler<TPriorityCore> Scheduler { get; }
    IViewDiagnostics<TItem> Diagnostics { get; }
    IViewPoolPolicy PoolPolicy { get; }
    IViewLayerPolicy<TItem> LayerPolicy { get; }
    IViewLinkLayer<THost, TItem> LinkLayer { get; }
    IViewMeasureHost<THost, TView, TItem> MeasureHost { get; }
}
```

## ViewStage

```csharp
public enum ViewStage
{
    Schedule = 0, Link = 1, Create = 2, Activate = 3, Attach = 4,
    Arrange = 5, Layer = 6, Measure = 7, Deactivate = 8, Detach = 9, Destroy = 10
}
```

| 成员 | 命名的失败 |
|---|---|
| `Schedule` | 调度器拒绝了批次。 |
| `Link` | 链接层无法渲染。 |
| `Create` | 工厂无法创建视图。 |
| `Activate` | 容器无法绑定或显示视图。 |
| `Attach` | 容器无法挂接视图。 |
| `Arrange` | 摆位器无法应用几何。 |
| `Layer` | 层策略无法应用 z 序。 |
| `Measure` | 测量宿主无法测量。 |
| `Deactivate` | 容器无法释放或隐藏。 |
| `Detach` | 容器无法分离。 |
| `Destroy` | 容器无法销毁。 |

## ViewHostCore

```csharp
public abstract class ViewHostCore<THost, TView, TItem, TPriorityCore>
    : IViewHost<THost, TView, TItem, TPriorityCore>
    where THost : class where TView : class where TItem : class
```

| 签名 / 成员 | 说明 |
|---|---|
| `protected ViewHostCore(IViewFactory<TItem,TView> factory, IViewContainer<THost,TView,TItem> container, IViewArranger<TItem,TView> arranger, IViewScheduler<TPriorityCore> scheduler, IViewDiagnostics<TItem>? diagnostics = null, IViewPoolPolicy? poolPolicy = null, IViewLayerPolicy<TItem>? layerPolicy = null, IViewLinkLayer<THost,TItem>? linkLayer = null, IViewMeasureHost<THost,TView,TItem>? measureHost = null)` | 组合各层。必需层为 null 时抛 `ArgumentNullException`。 |
| `Factory`、`Container`、`Arranger`、`Scheduler` | 四个必需层。 |
| `Diagnostics` | 默认是内部空诊断。 |
| `PoolPolicy` | 默认内部策略：批 3、无预算、不限回收。 |
| `LayerPolicy` | 默认恒为 z 序 0。 |
| `LinkLayer` | 默认不激活。 |
| `MeasureHost` | 默认空操作。 |

## ViewSourcePipelineCore

```csharp
public class ViewSourcePipelineCore<THost, TView, TItem, TPriorityCore,
    TFactory, TContainer, TArranger, TScheduler, TDiagnostics>
    : ViewHostCore<THost, TView, TItem, TPriorityCore>, IDisposable
    where THost : class where TView : class where TItem : class
    where TFactory : class, IViewFactory<TItem,TView>
    where TContainer : class, IViewContainer<THost,TView,TItem>
    where TArranger : class, IViewArranger<TItem,TView>
    where TScheduler : class, IViewScheduler<TPriorityCore>
    where TDiagnostics : class, IViewDiagnostics<TItem>
```

| 成员 | 说明 |
|---|---|
| `ViewSourcePipelineCore(THost hostElement, TFactory factory, TContainer container, TArranger arranger, TScheduler scheduler, TDiagnostics diagnostics, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null, IViewLayerPolicy<TItem>? layerPolicy = null, IViewLinkLayer<THost,TItem>? linkLayer = null, IViewMeasureHost<THost,TView,TItem>? measureHost = null)` | 组合层实例并启动共享池。 |
| `Pool` | 运行中的 `ViewPool<THost,TView,TItem,TPriorityCore>`。销毁管线即可停止它。 |
| `Dispose()` | 停止跟踪并释放所有活动视图。虚方法。 |

## 说明

- Core 默认值刻意保守。需要自适应分批的适配器传入 `AdaptiveViewPoolPolicy`。
- `IViewScheduler.Schedule` 的投递是整条管线里唯一的线程边界。
- 失败通过 `Diagnostics.Failed` 报告；批次其余部分继续。
