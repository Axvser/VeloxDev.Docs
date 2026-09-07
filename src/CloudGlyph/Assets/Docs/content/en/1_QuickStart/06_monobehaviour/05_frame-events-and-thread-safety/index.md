# MonoBehaviour — Frame Events & Thread Safety

## 1. The event-payload types

All four payload types live in `VeloxDev.TimeLine` (`Src/Core/VeloxDev.Core/TimeLine/`):

| Type | Base | Purpose |
|---|---|---|
| `TimeLineEventArgs` | — | Abstract base; carries the `virtual bool Handled` flag (default `false`). |
| `FrameEventArgs` | `TimeLineEventArgs` | The per-frame payload handed to `Update`, `LateUpdate` and `FixedUpdate`. |
| `ThreadSafeFrameEventArgs` | `FrameEventArgs` | A variant whose `Handled` getter/setter are guarded by a lock. |
| `TransitionEventArgs` | `TimeLineEventArgs` | Empty sealed payload shared with the transition feature. |

`FrameEventArgs` exposes four read-only values that the channel fills per frame (`internal` setters):

```csharp
partial void Update(FrameEventArgs e)
{
    Console.WriteLine($"delta   = {e.DeltaTime.TotalMilliseconds:F3} ms");  // scaled by TimeScale
    Console.WriteLine($"elapsed = {e.TotalTime.TotalSeconds:F3} s");        // channel runtime
    Console.WriteLine($"fps     = {e.CurrentFPS} (target {e.TargetFPS})");
}
```

- `DeltaTime` — the time since the last update frame, already multiplied by the channel `TimeScale` (a scale of `0` yields `0`).
- `TotalTime` — the channel's accumulated runtime at the frame boundary.
- `CurrentFPS` / `TargetFPS` — the measured frame rate and the configured target.

**Expected result:** the three printed lines change every frame and stay consistent with the manager's status queries.

## 2. The `Handled` flag — short-circuiting

`Handled` starts `false` for every frame. Setting it to `true` inside a hook stops the loop from invoking further hooks for that phase:

- In the Update phase, later behaviours' `Update` are skipped, and — because `LateUpdate` shares the same frame object — **no `LateUpdate` runs for that frame either**.
- The FixedUpdate pump builds its own per-tick `FrameEventArgs`, so a `Handled` set during `Update` does not affect `FixedUpdate`.

```csharp
partial void Update(FrameEventArgs e)
{
    if (SomeOneShotCondition)
    {
        e.Handled = true;   // skip remaining Update hooks and all LateUpdate this frame
    }
}
```

**Expected result:** after the flag is set once, the remaining behaviours see no further `Update` (and no `LateUpdate`) until the next frame resets the flag.

## 3. Frame objects are pooled — do not retain them

The manager pools and reuses `FrameEventArgs` instances (an internal object pool, default capacity 50). The object your hook receives is returned to the pool at the end of the frame and reused on a later frame. Reading its properties inside the hook is safe; storing the object (or capturing it in a closure that outlives the frame) will observe recycled values. If you need thread-safe `Handled` handling for your own scenarios, the public `ThreadSafeFrameEventArgs` subclass provides lock-guarded `Handled` access — the built-in loop itself uses the plain pooled `FrameEventArgs`, with `Handled` only written from its own pump.

**Expected result:** you only ever use `e` inside the hook body (and the loop is the only writer), which is the supported pattern.

## 4. The threading model

A running channel owns two pumps:

- the **Update pump** dispatches `Update` then `LateUpdate` for every behaviour, in registration order, on one thread (or task);
- the **FixedUpdate pump** dispatches `FixedUpdate` on a second thread (or task) every fixed-timestep interval (default 16 ms).

Consequences to design for:

- `Update` and `FixedUpdate` can run at the same time. Shared state between the two must be synchronized — the examples in this Quick Start use `Interlocked` for counters, and a `lock` works equally well.
- A hook body runs on a loop thread, never on a UI thread. To touch a WPF/WinUI/Avalonia control from `Update`, marshal onto the dispatcher — the shipped WPF demo does exactly that with `Dispatcher.Invoke(...)` from inside `Update` (`Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs`).
- `ExecuteOnMainThread(action, channel)` does not marshal to the UI thread. It queues the action to be run at the top of the next **Update pump** frame on that pump's own thread — useful to move work off the FixedUpdate thread onto the Update thread, not to reach a window.
- An exception inside a hook is caught by the channel (logged via `Debug.WriteLine`) and the loop keeps running; a single bad behaviour does not stop its neighbours.
- Each channel is independent: behaviours and settings are per channel, and channels run their own pumps.

**Expected result:** following these rules keeps counters exact and lets a hook safely update UI through a dispatcher without data races between the two pumps.

## Run declaration

- ⚠️ Statically verified only — the type hierarchy, the `Handled` short-circuit semantics and the threading model are transcribed from the event-args source files and the loop bodies in `MonoBehaviourManager.cs`; they are exercised by the automated tests described on the [Verify & Complete Code](../06_verify-and-complete-code/) page.
