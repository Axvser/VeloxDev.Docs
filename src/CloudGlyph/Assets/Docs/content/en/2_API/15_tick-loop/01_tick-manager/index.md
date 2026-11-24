# Tick Manager

The static owner of every channel: threads, frame rate, fixed step, time scale and the registered behaviours. Namespace `VeloxDev.TimeLine`.

## VeloxDev.TimeLine

### Class: TickManager

**Signature:** `public static class TickManager`

**Constant**

| Member | Type | Value |
|---|---|---|
| `DEFAULT_CHANNEL` | `const string` | `"default"` |

**Properties**

| Member | Type | Description |
|---|---|---|
| `UseAsyncLoop` | `static bool { get; set; }` | Use `async` / `Task.Delay` instead of native threads. Defaults to `true` on browser and iOS, otherwise `#if NET5_0_OR_GREATER` decides per platform. |
| `ChannelNames` | `static IEnumerable<string> { get; }` | The names of all created channels. |

**Events**

| Member | Signature | Description |
|---|---|---|
| `OnChannelStarted` | `static event EventHandler<TickChannelEventArgs>?` | A channel started. |
| `OnChannelPaused` | `static event EventHandler<TickChannelEventArgs>?` | A channel paused. |
| `OnChannelResumed` | `static event EventHandler<TickChannelEventArgs>?` | A channel resumed. |
| `OnChannelStopped` | `static event EventHandler<TickChannelEventArgs>?` | A channel stopped. |
| `OnBehaviorError` | `static event EventHandler<TickBehaviorErrorEventArgs>?` | A behaviour or main-thread action threw. The loop keeps running; without a subscriber the error only reaches `Debug`. |

**Lifecycle**

| Member | Signature | Description |
|---|---|---|
| `Start` | `static void Start(string channel = DEFAULT_CHANNEL)` | Starts or resumes the channel. Idempotent while running. |
| `StopAsync` | `static Task StopAsync(string channel = DEFAULT_CHANNEL)` | Stops the channel, joins its loops and resets statistics. |
| `Pause` | `static void Pause(string channel = DEFAULT_CHANNEL)` | Freezes the clock and both loops. |
| `Resume` | `static void Resume(string channel = DEFAULT_CHANNEL)` | Resumes at the rate last set. |
| `RestartAsync` | `static Task RestartAsync(string channel = DEFAULT_CHANNEL)` | Stops, waits for shutdown, then starts again. |
| `TogglePause` | `static void TogglePause(string channel = DEFAULT_CHANNEL)` | Pauses when running, resumes when paused. |
| `RegisterBehaviour` | `static void RegisterBehaviour(ITickable behavior, string channel = DEFAULT_CHANNEL)` | Queues a behaviour; `Awake` and `Start` run on the channel's next drain. |
| `UnregisterBehaviour` | `static void UnregisterBehaviour(ITickable behavior, string channel = DEFAULT_CHANNEL)` | Queues unregistration. |

**Configuration**

| Member | Signature | Description |
|---|---|---|
| `SetTargetFPS` | `static void SetTargetFPS(int fps, string channel = DEFAULT_CHANNEL)` | Values outside 1–1000 are ignored. |
| `SetFixedUpdateInterval` | `static void SetFixedUpdateInterval(int intervalMs, string channel = DEFAULT_CHANNEL)` | Fixed step in milliseconds; values outside 1–1000 are ignored. |
| `SetTimeScale` | `static void SetTimeScale(float timeScale, string channel = DEFAULT_CHANNEL)` | Multiplies elapsed time. `0` freezes without setting `IsPaused`; a negative value throws `ArgumentOutOfRangeException`. |
| `ExecuteOnMainThread` | `static void ExecuteOnMainThread(Action action, string channel = DEFAULT_CHANNEL)` | Queues work onto the channel's update thread. |
| `SetUseAsyncLoop` | `static void SetUseAsyncLoop(bool useAsyncLoop, string channel = DEFAULT_CHANNEL)` | Per-channel override. Throws `InvalidOperationException` while the channel is running. |
| `ClearUseAsyncLoopOverride` | `static void ClearUseAsyncLoopOverride(string channel = DEFAULT_CHANNEL)` | Drops the per-channel override. Throws `InvalidOperationException` while running. |

**Status queries**

