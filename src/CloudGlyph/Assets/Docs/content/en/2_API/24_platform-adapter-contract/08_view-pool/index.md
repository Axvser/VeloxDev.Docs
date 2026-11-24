# View pool

The pool keeps one host element's views in sync with a visible-item collection: it materializes each item at most once, recycles views by runtime type, and dispatches creation in small scheduled batches. The pool is platform-neutral; an adapter closes the generic composition once and exposes the short type its users see.

## Namespace

`VeloxDev.WorkflowSystem` in `VeloxDev.Core`.

## ViewPoolCore

**Signature:** `abstract class ViewPoolCore<THost, TView, TItem, TPriorityCore> : IDisposable` with `THost/TView/TItem : class`

| Member | Type | Description |
| --- | --- | --- |
| `protected ViewPoolCore(THost hostElement, IViewHost<THost, TView, TItem, TPriorityCore> host, INotifyCollectionChanged source)` | constructor | Starts tracking `source`. Throws `ArgumentNullException` for a required null; `ArgumentException` when `source` is not enumerable. |
| `ActiveViewCount` | `int` | Items that currently have a bound view. |
| `PendingViewCount` | `int` | Items waiting for a scheduled batch. |
| `CreatedViewCount` / `ReusedViewCount` / `DestroyedViewCount` | `int` | Cumulative factory-created, recycled and destroyed counts. |
| `RecycledViewCount` | `int` | Views currently held for reuse. |
| `Dispose()` | `void` | Stops tracking and releases every active view. |

The pool reacts to `Add`, `Remove`, `Replace` and `Reset` notifications; `Move` is ignored because view identity is the item reference. Each batch stops at `poolPolicy.BatchSize` or `FrameBudgetMilliseconds`, then schedules the remainder on the next dispatcher turn.

## ViewPool

**Signature:** `sealed class ViewPool<THost, TView, TItem, TPriorityCore> : ViewPoolCore<...>`

| Member | Signature | Description |
| --- | --- | --- |
| `ViewPool(THost hostElement, IViewHost<THost, TView, TItem, TPriorityCore> host, INotifyCollectionChanged source)` | constructor | The default pool with no further specialization. |

## ViewSourcePipelineCore

**Signature:** `class ViewSourcePipelineCore<THost, TView, TItem, TPriorityCore, TFactory, TContainer, TArranger, TScheduler, TDiagnostics> : ViewHostCore<...>, IDisposable`

The nine-argument composition point: it closes one factory, container, arranger, scheduler and diagnostics over one host and starts the shared pool. An adapter derives once and exposes the closed type.

| Member | Type | Description |
| --- | --- | --- |
| `ViewSourcePipelineCore(THost hostElement, TFactory factory, TContainer container, TArranger arranger, TScheduler scheduler, TDiagnostics diagnostics, INotifyCollectionChanged source, IViewPoolPolicy? poolPolicy = null, IViewLayerPolicy<TItem>? layerPolicy = null, IViewLinkLayer<THost, TItem>? linkLayer = null, IViewMeasureHost<THost, TView, TItem>? measureHost = null)` | constructor | Builds the layers and starts `Pool`. |
| `Pool` | `ViewPool<THost, TView, TItem, TPriorityCore>` | The running pool; dispose the pipeline to stop it. |
| `Dispose()` | `virtual void` | Disposes the pool. |

### ViewHostCore

**Signature:** `abstract class ViewHostCore<THost, TView, TItem, TPriorityCore>`

The base of `ViewSourcePipelineCore`; it exposes the composed layers the pool consumes.

| Member | Type |
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

**Signature:** `interface IViewPoolPolicy`

| Member | Type | Description |
| --- | --- | --- |
| `BatchSize` | `int` | Maximum views one batch may materialize; values below one are treated as one. |
| `FrameBudgetMilliseconds` | `double` | Wall-clock budget for one batch; zero or negative means no limit. |
| `MaxRecycledViewsPerType` | `int` | Recycled views kept per runtime type; zero or negative means unlimited. |

## AdaptiveViewPoolPolicy

**Signature:** `sealed class AdaptiveViewPoolPolicy : IViewPoolPolicy, IViewBatchFeedback`

| Member | Signature | Description |
| --- | --- | --- |
| `AdaptiveViewPoolPolicy(int initialBatchSize = 64, double initialBudgetMilliseconds = 8d)` | constructor | Conservative first values. |
| `AdaptiveViewPoolPolicy(ViewPoolOptions options)` | constructor | Copies and normalizes a profile. Throws `ArgumentNullException` for null. |
| `Options` | `ViewPoolOptions` | A detached copy of the profile; changing it does not retune the running policy. |
| `FromOptions(ViewPoolOptions options)` | `static AdaptiveViewPoolPolicy` | Creates a policy from a profile. |
| `BatchSize` / `FrameBudgetMilliseconds` / `MaxRecycledViewsPerType` | `int` / `double` / `int` | The current tuning. |
| `OnBatchCompleted(int processed, long elapsedTicks, int pending)` | `void` | Updates the smoothed throughput and the target budget. |

The target budget is 8 ms for a small pending set, 12 ms above `SmallPendingThreshold` (256) and 16 ms above `LargePendingThreshold` (1024). This is per-process feedback, not a machine fingerprint; it needs no calibration.

## ViewPoolOptions

**Signature:** `[Serializable] sealed class ViewPoolOptions`

| Property | Default | Meaning |
| --- | --- | --- |
| `InitialBatchSize` | `64` | First batch size before feedback. |
| `InitialBudgetMilliseconds` | `8` | First time budget. |
| `MinimumBatchSize` / `MaximumBatchSize` | `16` / `4096` | Batch-size bounds. |
| `InitialViewsPerMillisecond` | `0.25` | Initial smoothed throughput. |
| `SmallPendingThreshold` / `LargePendingThreshold` | `256` / `1024` | Pending counts above which the medium/large budget applies. |
| `SmallBudgetMilliseconds` / `MediumBudgetMilliseconds` / `LargeBudgetMilliseconds` | `8` / `12` / `16` | Target budgets. |
| `MeasurementWeight` | `0.3` | Weight of the newest sample; `0` freezes the estimate. |
| `GrowThreshold` / `ShrinkThreshold` | `1.25` / `0.8` | Ratios that trigger batch-size changes. |
| `MaxRecycledViewsPerType` | `0` | Recycled views per type; zero or negative means unlimited. |
| `Clone()` | method | Independent copy. |
| `Normalize()` | method | Clamps every field into the executable range. |

## IViewBatchFeedback

**Signature:** `interface IViewBatchFeedback`

| Member | Signature | Description |
| --- | --- | --- |
| `OnBatchCompleted(int processed, long elapsedTicks, int pending)` | `void` | Called after a batch so a policy can retune. |

```csharp
var policy = new AdaptiveViewPoolPolicy(initialBatchSize: 32);
Console.WriteLine($"{policy.BatchSize} {policy.FrameBudgetMilliseconds}");

var options = new ViewPoolOptions { InitialBatchSize = 128, MaxRecycledViewsPerType = 64 };
options.Normalize();
var tuned = new AdaptiveViewPoolPolicy(options);
```

**Expected result:** a new policy starts at the values it was given, and `Normalize` clamps a hand-edited profile into the executable range before the policy uses it. An adapter closes `ViewSourcePipelineCore` once and hands the resulting pool an `IViewPoolPolicy`.
