# MonoBehaviour — Configure & Run the Loop

All control flows through the static `VeloxDev.TimeLine.MonoBehaviourManager`. Every method takes an optional `channel` argument that defaults to the `"default"` channel; a channel is created lazily the first time a configuration, registration or lifecycle call names it. Behaviours, configuration and lifecycle are all per channel.

## 1. Configuration knobs

The per-channel settings are queued as change requests and applied at the start of the next frame (`Src/Core/VeloxDev.Core/TimeLine/MonoBehaviourManager.cs`).

```csharp
MonoBehaviourManager.SetTargetFPS(60, "game");            // valid 1..1000; out of range is ignored
MonoBehaviourManager.SetFixedUpdateInterval(16, "game");  // ms, valid 1..1000; out of range is ignored
MonoBehaviourManager.SetTimeScale(1.0f, "game");          // clamped to 0..10
MonoBehaviourManager.ExecuteOnMainThread(() => DoUiWork(), "game"); // runs at the top of the next update frame
```

- `SetTargetFPS` paces the Update pump (default 60).
- `SetFixedUpdateInterval` sets the fixed-timestep period of the FixedUpdate pump in milliseconds (default 16).
- `SetTimeScale` scales `FrameEventArgs.DeltaTime` for every behaviour that frame (`0` freezes delta time without stopping the pump).
- `ExecuteOnMainThread` queues an `Action` that the Update pump runs at the top of its next frame — it runs on the *loop* thread, not on any UI thread.

**Expected result:** configuration is applied on the next frame boundary; status queries reflect the new values once applied.

## 2. Thread or async-loop mode

Each pump of a channel runs either on a background `Thread` (threads are named `VeloxDev.Update[channel]` / `VeloxDev.FixedUpdate[channel]`) or on an `async` task. The switch is `MonoBehaviourManager.UseAsyncLoop` (global) with an optional per-channel override:

```csharp
MonoBehaviourManager.SetUseAsyncLoop(true, "game");   // force async/await + Task.Delay for this channel
MonoBehaviourManager.ClearUseAsyncLoopOverride("game");
```

The default is environment-sensitive (`MonoBehaviourManager.cs`): on .NET 5+ `UseAsyncLoop` defaults to `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()` — so WASM and iOS NativeAOT use the async path (no `System.Threading.Thread`), while desktop .NET 5+ uses native threads. On older targets (netstandard2.0 / netcoreapp3.0 / .NET Framework) the property defaults to `true`. Setting the override while a channel is already running throws `InvalidOperationException`; set it before `Start` (the tests on the [Verify & Complete Code](../06_verify-and-complete-code/) page pin this).

**Expected result:** `IsUpdateThreadAlive("game")` / `IsFixedUpdateThreadAlive("game")` report whether the corresponding pump is actively ticking, whichever mechanism drives it.

## 3. Start and stop

```csharp
var counter = new FrameCounter();        // registered in its constructor (queued)
MonoBehaviourManager.Start("game");      // returns immediately; first frame drains the add-queue
// Awake() and Start() fire here, on the loop thread.
await MonoBehaviourManager.StopAsync("game");
```

`Start` spawns the pumps, rebuilds the behaviour list and fires `OnChannelStarted`; it returns before the first frame, so the `Awake` / `Start` hooks of queued behaviours run a moment later on the loop thread. `StopAsync` cancels the pumps (1 s shutdown timeout), resets the channel statistics (`CurrentFPS`, `TotalFrames`, `TotalTime`, ...), clears the pending add/remove/config/main-thread queues and fires `OnChannelStopped`. Registered behaviours are kept — they simply become active again on the next `Start` of the same channel (their `Awake`/`Start` do not re-run).

**Expected result:** right after `Start`, `SystemStatus("game")` returns `"Running"`; after `StopAsync` it returns `"Stopped"`.

## 4. Status queries

```csharp
Console.WriteLine(MonoBehaviourManager.SystemStatus("game"));        // "Running" | "Paused" | "Stopped"
Console.WriteLine(MonoBehaviourManager.IsRunning("game"));
Console.WriteLine(MonoBehaviourManager.IsPaused("game"));
Console.WriteLine(MonoBehaviourManager.CurrentFPS("game"));          // measured, updated ~once per second
Console.WriteLine(MonoBehaviourManager.TargetFPS("game"));
Console.WriteLine(MonoBehaviourManager.ActiveBehaviorCount("game"));
Console.WriteLine(MonoBehaviourManager.TotalFrames("game"));
Console.WriteLine(MonoBehaviourManager.TotalTimeMs("game"));
```

For a channel that has not been created yet the queries return the neutral defaults (`0` / `"Stopped"` / the default target FPS). `ChannelNames` enumerates the channels created so far.

**Expected result:** while the loop runs, `IsRunning` is `true`, `CurrentFPS` tracks the measured frame rate and `ActiveBehaviorCount` equals the number of behaviours picked up by the channel.

## 5. Channel events

The manager exposes four static events; each fires synchronously on the thread that calls the lifecycle method, with a `MonoBehaviourChannelEventArgs` carrying `ChannelName`:

```csharp
MonoBehaviourManager.OnChannelStarted += (s, e) => Console.WriteLine($"[OnChannelStarted] {e.ChannelName}");
MonoBehaviourManager.OnChannelPaused  += (s, e) => Console.WriteLine($"[OnChannelPaused]  {e.ChannelName}");
MonoBehaviourManager.OnChannelResumed += (s, e) => Console.WriteLine($"[OnChannelResumed] {e.ChannelName}");
MonoBehaviourManager.OnChannelStopped += (s, e) => Console.WriteLine($"[OnChannelStopped] {e.ChannelName}");
```

`RestartAsync` therefore raises `OnChannelStopped` followed by `OnChannelStarted`.

**Expected result:** subscribing before `Start` prints one event per lifecycle transition of the channel.

## 6. Cancellation and error handling inside the loop

- Each pump owns a `CancellationTokenSource`; `StopAsync` cancels it, and the pumps treat cancellation as a normal exit (no rethrow escapes the loop).
- An exception thrown inside a behaviour hook is caught by the channel, logged with `Debug.WriteLine` (a no-op in release without a debugger) and does not stop the loop; the remaining behaviours in that frame still run because the exception is swallowed per wrapper.
- `FrameEventArgs.DeltaTime` reflects real elapsed time scaled by `TimeScale`; a `TimeScale` of `0` yields a zero `DeltaTime` for that frame.

**Expected result:** a hook that throws once does not kill the channel; stopping the loop joins the pumps within the shutdown timeout and leaves the channel in `"Stopped"`.

## Run declaration

- ⚠️ Statically verified only — the method names, defaults and clamps on this page are transcribed from `MonoBehaviourManager.cs`; no code on this page was compiled on its own. The same calls are exercised end-to-end in the program on the [Verify & Complete Code](../06_verify-and-complete-code/) page.
