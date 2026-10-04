# 03 · Configure and Run the Loop

Everything in this step goes through the static facade `TickManager`. Every one of its members takes an optional trailing `channel` argument that defaults to `TickManager.DEFAULT_CHANNEL` (the literal `"default"`).

## 1. Registration, then start

```csharp
var ball = new BouncingBall();

ball.InitializeTickable();          // generated: enqueue this instance onto channel "demo"
TickManager.Start("demo");         // create the channel and start both pumps
```

**Expected result:** `Awake` prints once, then `Start` prints once, then `Update` / `LateUpdate` / `FixedUpdate` start arriving. `TickManager.IsRunning("demo")` is `true`.

The order of those two lines does not matter and is worth being explicit about. `RegisterBehaviour` only *enqueues*; the update pump drains the queue inside its first frame body, **before** that frame is sampled. So registering after `Start` still produces `Awake` → `Start` → first `Update`, and registering before `Start` produces the same sequence. What you cannot get is a hook running before registration.

`Start` is idempotent: `LoopChannel.Start` begins with `if (_isRunning) return;` (`TickManager.cs` line 276), so a second `Start("demo")` on a running channel does nothing — including not re-firing `OnChannelStarted`.

## 2. The channel knobs

| Call | Effect | Where it lands |
|---|---|---|
| `TickManager.SetTargetFPS(30, "demo")` | Target frames per second. Valid range `1..1000`; anything outside is **ignored**, not clamped. Default 60. | Queued; applied on the next frame boundary |
| `TickManager.SetFixedUpdateInterval(33, "demo")` | Milliseconds between `FixedUpdate` pushes. Valid range `1..1000`; out of range ignored. Default 16. | Written to a volatile field; the fixed pump picks it up on its own thread |
| `TickManager.SetTimeScale(2f, "demo")` | Rate of the channel's clock. `1.0` is real time. | Applied straight to the channel's time source. **Throws `ArgumentOutOfRangeException` for a negative value** |
| `TickManager.SetUseAsyncLoop(true, "demo")` | Drives the loop with `async`/`await` instead of native threads | Stored on the channel. **Throws `InvalidOperationException` if the channel is running** |
| `TickManager.ClearUseAsyncLoopOverride("demo")` | Drops the per-channel override, falls back to `TickManager.UseAsyncLoop` | Same `InvalidOperationException` guard |
| `TickManager.ExecuteOnMainThread(() => ..., "demo")` | Runs the delegate at the start of the next frame | Queued; up to 64 actions per frame are drained |

Two of these behave differently from a naive reading:

- **`SetTargetFPS` is a silent no-op out of range.** `if (fps < MIN_FPS || fps > MAX_FPS) return;` (`TickManager.cs` lines 205-206). Passing `0` or `5000` changes nothing and tells you nothing.
- **A time scale of `0` is not a pause.** It freezes the clock — no frame is dispatched and `TotalTime` stops — but `TickManager.IsPaused("demo")` stays `false` and `SystemStatus("demo")` still reports `"Running"`. Only a non-zero rate restarts it, and `Resume()` will not. The WPF demo prints `IsAdvancing` next to `SystemStatus` for exactly this reason (`MainWindow.xaml.cs` lines 307-324).

**Expected result:** after `SetTargetFPS(30, "demo")` the measured `TickManager.CurrentFPS("demo")` settles around 30 within a second. After `SetTimeScale(2f, "demo")`, `TickManager.TimeScale("demo")` returns `2`.

## 3. Reading the channel back

| Query | Returns |
|---|---|
| `IsRunning(channel)` | `bool` — pumps started and not stopped |
| `IsPaused(channel)` | `bool` — the channel's clock is paused |
| `SystemStatus(channel)` | `"Stopped"` / `"Paused"` / `"Running"` |
| `TargetFPS(channel)` / `CurrentFPS(channel)` | Configured vs. measured frames per second |
| `TotalTime(channel)` / `TotalTimeMs(channel)` | Virtual time since the channel started |
| `TotalFrames(channel)` | Frames completed |
| `ActiveBehaviorCount(channel)` | Behaviours currently registered |
| `TimeScale(channel)` | The clock's rate |
| `IsUpdateThreadAlive(channel)` / `IsFixedUpdateThreadAlive(channel)` | `bool` — see the note below |
| `Bus(channel)` | `ITimeSourceControl?` — the channel's clock, or `null` if the channel was never created |
| `ChannelNames` | `IEnumerable<string>` — every channel that has been created |

Every query except `ChannelNames` is safe on a channel that does not exist: it returns the "stopped" answer (`false`, `0`, `TimeSpan.Zero`, `"Stopped"`) or `null` for `Bus`. A query **never creates** a channel — `Bus` is written specifically to answer `null` rather than construct one as a side effect (`TickManager.cs` lines 1134-1145, asserted by `TickableBusTests.BusIsNullForAChannelThatWasNeverStarted`).

### The liveness queries are not inactivity checks

`IsUpdateThreadAlive` / `IsFixedUpdateThreadAlive` read:

```csharp
public bool IsUpdateThreadAlive => _isRunning && _isUpdateThreadActive &&
    (!_bus.IsAdvancing || IsRecentActivity(Interlocked.Read(ref _updateThreadLastActivityTimestamp)));
```

A **paused** pump parks on the time source instead of polling, so "has it done anything in the last 2 s" is necessarily false while paused. The `!_bus.IsAdvancing ||` term is what stops that from being reported as a dead thread. Measured: pausing a channel and then querying still returns `true` for both — see `TickableBusTests.PausingAChannelStopsItsFramesAndResumingRestartsThem` and the run in `06_verify-and-complete-code`.

## 4. Channel events

```csharp
TickManager.OnChannelStarted += (_, e) => Console.WriteLine($"started {e.ChannelName}");
TickManager.OnChannelPaused  += (_, e) => Console.WriteLine($"paused  {e.ChannelName}");
TickManager.OnChannelResumed += (_, e) => Console.WriteLine($"resumed {e.ChannelName}");
TickManager.OnChannelStopped += (_, e) => Console.WriteLine($"stopped {e.ChannelName}");
```

**Expected result:** starting channel `demo` prints `started demo`. The payload is `TickChannelEventArgs`, whose only member is `ChannelName`.

These are **static** events and the subscription is process-wide, so a handler must filter by `ChannelName` if it only cares about one channel. Note also that `StopAsync` on a channel that is not running returns early (`TickManager.cs` line 331, `if (!_isRunning) return;`) and so does **not** fire `OnChannelStopped`. The event fires exactly when the channel transitioned from running to stopped.

## Notes

- `Start` creates the channel on first use, so `TickManager.Start("demo")` on a name nothing has registered on is legal — it just produces an empty loop.
- A channel's thread names are `VeloxDev.Update[<name>]` and `VeloxDev.FixedUpdate[<name>]` (`TickManager.cs` lines 310, 316). They appear in a debugger's thread list and in the demo's log readout.
