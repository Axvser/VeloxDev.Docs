# 05 · Frame Events and Thread Safety

## 1. What a hook is handed

Every hook except `Awake` and `Start` receives a `FrameEventArgs`, which derives from the abstract `TimeLineEventArgs`.

| Member | Type | Meaning |
|---|---|---|
| `DeltaTime` | `TimeSpan` | Time elapsed since the previous frame **of this pump**, after the time scale has been applied |
| `TotalTime` | `TimeSpan` | Virtual time since the channel started. Excludes everything spent stalled; **not** the sum of the deltas you have been handed, in the sense that the clock owns it |
| `CurrentFPS` | `int` | Measured frames per second, wall-clock based, refreshed once per second |
| `TargetFPS` | `int` | The channel's configured target |
| `Handled` | `bool` | Inherited from `TimeLineEventArgs`. Set it to `true` to stop this frame phase |

All four of `DeltaTime`, `TotalTime`, `CurrentFPS` and `TargetFPS` have **`internal` setters** (`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs` lines 10-25). You can read them from your hooks; you cannot write them. `Handled` is the only writable member, and it is the only one you would ever want to write.

Both times come from one `TimeSample` taken from the channel's clock, so the rate is already inside them (`CreateFrameEventArgs`, `TickManager.cs` lines 824-833) — the pumps do not scale anything afterwards.

## 2. `Handled` stops the rest of the frame phase

```csharp
partial void Update(FrameEventArgs e)
{
    if (KeyboardInterrupt) e.Handled = true;
}
```

The pump checks the flag before each behaviour, not after:

```csharp
// TickManager.cs lines 688-702
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

Three consequences:

- `Handled` is checked **before** the behaviour that set it — so the behaviour that set it is not skipped, only everything after it.
- `LateUpdate` is a separate loop with its own check, so setting `Handled` in `Update` skips this frame's **entire** `LateUpdate` phase, for every behaviour.
- **`FixedUpdate` is unaffected.** Each fixed step builds its own `FrameEventArgs`, so a flag raised in an `Update` is never visible to the fixed pump. The WPF demo demonstrates both halves: with `Handled` on, the two balls keep moving while the `LateUpdate`-positioned follower ring freezes.

**Expected result:** with one behaviour registered and `Handled` set every frame, `Update` runs and `LateUpdate` does not. The headless run in `06_verify-and-complete-code` records `Update +8 LateUpdate +0`.

## 3. Threading model

| Context | Thread |
|---|---|
| `Awake`, `Start`, `Update`, `LateUpdate` | The channel's update thread, `VeloxDev.Update[<channel>]` |
| `FixedUpdate` | The channel's fixed-update thread, `VeloxDev.FixedUpdate[<channel>]` |
| `TickManager.Start` / `Pause` / `Resume` / `SetTargetFPS` / `RegisterBehaviour` / … | Whatever thread calls it — safe from any thread |
| `TickManager.ExecuteOnMainThread(action, channel)` | The delegate runs on the **update** thread, at the start of the next frame |

The two pumps are separate threads and run **concurrently**. A `FixedUpdate` body and an `Update` body can be executing at the same instant, so any field both touch needs its own synchronisation. The demo solves it by *ownership* rather than locks: each ball is owned outright by exactly one pump thread and the window never touches one — `SimState.cs` says so in as many words ("No locking anywhere: exactly one pump thread owns each instance and the window never touches one"). The only state that crosses threads is published whole: an immutable `BallReport` snapshot written with `Volatile.Write` and read with `Volatile.Read`, `Interlocked` counters, and a `ConcurrentQueue` log (`DemoState`, `SimState.cs` lines 191-279). Nothing in the framework does any of this for you.

"Main thread" in `ExecuteOnMainThread` means *the update pump's thread*, not a UI thread. In a GUI host you still have to marshal to the dispatcher yourself — and you should not do it from inside a hook, because the engine catches every exception a hook throws and writes it to `Debug.WriteLine` only. A `Dispatcher.Invoke` that throws is therefore a failure with **no symptom on screen and nothing in any log**. The WPF demo avoids the whole class of problem by having hooks publish immutable snapshots that the UI thread polls (`MainWindow.Hooks.cs` lines 15-22).

## 4. Exception isolation

Every hook call is wrapped:

```csharp
try { w.Behavior.InvokeUpdate(frameArgs); }
catch (Exception ex) { Debug.WriteLine($"[{Name}] Update error: {ex.Message}"); }
```

- An exception in one behaviour does **not** stop the loop and does **not** prevent the other behaviours from running.
- The only trace is `Debug.WriteLine`, which is compiled out of a Release build (no `DEBUG` constant is set by the framework; `Debug.WriteLine` is conditional on your assembly's configuration). In Release, a throwing hook is silent.
- The generated `Awake` and `Start` go through an equivalent guard (`SafeExecute`, `TickManager.cs` lines 939-942).

**Expected result:** a hook that throws every frame leaves the loop running, `TotalFrames` still climbing, and — in a Debug build with a debugger attached — one line per exception in the Output window.

## 5. When you need a thread-safe flag

`FrameEventArgs` is a plain class and its `Handled` property is an ordinary `bool` with no memory barrier. The pump reads it on the pump thread and you write it on the pump thread, so within one hook it is fine. If you want to *raise* a flag from another thread, use `ThreadSafeFrameEventArgs`, which guards the property with a lock (`Src/Core/VeloxDev.Core/TimeLine/ThreadSafeFrameEventArgs.cs`):

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    private readonly object _lockObject = new();
    private bool _handled;

    public new bool Handled
    {
        get { lock (_lockObject) return _handled; }
        set { lock (_lockObject) _handled = value; }
    }
}
```

Note that the framework never constructs this type — every `FrameEventArgs` handed to a hook comes from the channel's pool as a plain `FrameEventArgs`. It exists for hosts that build their own arguments, and the `new` keyword means a `ThreadSafeFrameEventArgs` read through a `FrameEventArgs` reference gets the **unsynchronised** property. Use it through its own static type or not at all.

## Notes

- Do not hold a lock across the whole `Update` body if the fixed pump needs the same lock; at a 16 ms step the fixed pump will block behind it and your `FixedUpdate` count will drop.
- Do not call `Thread.Sleep` in a hook expecting the loop to compensate cleanly. `Update` is uncompensated — a sleep there shows up as one large `DeltaTime` on the *next* frame, because the sample is taken before the hooks run. `FixedUpdate` *is* compensated — a sleep there becomes a batch of steps on the next advance. The WPF demo has a button for each, and the difference between them is the point of that demo.
