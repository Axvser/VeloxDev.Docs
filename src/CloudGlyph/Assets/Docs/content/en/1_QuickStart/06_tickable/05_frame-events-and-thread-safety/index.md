# 05 · Frame Events and Thread Safety

## 1. What a hook is handed

Every hook except `Awake` and `Start` receives a `FrameEventArgs`, which derives from the abstract `TimeLineEventArgs`. The two clock readings (`DeltaTime` / `TotalTime`) and `Handled` come from that base; only the two frame-rate readings are declared on `FrameEventArgs` itself.

| Member | Type | Meaning |
|---|---|---|
| `DeltaTime` | `TimeSpan` | Time elapsed since the previous frame **of this pump**, after the time scale has been applied |
| `TotalTime` | `TimeSpan` | Virtual time since the channel started. Excludes everything spent stalled; **not** the sum of the deltas you have been handed, in the sense that the clock owns it |
| `CurrentFPS` | `int` | Measured frames per second, wall-clock based, refreshed once per second |
| `TargetFPS` | `int` | The channel's configured target |
| `Handled` | `bool` | Inherited from `TimeLineEventArgs`. Set it to `true` to stop this frame phase |

`DeltaTime` and `TotalTime` are declared on the abstract base `TimeLineEventArgs` (`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`); `CurrentFPS` and `TargetFPS` are declared on `FrameEventArgs` (`Src/Core/VeloxDev.Core/TimeLine/FrameEventArgs.cs`). All four have **`internal` setters**: you can read them from your hooks, but you cannot write them. `Handled` is the only writable member, and it is the only one you would ever want to write.

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

The two pumps are separate threads and run **concurrently**: a `FixedUpdate` body and an `Update` body can be executing at the same instant, so any field both touch needs its own synchronisation. The demo solves that by *ownership* rather than locks — each ball is owned outright by exactly one pump thread and the window never touches one (`SimState.cs`). The only state that crosses threads is published whole:

| Channel | Mechanism |
|---|---|
| Ball snapshots | an immutable `BallReport` written with `Volatile.Write`, read with `Volatile.Read` |
| Counters | `Interlocked` |
| Log | `ConcurrentQueue` (`DemoState`, `SimState.cs:191-279`) |

Nothing in the framework does any of this for you.

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

## 5. When you need a cross-thread flag

`FrameEventArgs` is a plain class and `Handled` is an ordinary `bool` with no memory barrier. That is safe because the pump reads it and your hooks write it on the **same** thread — inside the framework `Handled` never crosses a thread boundary. It is also reset to `false` whenever the arguments are built (`TickManager.cs:833`), so it carries nothing from one frame to the next.

An earlier version of this page recommended `ThreadSafeFrameEventArgs`, a lock-guarded subclass. **It has been deleted from the source.** The framework never constructed it — every `FrameEventArgs` a hook receives comes from the channel's pool as a plain `FrameEventArgs` (`TickManager.cs:154`) — and its `new`-shadowed `Handled` resolved to the *unsynchronised* base property through a `FrameEventArgs` reference anyway, so it could not have done the job it advertised.

If your own code must observe a flag raised on another thread, do not write `FrameEventArgs.Handled` from that thread. Publish the flag with `Volatile.Write` and read it with `Volatile.Read` — the idiom the framework itself uses for the cross-thread `_targetFPS` (`TickManager.cs:778` write, `:832` read) — and transfer it to `Handled` inside a hook, on the pump thread:

```csharp
// Host state, written from another thread:
private int _stopRequested;                          // 0 / 1
public void RequestStop() => Volatile.Write(ref _stopRequested, 1);

// In the hook — runs on the pump thread:
partial void Update(FrameEventArgs e)
{
    if (Volatile.Read(ref _stopRequested) != 0) e.Handled = true;
}
```

`Handled` stays a single-threaded write on the pump thread; only the host flag crosses threads, and it does so through a proper barrier. Remember that `Handled` stops only the current frame phase (section 2). To end the loop itself, call `TickManager.Pause(channel)` / `StopAsync(channel)` — the lifecycle calls are safe from any thread (section 3).

## Notes

- Do not hold a lock across the whole `Update` body if the fixed pump needs the same lock; at a 16 ms step the fixed pump will block behind it and your `FixedUpdate` count will drop.
- Do not call `Thread.Sleep` in a hook expecting the loop to compensate cleanly. `Update` is uncompensated — a sleep there shows up as one large `DeltaTime` on the *next* frame, because the sample is taken before the hooks run. `FixedUpdate` *is* compensated — a sleep there becomes a batch of steps on the next advance. The WPF demo has a button for each, and the difference between them is the point of that demo.
