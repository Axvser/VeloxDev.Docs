# `TickManager` — Lifecycle & Registration

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 1046-1071 (the static wrappers) and 274-441 (`LoopChannel` implementations).

Every member here takes `string channel = TickManager.DEFAULT_CHANNEL` and forwards to the same-named member on the channel's `LoopChannel`. All of them **create the channel on first use** through `GetOrCreateChannel` — except `Pause`, `Resume`, `TogglePause` and the status queries, which are harmless on a channel created empty. `StopAsync` on a channel that was never started returns a completed task.

#### `TickManager.Start`

**Signature:**
`public static void Start(string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `channel` | `string` | Channel to create (if needed) and start. |

**Returns:** `void`.

**Exceptions:** none. Starting an already-running channel is a no-op — `LoopChannel.Start` opens with `if (_isRunning) return;` (line 276).

**Example:**
```text
// Source: Examples/Tickable/WPF/Demo/MainWindow.xaml.cs (line 60)
TickManager.Start(DemoChannel.Name);
```

**Notes:**
- Spawns the update and fixed-update threads (`VeloxDev.Update[<channel>]`, `VeloxDev.FixedUpdate[<channel>]`, `ThreadPriority.AboveNormal`, `IsBackground = true`), or the two async loops when `EffectiveUseAsyncLoop` is true.
- Re-anchors both samplers to "now" (lines 288-289) and calls `_bus.Resume()` (line 293), so a pause left over from a previous lifecycle does not survive.
- Rebuilds the cached, execution-order-sorted behaviour array, then raises `Started` → `OnChannelStarted`.

#### `TickManager.StopAsync`

**Signature:**
`public static Task StopAsync(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `Task` — completes when the pumps have stopped, the queues are cleared and the statistics are reset.

**Exceptions:** none observable. The pump join is wrapped in `try { … } catch (Exception) { }` and the cleanup lives in `finally`, so the returned task does not fault.

**Example:**
```text
// Source: Examples/Tickable/WPF/Demo/MainWindow.xaml.cs (line 69)
_ = TickManager.StopAsync(DemoChannel.Name);
```

**Notes:**
- Returns immediately (`Task.CompletedTask`-like) if the channel is not running, and in that case does **not** raise `OnChannelStopped`.
- Cancels the pumps, then waits up to `RESTART_SHUTDOWN_TIMEOUT_MS` (1 s) for them. Waits are `Thread.Join` for the thread path, `Task.WhenAny(Task.WhenAll(...), Task.Delay(1000))` for the async path.
- Clears a pause on the way down (`_bus.Resume()`, line 339) — a paused channel that is stopped comes back runnable. It does **not** lift a rate of `0`.
- Resets `TotalTime`, `TotalFrames`, `CurrentFPS` and the config cache timestamp, and drains all four queues.
- Safe against a channel parked by `Pause()`: the park observes the cancellation token, so the cancel propagates into it.

#### `TickManager.Pause`

**Signature:**
`public static void Pause(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `void`.

**Exceptions:** none.

**Notes:**
- No-op when the channel is not running or already paused (line 386).
- Sets `IsPaused` on the channel's time source and raises `Paused` → `OnChannelPaused`.
- The pumps park on `WaitWhileStalledAsync` rather than polling, so a paused channel makes no wake-ups at all.
- Because the paused state belongs to the shared time source, an animation anchored to `TickManager.Bus(channel)` freezes in the same instant.

#### `TickManager.Resume`

**Signature:**
`public static void Resume(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `void`.

**Exceptions:** none.

**Notes:**
- No-op when the channel is not running or not paused (line 399).
- Raises `Resumed` → `OnChannelResumed`.
- After a rate of `0` this lifts the pause without making the clock advance — the channel stays parked until a non-zero rate is set (`LoopChannel.Resume` remarks, lines 391-396).

#### `TickManager.TogglePause`

**Signature:**
`public static void TogglePause(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `void`.

**Notes:**
- Implemented as `if (_bus.IsPaused) Resume(); else Pause();` (line 440), so both branches inherit the guards above: on a stopped channel it is a no-op.
- Raises `OnChannelPaused` or `OnChannelResumed`, never both.

#### `TickManager.RestartAsync`

**Signature:**
`public static Task RestartAsync(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `Task` — completes when the channel has stopped, settled and started again.

**Notes:**
- `StopAsync`, then wait up to 1 s for `!_isRunning && !_isUpdateThreadActive && !_isFixedUpdateThreadActive`; on timeout it logs `Warning: Force restarting after timeout` to `Debug.WriteLine` and calls `ForceCleanup`.
- Then wait up to 500 ms for all four queues to empty (the result is ignored), then `Start()`.
- **Does not re-run `Awake` / `Start`** on registered behaviours. Only `CloseTickable()` + `InitializeTickable()` does that.

#### `TickManager.RegisterBehaviour`

**Signature:**
`public static void RegisterBehaviour(ITickable behavior, string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `behavior` | `ITickable` | The behaviour instance to add. `null` is accepted and ignored. |
| `channel` | `string` | The target channel; created if it does not exist. |

**Returns:** `void`.

**Exceptions:** none. `null` is filtered by `if (behavior != null) _addQueue.Enqueue(behavior);` (line 432).

**Example:**
```text
// Source: the generated InitializeTickable() (TickWriter.cs line 83)
TickManager.RegisterBehaviour(this, "demo");
```

**Notes:**
- The call only enqueues. The update pump drains the queue in `ProcessAddedBehaviors` (lines 785-801) before sampling the next frame, so `InvokeAwake()` then `InvokeStart()` run on the update thread, **before the first frame body**, whether registration happened before or after `Start`.
- Behaviours are keyed by `RuntimeHelpers.GetHashCode(behavior)`, so registering the same instance twice replaces the wrapper rather than adding a second one — but it still runs `InvokeAwake` / `InvokeStart` again on the replacement.
- Execution order is registration order: each wrapper takes `Interlocked.Increment(ref _instanceCounter)` as its `ExecutionOrder`, and the cached array is insertion-sorted on it.
- A registering behaviour is **not** started immediately: if the channel is not running, `Awake` / `Start` wait for the first frame after `Start`.

#### `TickManager.UnregisterBehaviour`

**Signature:**
`public static void UnregisterBehaviour(ITickable behavior, string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `behavior` | `ITickable` | The instance to remove. `null` is accepted and ignored. |
| `channel` | `string` | The channel it was registered on. |

**Returns:** `void`.

**Exceptions:** none.

**Example:**
```text
// Source: the generated CloseTickable() (TickWriter.cs line 88)
TickManager.UnregisterBehaviour(this, "demo");
```

**Notes:**
- Enqueues; the drain (`ProcessRemovedBehaviors`, lines 803-816) removes the wrapper, clears it and returns it to `_wrapperPool`.
- Removal is **silent**: `UnregisterBehaviour` removes the wrapper and invokes no hook on the behaviour — the loop never calls a "close" callback. (`CloseTickable()` *does* exist on `ITickable`, but it is the method that *performs* the unregistration, so unregistering does not call it back.) Any cleanup the behaviour needs is the caller's to perform.
- After removal the instance still implements `ITickable` and can be registered again — and doing so runs `Awake` and `Start` once more on a fresh wrapper.
