# 视图池

视图池让一个宿主元素的视图与可见条目集合保持同步：每个条目最多物化一次，按运行时类型回收视图，并把创建分到小批次里调度。池本身与平台无关；适配器闭合一次泛型组合，并暴露用户看到的短类型。

## 命名空间

`VeloxDev.Core` 中的 `VeloxDev.WorkflowSystem`。

## ViewPoolCore

**签名：** `abstract class ViewPoolCore<THost, TView, TItem, TPriorityCore> : IDisposable`，`THost/TView/TItem : class`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `protected ViewPoolCore(THost hostElement, IViewHost<THost, TView, TItem, TPriorityCore> host, INotifyCollectionChanged source)` | 构造函数 | 开始跟踪 `source`。必需参数为 null 时抛 `ArgumentNullException`；`source` 不可枚举时抛 `ArgumentException`。 |
| `ActiveViewCount` | `int` | 当前已绑定视图的条目数。 |
| `PendingViewCount` | `int` | 等待调度批次的条目数。 |
| `CreatedViewCount` / `ReusedViewCount` / `DestroyedViewCount` | `int` | 累计创建、回收复用、销毁的数量。 |
| `RecycledViewCount` | `int` | 当前保留待复用的视图数。 |
| `Dispose()` | `void` | 停止跟踪并释放所有活动视图。 |

池响应 `Add`、`Remove`、`Replace`、`Reset` 通知；忽略 `Move`，因为视图身份是条目引用。每批次在 `poolPolicy.BatchSize` 或 `FrameBudgetMilliseconds` 处停止，再把剩余工作调度到下一个调度器轮次。

## ViewPool

**签名：** `sealed class ViewPool<THost, TView, TItem, TPriorityCore> : ViewPoolCore<...>`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `ViewPool(THost hostElement, IViewHost<THost, TView, TItem, TPriorityCore> host, INotifyCollectionChanged source)` | 构造函数 | 不再特化的默认池。 |

## ViewSourcePipelineCore

**签名：** `class ViewSourcePipelineCore<THost, TView, TItem, TPriorityCore, TFactory, TContainer, TArranger, TScheduler, TDiagnostics> : ViewHostCore<...>, IDisposable`

九参数组合点：把一个工厂、容器、排列器、调度器与诊断层闭合到一个宿主上，并启动共享池。适配器派生一次并暴露闭合类型。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `ViewSourcePipelineCore(THost hostElement, TFactory factory, TContainer container, TArranger arranger, TScheduler scheduler, TDiagnostics diagnostics, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null, IViewLayerPolicy<TItem>? layerPolicy = null, IViewLinkLayer<THost, TItem>? linkLayer = null, IViewMeasureHost<THost, TView, TItem>? measureHost = null)` | 构造函数 | 构建各层并启动 `Pool`。 |
| `Pool` | `ViewPool<THost, TView, TItem, TPriorityCore>` | 运行中的池；释放管道即停止它。 |
| `Dispose()` | `virtual void` | 释放池。 |

### ViewHostCore

**签名：** `abstract class ViewHostCore<THost, TView, TItem, TPriorityCore>`

`ViewSourcePipelineCore` 的基类；暴露池所消费的组合层。

| 成员 | 类型 |
| --- | --- |
| `Factory` | `IViewFactory<TItem, TView>` |
| `Container` | `IViewContainer<THost, TView, TItem>` |
| `Arranger` | `IViewArranger<TItem, TView>` |
| `Scheduler` | `IViewScheduler<TPriorityCore>` |
| `Diagnostics` | `IViewDiagnostics<TItem>` |
| `PoolPolicy` | `IViewPoolPolicy` |
| `LayerPolicy` | `IViewLayerPolicy<TItem>` |
| `LinkLayer` | `IViewLinkLayer<THost, TItem>` |
| `MeasureHost` | `IViewMeasureHost<THost, TView, TItem>` |

## IViewPoolPolicy

