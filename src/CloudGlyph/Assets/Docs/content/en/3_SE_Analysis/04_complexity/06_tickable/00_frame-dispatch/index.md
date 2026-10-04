# Frame Dispatch

The cost of one frame, and why it does not grow with the frame rate.

Let $N$ be the number of registered behaviours on the channel and $k$ the number added or removed since the last rebuild.

## The sweeps

One update iteration performs three sweeps over the same array:

$$
T_{\text{frame}} = \underbrace{O(N)}_{\text{Update sweep}} + \underbrace{O(N)}_{\text{LateUpdate sweep}} + \underbrace{O(1)}_{\text{sample, pace, stats}}
$$

Each sweep body is: an array index, a pattern-match on the wrapper, and one delegate call. The `Handled` check is hoisted to the top of the body, so a behaviour that aborts the phase turns the rest of **both** loops into a single branch:

```csharp
// Src/Core/VeloxDev.Core/TimeLine/TickManager.cs (lines 692-701)
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
```

So the bound is sharp in one direction: $T_{\text{Update sweep}} \le c_1 N$ with the constant being one delegate invocation, and a behaviour at index $i$ that raises `Handled` makes both sweeps cost $O(i)$ instead of $O(N)$.

The `try`/`catch` is inside the loop, which is worth noting for its cost: on the no-throw path a `try` block costs nothing at run time in .NET, so exception isolation is free until an exception actually happens.

## Per step, not per frame

The fixed pump's cost is per step ($h$ ms), not per frame:

$$
T_{\text{fixed}} = O(N) \text{ per owed step}
$$

At $F$ fps and step $h$ ms, the steps owed per second is $1000/h$ while the frames per second is $F$, so the fixed sweeps happen about $\frac{1000}{F \cdot h}$ times as often as the update sweeps:

$$
\frac{\text{steps}}{\text{frame}} \approx \frac{1000}{F \cdot h}
$$

For the defaults, $F = 60$ and $h = 16$: $\frac{1000}{60 \cdot 16} \approx 1.04$ steps per frame. Change the target to 2 fps and the ratio goes to about 31; press `SetFixedUpdateInterval(200)` and at 60 fps it drops to 2.5. The demo measures the ratio rather than computing it — `Δfixed / Δframes` over a one-second window (`MainWindow.xaml.cs` lines 201-228) — which is why the value it displays tracks the *measured* frame rate rather than the configured one and reads high while the update pump is still ramping up. Note also that the ratio is unaffected by the time scale: the rate moves the virtual clock, and the fixed pump follows the virtual clock.

## Amortised cache validation

`GetCachedWrappers` runs on every sweep and is $O(1)$ when the cache is good:

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

- **Cache hit:** one `Stopwatch.GetTimestamp()`, one `Interlocked.Read`, one comparison, one `volatile` read of the array. Constant, and called three times per frame (once per sweep) plus once per fixed step.
- **Cache miss:** `RebuildCachedWrappers`, which is where the $O(N^2)$ lives.

$T_{\text{rebuild}}$ has three parts — allocate and fill ($O(N)$), insertion-sort ($O(N^2)$ worst case, $O(N)$ on an already-ordered array, which is the common case because `ExecutionOrder` is a monotonically increasing counter and registration order *is* execution order), and a possible `Array.Resize` copy ($O(N)$):

$$
T_{\text{rebuild}} = O(N) + O(N^2)_{\text{worst}} + O(N) = O(N^2) \text{, and } O(N) \text{ in practice}
$$

The source comment states the trade implicitly: insertion sort was chosen over a comparison sort because "behavior counts are usually small, avoiding LINQ allocations". With the dispatch loop's own $O(N)$ dominating at realistic $N$ (a handful), the sort's asymptotics never bite.

## Space

The steady-state space per channel is fixed, not per frame:

| Structure | Size |
|---|---|
| `_behaviors` | $O(N)$ — one wrapper per registered behaviour |
| `_cachedWrappers` | $O(N)$ — the snapshot |
| The three pools | $O(\min(\text{churn}, 50))$ each, capped by `DEFAULT_OBJECT_POOL_SIZE` |
| The four queues | $O(k)$ where $k$ is unapplied changes; normally 0 |
| Samplers, bus, CTS | $O(1)$ each |

**Per-frame allocation in the steady state is zero.** One `FrameEventArgs` is drawn and returned; one wrapper per registration and one config request per FPS change are pooled; the dispatch array is only replaced on a change, not per frame. That is the property the pool exists for, and it is measurable: the demo's `HookEntry` is deliberately a struct "built without touching a string" because "at the default frame rate a channel runs about 120 hooks a second, and a log that allocated per call would be a GC cost the demo imposed on the very loop it is measuring" (`SimState.cs` lines 146-158).

> Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 689-751, 872-901; `Examples/Tickable/WPF/Demo/MainWindow.xaml.cs` lines 201-228; `Examples/Tickable/WPF/Demo/SimState.cs` lines 146-158.
