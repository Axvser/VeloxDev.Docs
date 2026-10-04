# Registry, Snapshot and Pooling

The three structures that bound the feature's memory and keep its hot path allocation-free.

Let $C$ be the number of channels created in the process, $N$ the behaviours on one channel, and $K$ the pool capacity (`DEFAULT_OBJECT_POOL_SIZE` = 50).

## Channel registry

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 1017-1030)
private static readonly ConcurrentDictionary<string, LoopChannel> _channels = new();

private static LoopChannel GetOrCreateChannel(string name)
{
    return _channels.GetOrAdd(name, n =>
    {
        var ch = new LoopChannel(n);
        // …four event forwarders…
        return ch;
    });
}
```

| Operation | Expected time | Space |
|---|---|---|
| `GetOrCreateChannel` (existing name) | $O(1)$ hash probe | — |
| `GetOrCreateChannel` (new name) | $O(1)$ + channel construction | $O(1)$ per channel |
| Status query (`IsRunning`, `Bus`, …) | $O(1)$ `TryGetValue` | — |
| `ChannelNames` | $O(C)$ to enumerate | — |

The dictionary is lock-free on the read path, which matters because the status queries run at display frequency in the demo: `MainWindow.xaml.cs` polls all thirteen of them every 33 ms. The registry is never pruned, so its space is $O(C)$ and $C$ only grows — a named channel is a process-lifetime object.

Channel construction is the one expensive part of `GetOrCreateChannel`, and it happens once per name: `TimerCore.CreateTimeSource<ITimeSourceControl>()` plus two samplers, three `ObjectPool` instances in the `LoopChannel` constructor (`_frameEventArgsPool`, `_configRequestPool`, `_wrapperPool`, declared at lines 152-154; constructor at 160-167), one `CancellationTokenSource`, and four delegate subscriptions.

## Copy-on-write snapshot

| Operation | Time | Space |
|---|---|---|
| `GetCachedWrappers` hit | $O(1)$ | — |
| `RebuildCachedWrappers` — fill | $O(N)$ | $O(N)$ new array |
| `RebuildCachedWrappers` — insertion sort | $O(N)$ when already ordered, $O(N^2)$ worst case | $O(1)$ |
| `RebuildCachedWrappers` — `Array.Resize` down | $O(N)$ copy, only when some wrapper was skipped | $O(N)$ |
| Dispatch sweep read | $O(1)$ — one `volatile` array reference | — |

The sort is the only super-linear term in the feature, and it is contained on purpose:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 883-894)
// Insertion sort — behavior counts are usually small, avoiding LINQ allocations
for (int i = 1; i < idx; i++)
{
    var key = arr[i];
    int j = i - 1;
    while (j >= 0 && arr[j].ExecutionOrder > key.ExecutionOrder)
    {
        arr[j + 1] = arr[j];
        j--;
    }
    arr[j + 1] = key;
}
```

The input is nearly always already sorted: `ExecutionOrder` is `Interlocked.Increment(ref _instanceCounter)`, so the array is ordered by construction and rebuilt in dictionary-enumeration order. Insertion sort's best case on an ordered array is $O(N)$ with one comparison per element, and its cost is the allocation-free inner loop rather than a comparison delegate. With $N$ in the single digits, the $O(N^2)$ worst case is at most a few dozen comparisons.

The rebuild's amortisation is worth stating: it runs at most once per `MAX_CONFIG_CACHE_DURATION_MS` (1 s) unless `_wrappersNeedSort` is set, and the flag is set only by an add or a remove drain. So the cost per registration is one rebuild, not one rebuild per frame.

## The three pools

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 74-92)
[MethodImpl(MethodImplOptions.AggressiveInlining)]
public T Get()
{
    if (_pool.TryPop(out var item))
    {
        Interlocked.Decrement(ref _count);
        return item;
    }
    return new T();
}

[MethodImpl(MethodImplOptions.AggressiveInlining)]
public void Return(T item)
{
    if (Interlocked.Increment(ref _count) <= maxSize)
        _pool.Push(item);
    else
        Interlocked.Decrement(ref _count);
}
```

| Operation | Time | Space | Notes |
|---|---|---|---|
| `Get` (hit) | $O(1)$ | — | `ConcurrentStack.TryPop` |
| `Get` (miss) | $O(1)$ | one allocation | No blocking, no wait list |
| `Return` (under cap) | $O(1)$ | — | |
| `Return` (over cap) | $O(1)$ | item becomes garbage | The pool trims under a burst instead of unbounded growth |

The occupancy counter is an `int` maintained with `Interlocked`, not `_pool.Count` — reading `ConcurrentStack<T>.Count` is $O(n)$, and it is read on every `Return`.

Pool occupancy over time is bounded by both churn and the cap:

$$
\text{occupancy} \le \min(K,\ \text{peak concurrent demand}), \qquad K = 50
$$

The steady-state demand per channel is small and known:

| Pool | Objects live at once |
|---|---|
| `_frameEventArgsPool` | 1 update frame args + up to `MaxStepsPerCall` (8) fixed step args in flight during a catch-up batch |
| `_configRequestPool` | 0 in steady state; 1 per FPS change until the next drain |
| `_wrapperPool` | 1 per registered behaviour, i.e. $O(N)$ |

With three channels and a handful of behaviours, total pooled memory is a few hundred small objects and does not grow with the frame rate or with uptime.

## Total space

$$
S = O(C) + O(C \cdot (\text{samplers} + \text{bus} + \text{pools})) + O(N) + O(K)
$$

Concretely, per channel: two samplers, one time source, three pools of at most 50 elements each, four queues (empty in steady state), one `CancellationTokenSource`, two threads (or none, in async mode), and the behaviour dictionary plus its snapshot. Nothing in that list scales with the frame rate, and nothing scales with time — a channel that has run for a week holds exactly what it held after a second.

> Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 69-93, 152-154, 160-167, 741-751, 872-901, 1017-1030; `Src/Core/VeloxDev.Core/Timing/CompensatingTimeSampler.cs` lines 24-30.