**签名：** `interface IViewPoolPolicy`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `BatchSize` | `int` | 一个批次最多物化的视图数；小于一按一处理。 |
| `FrameBudgetMilliseconds` | `double` | 一个批次的墙钟预算；零或负表示不限。 |
| `MaxRecycledViewsPerType` | `int` | 每种运行时类型保留的回收视图数；零或负表示不限。 |

## AdaptiveViewPoolPolicy

**签名：** `sealed class AdaptiveViewPoolPolicy : IViewPoolPolicy, IViewBatchFeedback`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `AdaptiveViewPoolPolicy(int initialBatchSize = 64, double initialBudgetMilliseconds = 8d)` | 构造函数 | 保守的初始值。 |
| `AdaptiveViewPoolPolicy(ViewPoolOptions options)` | 构造函数 | 复制并规范化配置。null 时抛 `ArgumentNullException`。 |
| `Options` | `ViewPoolOptions` | 配置的独立副本；修改它不会重新调优运行中的策略。 |
| `FromOptions(ViewPoolOptions options)` | `static AdaptiveViewPoolPolicy` | 由配置创建策略。 |
| `BatchSize` / `FrameBudgetMilliseconds` / `MaxRecycledViewsPerType` | `int` / `double` / `int` | 当前调优值。 |
| `OnBatchCompleted(int processed, long elapsedTicks, int pending)` | `void` | 更新平滑吞吐与目标预算。 |

目标预算在待处理集较小时为 8 ms，超过 `SmallPendingThreshold`（256）为 12 ms，超过 `LargePendingThreshold`（1024）为 16 ms。这是进程内反馈，不是机器指纹，无需校准。

## ViewPoolOptions

**签名：** `[Serializable] sealed class ViewPoolOptions`

| 属性 | 默认值 | 含义 |
| --- | --- | --- |
| `InitialBatchSize` | `64` | 反馈前的首批大小。 |
| `InitialBudgetMilliseconds` | `8` | 首个时间预算。 |
| `MinimumBatchSize` / `MaximumBatchSize` | `16` / `4096` | 批次大小边界。 |
| `InitialViewsPerMillisecond` | `0.25` | 初始平滑吞吐。 |
| `SmallPendingThreshold` / `LargePendingThreshold` | `256` / `1024` | 超过后分别采用中/大预算的待处理数。 |
| `SmallBudgetMilliseconds` / `MediumBudgetMilliseconds` / `LargeBudgetMilliseconds` | `8` / `12` / `16` | 目标预算。 |
| `MeasurementWeight` | `0.3` | 最新样本权重；`0` 冻结估计。 |
| `GrowThreshold` / `ShrinkThreshold` | `1.25` / `0.8` | 触发批次大小变化的比值。 |
| `MaxRecycledViewsPerType` | `0` | 每种类型回收数；零或负表示不限。 |
| `Clone()` | 方法 | 独立副本。 |
| `Normalize()` | 方法 | 把每个字段钳制到可执行范围。 |

## IViewBatchFeedback

**签名：** `interface IViewBatchFeedback`

| 成员 | 签名 | 说明 |
| --- | --- | --- |
| `OnBatchCompleted(int processed, long elapsedTicks, int pending)` | `void` | 一个批次结束后调用，供策略重新调优。 |

```csharp
var policy = new AdaptiveViewPoolPolicy(initialBatchSize: 32);
Console.WriteLine($"{policy.BatchSize} {policy.FrameBudgetMilliseconds}");

var options = new ViewPoolOptions { InitialBatchSize = 128, MaxRecycledViewsPerType = 64 };
options.Normalize();
var tuned = new AdaptiveViewPoolPolicy(options);
```

**预期结果：** 新策略从给定值开始；`Normalize` 会在策略使用手改配置前把它钳制到可执行范围。适配器闭合一次 `ViewSourcePipelineCore`，并把生成的池交给一个 `IViewPoolPolicy`。
