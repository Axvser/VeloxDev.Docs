# 视图池

视图池消费一个可见项集合，为每一项物化一个视图。它维护自己的活动映射，通过调度器推进批次，并按运行时类型回收视图，而不是重新创建。

## IViewPoolPolicy

```csharp
public interface IViewPoolPolicy
{
    int BatchSize { get; }
    double FrameBudgetMilliseconds { get; }
    int MaxRecycledViewsPerType { get; }
}
```

| 成员 | 含义 |
|---|---|
| `BatchSize` | 一个已调度批次最多物化的视图数；小于 1 时按 1 处理。 |
| `FrameBudgetMilliseconds` | 每批的墙钟预算（毫秒）；零或负数表示不限时。 |
| `MaxRecycledViewsPerType` | 每种运行时类型最多保留的回收视图数；零或负数表示不限。 |

## ViewPoolOptions

```csharp
[Serializable]
public sealed class ViewPoolOptions
```

`AdaptiveViewPoolPolicy` 的可序列化配置。无参构造函数初始化每个属性。

| 属性 | 类型 | 默认 | 含义 |
|---|---|---:|---|
| `InitialBatchSize` | `int` | `64` | 反馈前的首批大小。 |
| `InitialBudgetMilliseconds` | `double` | `8d` | 反馈前的初始预算。 |
| `MinimumBatchSize` | `int` | `16` | 可选最小批大小。 |
| `MaximumBatchSize` | `int` | `4096` | 可选最大批大小。 |
| `InitialViewsPerMillisecond` | `double` | `0.25d` | 初始平滑吞吐。 |
| `SmallPendingThreshold` | `int` | `256` | 超过该待处理数时应用中等预算。 |
| `LargePendingThreshold` | `int` | `1024` | 超过该待处理数时应用大预算。 |
| `SmallBudgetMilliseconds` | `double` | `8d` | 小待处理集的目标预算。 |
| `MediumBudgetMilliseconds` | `double` | `12d` | 中等待处理集的目标预算。 |
| `LargeBudgetMilliseconds` | `double` | `16d` | 大待处理集的目标预算。 |
| `MeasurementWeight` | `double` | `0.3d` | 最新吞吐样本的权重；0 冻结，1 只用最新。 |
| `GrowThreshold` | `double` | `1.25d` | 超过当前批大小多少倍时增长。 |
| `ShrinkThreshold` | `double` | `0.8d` | 低于当前批大小多少倍时收缩。 |
| `MaxRecycledViewsPerType` | `int` | `0` | 零或负数表示不限。 |

| 方法 | 说明 |
|---|---|
| `Clone()` | 返回独立副本。 |
| `Normalize()` | 把每个字段钳制到支持范围：最小批至少 1、最大不小于最小、预算至少 0.1、吞吐至少 0.001、阈值有序、权重在 `[0,1]`。 |

## AdaptiveViewPoolPolicy

```csharp
public sealed class AdaptiveViewPoolPolicy : IViewPoolPolicy, IViewBatchFeedback
```

从每批 64 项、8 ms 预算开始，再根据实测吞吐与待处理数调整。

### 构造函数

| 签名 | 说明 |
|---|---|
| `AdaptiveViewPoolPolicy(int initialBatchSize = 64, double initialBudgetMilliseconds = 8d)` | 用保守初值创建；两个值都会钳制到支持范围。 |
| `AdaptiveViewPoolPolicy(ViewPoolOptions options)` | 由配置创建；配置会被克隆并规范化。`options` 为 null 时抛 `ArgumentNullException`。 |

### 成员

| 成员 | 类型 | 说明 |
|---|---|---|
| `Options` | `ViewPoolOptions` | 构造配置的独立副本；不含学习到的状态。 |
| `BatchSize` | `int` | 当前自适应批大小。 |
| `FrameBudgetMilliseconds` | `double` | 当前目标预算：默认 8 ms，待处理超过 256 时 12 ms，超过 1024 时 16 ms。 |
| `MaxRecycledViewsPerType` | `int` | 取自配置。 |
| `FromOptions(ViewPoolOptions options)` | `static AdaptiveViewPoolPolicy` | 由配置创建策略。 |
| `OnBatchCompleted(int processed, long elapsedTicks, int pending)` | `void` | 平滑每毫秒视图数，按目标预算重算批次，并且只有越过增长（1.25×）或收缩（0.8×）阈值时才改变批大小。 |

## ViewPoolCore

```csharp
public abstract class ViewPoolCore<THost, TView, TItem, TPriorityCore> : IDisposable
    where THost : class where TView : class where TItem : class
```

| 签名 / 成员 | 说明 |
|---|---|
| `protected ViewPoolCore(THost hostElement, IViewHost<THost,TView,TItem,TPriorityCore> host, INotifyCollectionChanged source)` | 开始跟踪可见集合、填充待处理队列，并在链接层激活时渲染一次连线。参数为 null 时抛 `ArgumentNullException`；`source` 不可枚举时抛 `ArgumentException`。 |
| `ActiveViewCount` | 当前已绑定视图的项数。 |
| `PendingViewCount` | 等待调度批次的项数。 |
| `CreatedViewCount` | 工厂累计创建的视图数。 |
| `ReusedViewCount` | 从回收池累计取得的视图数。 |
| `DestroyedViewCount` | 因策略拒绝保留而销毁的累计视图数。 |
| `RecycledViewCount` | 当前保留待复用的视图数，按类型求和。 |
| `Dispose()` | 幂等；取消订阅、回收所有活动视图，并清空待处理、池与不支持类型集合。 |

## ViewPool

```csharp
public sealed class ViewPool<THost, TView, TItem, TPriorityCore>
    : ViewPoolCore<THost, TView, TItem, TPriorityCore>
    where THost : class where TView : class where TItem : class
```

| 签名 | 说明 |
|---|---|
| `ViewPool(THost hostElement, IViewHost<THost,TView,TItem,TPriorityCore> host, INotifyCollectionChanged source)` | 默认池，没有额外特化。 |

泛型参数：

| 参数 | 含义 | WPF 闭合 |
|---|---|---|
| `THost` | 拥有视图的元素。 | `Panel` |
| `TView` | 每项创建的元素。 | `FrameworkElement` |
| `TItem` | 跟踪的项类型。 | `IWorkflowComponent` |
| `TPriorityCore` | 调度器优先级类型，或 `VeloxDev.Threading.NonPriority`。 | `DispatcherPriority` |

## 说明

- 被移除的项会停用、分离并回到按类型划分的池。超过 `MaxRecycledViewsPerType` 时销毁视图而不是隐藏，因为隐藏的视图仍被宿主根引用。
- 工厂对某个运行时类型返回 `null`，该判断会在池的整个生命周期内被记住。
- `ViewPoolOptions.Normalize` 由策略调用；只有在保留配置用于检查时才需要自行调用。
