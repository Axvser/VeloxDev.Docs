# Pause, Resume and Restart

Pause is not a flag the loops poll. It is a property of the channel's **time source**, and the pumps park on it. That single decision is what makes a paused channel cost nothing and what makes one `Pause` freeze a frame loop and an animation anchored to the same clock at the same time.

## 1. Pause is a bus operation

`TickManager.cs` lines 386-404:

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

Both are guarded no-ops when they would not change anything.

Inside the pumps the pause shows up as a park, not a poll:

```csharp
// TickManager.cs lines 522-526, inside UpdateLoop
if (!_bus.IsAdvancing)
{
    _bus.WaitWhileStalledAsync(token).GetAwaiter().GetResult();
    continue;
}
```

`IsAdvancing` — not `IsPaused` — is the predicate the loops wait on, because a time scale of `0` also stops the clock without pausing it. A loop that checked only `IsPaused` would spin against a frozen clock.

**Expected result:** after `TickManager.Pause("demo")`, `TickManager.IsPaused("demo")` is `true`, `TickManager.SystemStatus("demo")` is `"Paused"`, and `TickManager.TotalFrames("demo")` stops increasing. **One frame already in flight may still land** after the call returns — measure from a moment after the pause, as the tests do:

```csharp
TickManager.Pause(channel);
await Task.Delay(60);   // let an in-flight frame land
var whilePaused = TickManager.TotalFrames(channel);
await Task.Delay(200);
// whilePaused == TickManager.TotalFrames(channel)
```

## 2. A parked loop is alive

`IsUpdateThreadAlive` and `IsFixedUpdateThreadAlive` return `true` while paused. A parked pump has no activity by construction, so the liveness query qualifies the clock rather than the activity (`TickManager.cs` lines 195-199). See `03_configure-and-run-the-loop`.

**Expected result:** while `IsPaused("demo")` is `true`, both liveness queries return `true`.

## 3. TogglePause

```csharp
TickManager.TogglePause("demo");
```

**Expected result:** toggles the paused state — `Pause()` if the channel is running and not paused, `Resume()` otherwise. On a stopped channel it is a no-op, because both branches fall through their own guards (`TickManager.cs` line 444).

## 4. StopAsync

```csharp
await TickManager.StopAsync("demo");
```

**Expected result:** `IsRunning("demo")` becomes `false`, `SystemStatus("demo")` becomes `"Stopped"`, both liveness queries become `false`, and `OnChannelStopped` fires.

`StopAsync` also does three things worth knowing:

- **It clears a pause.** `_bus.Resume()` is called on the way down (`TickManager.cs` line 341), so a channel that was paused when stopped comes back runnable (`TickableBusTests.StartingAChannelClearsAPauseLeftOverFromTheLastLifecycle`).
- **It resets the statistics and drains the queues** in its `finally` block (lines 365-373). `TotalFrames`, `TotalTime` and `CurrentFPS` go back to zero.
- **It waits for the pumps with a 1 s timeout**, then nulls the thread and task fields regardless. It is safe to `await` from a UI `Closing` handler; the demo does not, because the process is ending anyway (`MainWindow.xaml.cs` lines 55-61).

Stopping while paused works and must not hang: a parked pump waits on a call that observes the cancellation token, so `StopAsync`'s cancel propagates into the park (`TickableBusTests.StoppingWhilePausedEndsTheChannel`).

**Registrations survive a stop.** The `finally` block clears the four queues, not `_behaviors`; a behaviour whose registration had already been drained stays registered and starts ticking again on the next `Start`. A registration still queued when the stop drains it is discarded, and so is a pending unregistration in `_removeQueue`. `Awake` / `Start` do not re-run on the survivors.

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

Re-registration builds a fresh wrapper for the same object, and the drain calls `InvokeAwake` and `InvokeStart` on it. Stopping and starting the channel only moves the pumps. The WPF demo exposes both pairs of buttons (`MainWindow.xaml.cs` lines 105-119) precisely to make that visible.

`RestartAsync` is `StopAsync` plus two waits plus `Start` (`TickManager.cs` lines 408-432): it waits up to 1 s for shutdown confirmation (falling back to `ForceCleanup` if the pumps will not stop), then up to 500 ms for the queues to drain, then starts.

**Expected result:** after a restart the clocks are re-anchored — a frame delivered immediately after the restart has a `DeltaTime` of one frame, not of the whole downtime (`TickableBusTests.RestartingAChannelRePrimesItsClocks`).

## Notes

- `Pause`, `Resume`, `TogglePause` and `Start` are synchronous; only `StopAsync` and `RestartAsync` return `Task`.
- A rate of `0` is not a pause: `IsPaused` stays `false`, `Resume` cannot lift it, and only `SetTimeScale(<non-zero>)` restarts the clock.
