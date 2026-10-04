# `TickManager` — Status Queries

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 1105-1156.

All thirteen members take `string channel = TickManager.DEFAULT_CHANNEL`, are `static`, and are safe to call from any thread. Their common contract is the one worth stating once:

> A query never creates a channel, and it never throws. When the named channel does not exist it returns the "stopped" answer — `false`, `0`, `TimeSpan.Zero`, `"Stopped"`, or `null` for `Bus`.

Each is implemented as `_channels.TryGetValue(channel, out var c) ? c.X : <fallback>`.

| Member | Signature | Returns when the channel exists | Returns when it does not |
|---|---|---|---|
| `IsRunning` | `public static bool IsRunning(string channel = DEFAULT_CHANNEL)` | `_isRunning` — pumps started and not stopped | `false` |
| `IsPaused` | `public static bool IsPaused(string channel = DEFAULT_CHANNEL)` | `_bus.IsPaused` | `false` |
| `CurrentFPS` | `public static int CurrentFPS(string channel = DEFAULT_CHANNEL)` | Measured frames per second, refreshed once per wall-clock second | `0` |
| `TargetFPS` | `public static int TargetFPS(string channel = DEFAULT_CHANNEL)` | The configured target | `60` (`DEFAULT_TARGET_FPS`) |
| `TotalTime` | `public static TimeSpan TotalTime(string channel = DEFAULT_CHANNEL)` | Virtual time since `Start` | `TimeSpan.Zero` |
| `TotalTimeMs` | `public static long TotalTimeMs(string channel = DEFAULT_CHANNEL)` | `(long)TotalTime.TotalMilliseconds` | `0` |
| `TotalFrames` | `public static long TotalFrames(string channel = DEFAULT_CHANNEL)` | Frames completed since `Start` | `0` |
| `ActiveBehaviorCount` | `public static int ActiveBehaviorCount(string channel = DEFAULT_CHANNEL)` | Size of the behaviour dictionary | `0` |
| `TimeScale` | `public static float TimeScale(string channel = DEFAULT_CHANNEL)` | The clock's rate | `1.0f` (`DEFAULT_TIME_SCALE`) |
| `SystemStatus` | `public static string SystemStatus(string channel = DEFAULT_CHANNEL)` | `"Stopped"` / `"Paused"` / `"Running"` | `"Stopped"` |
| `IsUpdateThreadAlive` | `public static bool IsUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | See below | `false` |
| `IsFixedUpdateThreadAlive` | `public static bool IsFixedUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | See below | `false` |
| `Bus` | `public static ITimeSourceControl? Bus(string channel = DEFAULT_CHANNEL)` | The channel's time source | `null` |

#### `TickManager.SystemStatus`

**Signature:**
`public static string SystemStatus(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** one of three literals — `"Stopped"` when `!_isRunning`, `"Paused"` when the bus is paused, `"Running"` otherwise (line 185).

**Notes:**
- The strings are the public contract; there is no enum.
- **`"Running"` is reported at a rate of `0`.** A frozen clock is not a pause, so this is the one status the query does not cover. Use `TickManager.Bus(channel)?.IsAdvancing` for "is the clock actually moving" — the WPF demo prints both side by side for exactly this reason (`MainWindow.xaml.cs` lines 307-324).

#### `TickManager.IsUpdateThreadAlive` / `TickManager.IsFixedUpdateThreadAlive`

**Signature:**
`public static bool IsUpdateThreadAlive(string channel = TickManager.DEFAULT_CHANNEL)`
`public static bool IsFixedUpdateThreadAlive(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `bool` — `true` while the pump is running, including while it is parked.

**Notes:**
- The implementation (lines 193-197) is not an inactivity test:

```csharp
public bool IsUpdateThreadAlive => _isRunning && _isUpdateThreadActive &&
    (!_bus.IsAdvancing || IsRecentActivity(Interlocked.Read(ref _updateThreadLastActivityTimestamp)));
```

  The `!_bus.IsAdvancing ||` term is what keeps a paused channel from being reported as dead: a parked pump has no activity by construction, and the 2 s (`THREAD_INACTIVITY_TIMEOUT_MS`) window would otherwise expire on it.
- `IsRecentActivity` also returns `false` for a timestamp of `0`, which is the state right after a start before the pump's first iteration.

**Example:**
```text
// Source: Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs (lines 151-155)
// 旧实现靠每 10ms 醒来轮询暂停标志，暂停中的循环仍然活着；这里改为 park 在总线上，
// 所以「线程还活着吗」不能再用「最近有没有活动」来判断。
Assert.IsTrue(TickManager.IsUpdateThreadAlive(channel),
    "a parked loop is alive, not dead — the liveness query has to account for the stalled clock");
Assert.IsTrue(TickManager.IsFixedUpdateThreadAlive(channel));
```

#### `TickManager.Bus`

**Signature:**
`public static ITimeSourceControl? Bus(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `ITimeSourceControl?` — the channel's time source, or `null` when the channel has never been created.

**Exceptions:** none.

**Example:**
```text
// Source: Examples/Tickable/WPF/Demo/MainWindow.xaml.cs (line 307)
var bus = TickManager.Bus(DemoChannel.Name);
$"IsAdvancing {bus?.IsAdvancing}  IsPaused {bus?.IsPaused}  Epoch {bus?.Epoch}  Rate {bus?.Rate ?? 0:F2}×"
```

**Notes:**
- `null` is the deliberate answer for a channel that was never started: a query must not create one as a side effect (`TickableBusTests.BusIsNullForAChannelThatWasNeverStarted`).
- One channel is one transport for its whole life; two calls return the same instance (`TickableBusTests.BusIsStableForAStartedChannel`).
- The source is resolved once, at channel construction, through `TimerCore.CreateTimeSource<ITimeSourceControl>()` (line 116), so a platform can substitute its own by registering one there. The default implementation is `TimeSourceCore` in `VeloxDev.Timing`.
- Passing it to `TransitionCore.Execute(target, timeline)` is what makes one `Pause()` stop the frame callbacks and the animation together, and what makes the channel's rate multiply both (`TickableBusTests.PausingAChannelStopsItsFramesAndTheAnimationAnchoredToIt`).
- The members a consumer normally touches: `IsAdvancing`, `IsPaused`, `Rate`, `Position`, `Epoch`, `Pause()`, `Resume()`, `SetRate(double)`, `WaitWhileStalledAsync(CancellationToken)`.

#### `TickManager.ActiveBehaviorCount`

**Signature:**
`public static int ActiveBehaviorCount(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `int` — the number of entries in the channel's behaviour dictionary.

**Notes:**
- Counts **drained** registrations, not queued ones: `RegisterBehaviour` increments it only when the update pump processes the queue. A behaviour registered and queried within the same frame may not be counted yet.
- A behaviour registered twice counts once — the dictionary is keyed by `RuntimeHelpers.GetHashCode(behavior)`.
- The count drops only after `UnregisterBehaviour` has also been drained.
