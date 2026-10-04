# 04 · Pause, Resume and Restart

Pause is not a flag the loops poll. It is a property of the channel's **time source**, and the pumps park on it. That single decision is what makes a paused channel cost nothing and what makes one `Pause` freeze a frame loop and an animation anchored to the same clock at the same time.

## 1. Pause is a bus operation

`TickManager.cs` lines 384-402:

```csharp
public void Pause()
{
    if (!_isRunning || _bus.IsPaused) return;
    _bus.Pause();
    Paused?.Invoke(this, EventArgs.Empty);
}

public void Resume()
{
    if (!_isRunning || !_bus.IsPaused) return;
    _bus.Resume();
    Resumed?.Invoke(this, EventArgs.Empty);
}
```

Both are guarded no-ops when they would not change anything: `Pause` on a stopped or already-paused channel does nothing and fires nothing, and neither does `Resume` on a channel that is not paused.

Inside the pumps the pause shows up as a park, not a poll:

```csharp
// TickManager.cs lines 520-524, inside UpdateLoop
if (!_bus.IsAdvancing)
{
    _bus.WaitWhileStalledAsync(token).GetAwaiter().GetResult();
    continue;
}
```

`IsAdvancing` — not `IsPaused` — is the predicate the loops wait on, because a time scale of `0` also stops the clock without pausing it. A loop that checked only `IsPaused` would spin against a frozen clock.

**Expected result:** after `TickManager.Pause("demo")`, `TickManager.IsPaused("demo")` is `true`, `TickManager.SystemStatus("demo")` is `"Paused"`, and `TickManager.TotalFrames("demo")` stops increasing. **One frame that was already in flight may still land** after the call returns — measure from a moment after the pause, as the demo's tests do:

```csharp
TickManager.Pause(channel);
await Task.Delay(60);   // 让已在途的一帧落完，之后的读数才是暂停期间的
var whilePaused = TickManager.TotalFrames(channel);
await Task.Delay(200);
// whilePaused == TickManager.TotalFrames(channel)
```

## 2. A parked loop is alive

`IsUpdateThreadAlive` and `IsFixedUpdateThreadAlive` return `true` while paused. This is deliberate and is the one place where the "recent activity" heuristic had to be qualified: a parked pump has no activity by construction. See `03_configure-and-run-the-loop`.

**Expected result:** while `IsPaused("demo")` is `true`, both `IsUpdateThreadAlive("demo")` and `IsFixedUpdateThreadAlive("demo")` are `true`.

## 3. TogglePause

```csharp
TickManager.TogglePause("demo");
```

**Expected result:** toggles the paused state — `Pause()` if the channel is running and not paused, `Resume()` otherwise. On a stopped channel it is a no-op, because both branches fall through their own guards.

## 4. StopAsync

```csharp
await TickManager.StopAsync("demo");
```

**Expected result:** `IsRunning("demo")` becomes `false`, `SystemStatus("demo")` becomes `"Stopped"`, both liveness queries become `false`, and `OnChannelStopped` fires.

`StopAsync` also does three things worth knowing:

- **It clears a pause.** `_bus.Resume()` is called on the way down (line 339), so a channel that was paused when stopped comes back runnable. Without that, a "stopped while paused" channel would restart and immediately park forever (`TickableBusTests.StartingAChannelClearsAPauseLeftOverFromTheLastLifecycle`).
- **It resets the statistics and clears the queues** in its `finally` block (lines 363-371). `TotalFrames`, `TotalTime` and `CurrentFPS` all go back to zero.
- **It waits for the pumps with a 1 s timeout**, then nulls the thread and task fields regardless. It is safe to `await` it from a UI `Closing` handler; the demo does not, because the process is ending anyway (`MainWindow.xaml.cs` line 69).

Stopping while paused works and must not hang: a parked pump waits on a call that observes the cancellation token, so `StopAsync`'s cancel propagates into the park. `TickableBusTests.StoppingWhilePausedEndsTheChannel` asserts the task wins against a 5 s timeout.

## 5. RestartAsync

```csharp
await TickManager.RestartAsync("demo");
```

**Expected result:** `IsRunning("demo")` is `true` again, `TotalFrames("demo")` is small (the statistics were reset), and `Awake` / `Start` do **not** re-run.

That last point is the sharpest distinction in the whole lifecycle:

| Action | `Awake` / `Start` again? | Counters reset? |
|---|---|---|
| `StopAsync` then `Start` | No | Yes |
| `RestartAsync` | No | Yes |
| `CloseTickable()` then `InitializeTickable()` | **Yes** | No |

Re-registration builds a fresh wrapper for the same object, and the drain calls `InvokeAwake` and `InvokeStart` on it. Stopping and starting the channel only moves the pumps. The WPF demo exposes both buttons (`MainWindow.xaml.cs` lines 121-135) precisely to make that pair visible.

`RestartAsync` is `StopAsync` plus two waits plus `Start` (`TickManager.cs` lines 404-428): it waits up to 1 s for shutdown confirmation (falling back to `ForceCleanup` if the pumps will not stop), then up to 500 ms for the queues to drain, then starts.

**Expected result:** after a restart the clocks are re-anchored — a frame delivered immediately after the restart has a `DeltaTime` of one frame, not of the whole downtime.

## Notes

- `Pause`, `Resume`, `TogglePause` and `Start` are synchronous; only `StopAsync` and `RestartAsync` are `Task`-returning.
- A rate of `0` is not a pause: `IsPaused` stays `false`, `Resume` cannot lift it, and only `SetTimeScale(<non-zero>)` restarts the clock.
