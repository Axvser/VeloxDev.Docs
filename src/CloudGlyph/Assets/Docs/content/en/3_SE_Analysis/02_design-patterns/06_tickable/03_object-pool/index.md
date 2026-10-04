# Object Pool and copy-on-write dispatch

Per frame, a channel would otherwise allocate one `FrameEventArgs`, one `ConfigChangeRequest` per FPS change and one wrapper per registration. All three are pooled at a fixed capacity, and the dispatch array the loops read is a copy-on-change snapshot. The design goal is that a steady-state frame allocates nothing.

| Pool | Element type | Capacity | Source |
|---|---|---|---|
| `_frameEventArgsPool` | `FrameEventArgs` | `DEFAULT_OBJECT_POOL_SIZE` = 50 | `TickManager.cs` 152 |
| `_configRequestPool` | `ConfigChangeRequest` | 50 | `TickManager.cs` 153 |
| `_wrapperPool` | `BehaviorWrapper` | 50 | `TickManager.cs` 154 |

## The pool

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 69-93)
private sealed class ObjectPool<T>(int maxSize) where T : class, new()
{
    private readonly ConcurrentStack<T> _pool = new();
    private int _count;

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
}
```

Three details of that implementation are deliberate:

- **`Get` is allocation-free under load, and allocates on miss.** There is no blocking and no waiting list: an empty pool means `new T()`, so the hot path never stalls.
- **The cap is enforced on `Return` only.** The increment is unconditional, so the counter stays accurate under concurrency; the excess is decremented back and the item is dropped for the GC. The pool therefore *trims* under a burst instead of growing without bound.
- **The counter is an `int` with `Interlocked`, not `_pool.Count`.** `ConcurrentStack<T>.Count` walks the stack; this is O(1).

## Where the pool is touched

`FrameEventArgs` is drawn once per frame and returned at the end of the same frame body:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 824-833)
private FrameEventArgs CreateFrameEventArgs(TimeSpan delta, TimeSpan total)
{
    var frameArgs = _frameEventArgsPool.Get();
    frameArgs.DeltaTime = delta;
    frameArgs.TotalTime = total;
    frameArgs.CurrentFPS = _currentFPS;
    frameArgs.TargetFPS = Volatile.Read(ref _targetFPS);
    frameArgs.Handled = false;
    return frameArgs;
}
```

The `Handled = false` line is the reset that makes reuse safe, and it is the reason the per-frame-phase abort is reliable: each frame starts from a known-clean flag.

The fixed pump draws and returns one argument **per step**, not per wake-up — a stall that owes six steps draws six times inside one loop iteration and returns each immediately:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 483-493)
for (var i = 0; i < count; i++)
{
    var fixedFrameArgs = CreateFrameEventArgs(
        sample.Delta,
        TimeSpan.FromTicks((firstStep + i) * stepTicks));
    ExecuteBehaviorsFixedUpdateSync(fixedFrameArgs, token);

    // 直接还池。这里原来把它塞进一个跨线程队列，由 update 循环取出再还池——
    // 一次往返，而那条队列从不把参数交给任何人，纯粹是浪费。
    _frameEventArgsPool.Return(fixedFrameArgs);
}
```

That comment records a removed round trip: the arguments used to be handed to a cross-thread queue that the update loop drained purely to return them to the pool. Nothing ever read the arguments from it.

`ConfigChangeRequest` is the only pooled object that crosses threads — drawn on the caller's thread by `SetTargetFPS`, filled, enqueued, and later reset and returned by the update pump (`ProcessConfigChanges`, lines 768-783, and `ClearQueues`, lines 954-965).

`BehaviorWrapper` is pooled per registration: drawn and `Reset` in `ProcessAddedBehaviors` (lines 792-793), `Clear`ed and returned in `ProcessRemovedBehaviors` (lines 810-811).

## Why only three things are pooled

The two knobs that used to need a pooled request object no longer do, and the code says why:

- `SetFixedUpdateInterval` writes a single volatile field. The request object existed only when the value had to travel through the update pump's queue; it now goes straight to the pump that owns the sampler.
- `SetTimeScale` writes to the bus, which serialises its own writers.

`ConfigChangeRequest` survives for `TargetFPS` alone, because that one really does have to be applied by the update loop: the target and the cached frame duration must be written together, and only the update loop reads either.

## Copy-on-write dispatch

The loops never iterate the behaviour dictionary. They iterate a plain array that is rebuilt only when something changed:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 741-751)
private BehaviorWrapper[] GetCachedWrappers()
{
    var currentTime = GetTimestamp();
    if (_wrappersNeedSort || currentTime - Interlocked.Read(ref _lastConfigCheckTimestamp) >
        TimeConversion.MillisecondsToTicks(MAX_CONFIG_CACHE_DURATION_MS, TimeConversion.DefaultTicksPerSecond))
    {
        RebuildCachedWrappers();
        Interlocked.Exchange(ref _lastConfigCheckTimestamp, currentTime);
    }
    return _cachedWrappers;
}
```

The rebuild (lines 872-901) is where the interesting decisions are:

- It sizes the array from `_behaviors.Values.Count`, fills it with active wrappers, **insertion-sorts it on `ExecutionOrder`**, then `Array.Resize`es it down. The source comment names the reason for insertion sort: behaviour counts are small and LINQ would allocate.
- `_cachedWrappers` is `volatile`, so a pump thread that calls `GetCachedWrappers` sees a whole array or the previous whole array — never a half-built one. There is no lock on the dispatch path at all.
- `_wrappersNeedSort` is set by the add and remove drains and cleared by the rebuild, so a registration is visible to the very next frame.

The dispatch loops are consequently a bare indexed `for` over a stable array, with the `Handled` and cancellation checks inlined per iteration:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 689-702)
private void ExecuteBehaviorsUpdateSync(FrameEventArgs frameArgs, CancellationToken token)
{
    var wrappers = GetCachedWrappers();
    for (int i = 0; i < wrappers.Length; i++)
    {
        if (frameArgs.Handled || token.IsCancellationRequested) break;
        var w = wrappers[i];
        if (w is { IsActive: true, Behavior: not null })
        {
            try { w.Behavior.InvokeUpdate(frameArgs); }
            catch (Exception ex) { Debug.WriteLine($"[{Name}] Update error: {ex.Message}"); }
        }
    }
}
```

The `try/catch` inside the loop is the exception-isolation policy: one misbehaving behaviour cannot stop the loop or the behaviours behind it.

> Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 69-93, 152-154, 483-493, 689-702, 741-751, 768-816, 824-833, 872-901, 954-965.