| Member | Signature | Description |
|---|---|---|
| `IsRunning` | `static bool IsRunning(string channel = DEFAULT_CHANNEL)` | Channel exists and is running. |
| `IsPaused` | `static bool IsPaused(string channel = DEFAULT_CHANNEL)` | The clock is paused. A zero rate is not a pause. |
| `CurrentFPS` | `static int CurrentFPS(string channel = DEFAULT_CHANNEL)` | Measured frames per second. |
| `TargetFPS` | `static int TargetFPS(string channel = DEFAULT_CHANNEL)` | Requested frames per second; `60` for an unknown channel. |
| `TotalTime` | `static TimeSpan TotalTime(string channel = DEFAULT_CHANNEL)` | Virtual time since the clock started. |
| `TotalTimeMs` | `static long TotalTimeMs(string channel = DEFAULT_CHANNEL)` | `TotalTime` in milliseconds. |
| `TotalFrames` | `static long TotalFrames(string channel = DEFAULT_CHANNEL)` | Frames produced. |
| `ActiveBehaviorCount` | `static int ActiveBehaviorCount(string channel = DEFAULT_CHANNEL)` | Registered behaviours. |
| `TimeScale` | `static float TimeScale(string channel = DEFAULT_CHANNEL)` | The current rate; `1` for an unknown channel. |
| `Bus` | `static ITimeSourceControl? Bus(string channel = DEFAULT_CHANNEL)` | The channel's transport, or `null` when the channel does not exist. Pass it to an animation's `Execute(target, timeline)` overload so one pause and one rate move frames and animations together. |
| `SystemStatus` | `static string SystemStatus(string channel = DEFAULT_CHANNEL)` | `"Stopped"`, `"Paused"` or `"Running"`. |
| `IsUpdateThreadAlive` | `static bool IsUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | The update loop's thread/task is alive. |
| `IsFixedUpdateThreadAlive` | `static bool IsFixedUpdateThreadAlive(string channel = DEFAULT_CHANNEL)` | The fixed-update loop's thread/task is alive. |

### Class: TickChannelEventArgs

**Signature:** `public sealed class TickChannelEventArgs(string channelName) : EventArgs`

| Member | Type | Description |
|---|---|---|
| `ChannelName` | `string { get; }` | The channel the event belongs to. |

### Class: TickBehaviorErrorEventArgs

**Signature:** `public sealed class TickBehaviorErrorEventArgs(string channelName, string stage, Exception exception) : EventArgs`

| Member | Type | Description |
|---|---|---|
| `ChannelName` | `string { get; }` | The channel where the error happened. |
| `Stage` | `string { get; }` | `Awake`, `Start`, `Update`, `LateUpdate`, `FixedUpdate` or `MainThread`. |
| `Exception` | `Exception { get; }` | The thrown exception. |

## Behavior notes

- Each channel owns two loops (update, fixed-update), its own target FPS, fixed step and time scale. Behaviours on one channel never run on another's thread.
- Behaviours run sequentially in registration order. A throwing behaviour is reported through `OnBehaviorError` and does not stop the loop.
- `Update` and `LateUpdate` share one `FrameEventArgs`; setting `Handled` in `Update` skips the remaining `Update` behaviours and all `LateUpdate` behaviours for that frame. `FixedUpdate` creates its own args per step and is unaffected.
- `FixedUpdate` repays owed steps after a stall: one wake-up may produce several calls with consecutive `TotalTime` values.
- `SetTimeScale(0)` freezes the clock but leaves `IsPaused` false and `SystemStatus` `"Running"`. Only a non-zero rate starts it again.

## Example

```csharp
using System;
using System.Threading.Tasks;
using VeloxDev.TimeLine;

var ticker = new Ticker();
ticker.InitializeTickable();
TickManager.Start("quickstart");

await Task.Delay(400);
Console.WriteLine($"running={TickManager.IsRunning("quickstart")} frames={TickManager.TotalFrames("quickstart")}");

TickManager.SetTargetFPS(30, "quickstart");
TickManager.SetTimeScale(0.5f, "quickstart");
var bus = TickManager.Bus("quickstart");

await TickManager.StopAsync("quickstart");
ticker.CloseTickable();
```

See [Tickable contract](../00_tickable-contract/index.md) for the class shape and the [quick start](../../../1_QuickStart/15_tick-loop/index.md) for the complete program.
