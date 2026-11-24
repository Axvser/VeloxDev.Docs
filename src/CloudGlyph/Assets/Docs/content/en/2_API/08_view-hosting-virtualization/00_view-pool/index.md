# View pool

A view pool consumes a visible-item collection and materialises one view per item. It keeps its own active map, promotes batches through a scheduler, and recycles views by runtime type rather than recreating them.

## IViewPoolPolicy

```csharp
public interface IViewPoolPolicy
{
    int BatchSize { get; }
    double FrameBudgetMilliseconds { get; }
    int MaxRecycledViewsPerType { get; }
}
```

| Member | Meaning |
|---|---|
| `BatchSize` | Maximum views one scheduled batch may materialise; values below one are treated as one. |
| `FrameBudgetMilliseconds` | Wall-clock budget per batch in milliseconds; zero or negative means no time limit. |
| `MaxRecycledViewsPerType` | Maximum recycled views kept per runtime type; zero or negative means unlimited. |

## ViewPoolOptions

```csharp
[Serializable]
public sealed class ViewPoolOptions
```

A serialisable profile for `AdaptiveViewPoolPolicy`. The parameterless constructor initialises every property.

| Property | Type | Default | Meaning |
|---|---|---:|---|
| `InitialBatchSize` | `int` | `64` | First batch size before feedback. |
| `InitialBudgetMilliseconds` | `double` | `8d` | First budget before feedback. |
| `MinimumBatchSize` | `int` | `16` | Smallest selectable batch size. |
| `MaximumBatchSize` | `int` | `4096` | Largest selectable batch size. |
| `InitialViewsPerMillisecond` | `double` | `0.25d` | Initial smoothed throughput. |
| `SmallPendingThreshold` | `int` | `256` | Pending count above which the medium budget applies. |
| `LargePendingThreshold` | `int` | `1024` | Pending count above which the large budget applies. |
| `SmallBudgetMilliseconds` | `double` | `8d` | Target budget for a small pending set. |
| `MediumBudgetMilliseconds` | `double` | `12d` | Target budget for a medium pending set. |
| `LargeBudgetMilliseconds` | `double` | `16d` | Target budget for a large pending set. |
| `MeasurementWeight` | `double` | `0.3d` | Weight of the newest throughput sample; 0 freezes, 1 uses only the newest. |
| `GrowThreshold` | `double` | `1.25d` | Factor above the current batch size that triggers growth. |
| `ShrinkThreshold` | `double` | `0.8d` | Factor below the current batch size that triggers shrinkage. |
| `MaxRecycledViewsPerType` | `int` | `0` | Unlimited when zero or negative. |

| Method | Description |
|---|---|
| `Clone()` | Returns an independent copy. |
| `Normalize()` | Clamps every field into the supported range: minimum batch at least 1, maximum at least the minimum, budgets at least 0.1, throughput at least 0.001, thresholds ordered, weight in `[0,1]`. |

## AdaptiveViewPoolPolicy

```csharp
public sealed class AdaptiveViewPoolPolicy : IViewPoolPolicy, IViewBatchFeedback
```

Starts at 64 items per batch and an 8 ms budget, then adjusts from measured throughput and pending count.

### Constructors

| Signature | Description |
|---|---|
| `AdaptiveViewPoolPolicy(int initialBatchSize = 64, double initialBudgetMilliseconds = 8d)` | Creates a policy from conservative initials; both values clamp to the supported range. |
| `AdaptiveViewPoolPolicy(ViewPoolOptions options)` | Creates from a profile; the profile is cloned and normalised. Throws `ArgumentNullException` for a null options object. |

### Members

| Member | Type | Description |
|---|---|---|
| `Options` | `ViewPoolOptions` | Detached clone of the construction profile; learned state is not included. |
| `BatchSize` | `int` | Current adaptive batch size. |
| `FrameBudgetMilliseconds` | `double` | Current target budget: 8 ms by default, 12 ms above 256 pending, 16 ms above 1024 pending. |
| `MaxRecycledViewsPerType` | `int` | Taken from the profile. |
| `FromOptions(ViewPoolOptions options)` | `static AdaptiveViewPoolPolicy` | Creates a policy from a profile. |
| `OnBatchCompleted(int processed, long elapsedTicks, int pending)` | `void` | Smooths views per millisecond, recomputes the batch for the target budget, and moves the batch only past the grow (1.25×) or shrink (0.8×) threshold. |

## ViewPoolCore

```csharp
public abstract class ViewPoolCore<THost, TView, TItem, TPriorityCore> : IDisposable
    where THost : class where TView : class where TItem : class
```

| Signature / member | Description |
|---|---|
| `protected ViewPoolCore(THost hostElement, IViewHost<THost,TView,TItem,TPriorityCore> host, INotifyCollectionChanged source)` | Starts tracking the visible collection, seeds the pending queue, and renders links once when the link layer is active. Throws `ArgumentNullException` for a null argument and `ArgumentException` when `source` is not enumerable. |
| `ActiveViewCount` | Items currently having a bound view. |
| `PendingViewCount` | Items waiting for a scheduled batch. |
| `CreatedViewCount` | Cumulative views created by the factory. |
| `ReusedViewCount` | Cumulative views taken from recycle pools. |
| `DestroyedViewCount` | Cumulative views destroyed because the policy refused to keep them. |
| `RecycledViewCount` | Views currently held for reuse, summed over per-type pools. |
| `Dispose()` | Idempotent; unsubscribes, recycles every active view, and clears pending, pools, and unsupported sets. |

## ViewPool

```csharp
public sealed class ViewPool<THost, TView, TItem, TPriorityCore>
    : ViewPoolCore<THost, TView, TItem, TPriorityCore>
    where THost : class where TView : class where TItem : class
```

| Signature | Description |
|---|---|
| `ViewPool(THost hostElement, IViewHost<THost,TView,TItem,TPriorityCore> host, INotifyCollectionChanged source)` | Default pool with no further specialisation. |

Generic parameters:

| Parameter | Meaning | WPF closure |
|---|---|---|
| `THost` | Element that owns the views. | `Panel` |
| `TView` | Element created per item. | `FrameworkElement` |
| `TItem` | Tracked item type. | `IWorkflowComponent` |
| `TPriorityCore` | Dispatcher-priority type, or `VeloxDev.Threading.NonPriority`. | `DispatcherPriority` |

## Notes

- A removed item is deactivated, detached, and returned to a per-type pool. Removal past `MaxRecycledViewsPerType` destroys the view instead of hiding it, because a hidden view stays rooted.
- A factory that returns `null` for a runtime type makes that verdict permanent for the pool's lifetime.
- `ViewPoolOptions.Normalize` is called by the policy; call it yourself only when you keep the profile for inspection.
