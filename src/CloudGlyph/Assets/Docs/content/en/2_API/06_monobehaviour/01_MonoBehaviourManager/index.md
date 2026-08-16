# MonoBehaviour — `MonoBehaviourManager`

Constant: `public const string DEFAULT_CHANNEL = "default";`

#### Lifecycle

#### `MonoBehaviourManager.Start`

**Signature:**
`public static void Start(string channel = DEFAULT_CHANNEL)`

**Returns:** `void`

**Example:**
```text
// Source: Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs (line 218)
MonoBehaviourManager.Start();
```

**Notes:**
- Creates the channel on first use; spawns the Update + FixedUpdate threads (or async tasks when `UseAsyncLoop` is `true`); fires `OnChannelStarted`.

#### `MonoBehaviourManager.StopAsync`

**Signature:**
`public static Task StopAsync(string channel = DEFAULT_CHANNEL)`

**Returns:** `Task` — completes when the threads are joined (1 s timeout), queues cleared and statistics reset.

**Example:**
```text
// Source: Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs (line 113)
await MonoBehaviourManager.StopAsync();
```

**Notes:**
- Fires `OnChannelStopped`; the channel can be restarted afterwards.

#### `MonoBehaviourManager.Pause`

**Signature:**
`public static void Pause(string channel = DEFAULT_CHANNEL)`

**Returns:** `void`

**Notes:**
- No-op if the channel is not running or already paused. The loops sleep while paused; fires `OnChannelPaused`.

#### `MonoBehaviourManager.Resume`

**Signature:**
`public static void Resume(string channel = DEFAULT_CHANNEL)`

**Returns:** `void`

**Notes:**
- No-op if not paused. Fires `OnChannelResumed`.

#### `MonoBehaviourManager.RestartAsync`

**Signature:**
`public static Task RestartAsync(string channel = DEFAULT_CHANNEL)`

**Returns:** `Task` — completes when the channel has stopped and started again.

**Notes:**
- Stops, waits for shutdown confirmation (force-cleanup after 1 s), waits for queues to drain, then calls `Start`.

#### `MonoBehaviourManager.TogglePause`

**Signature:**
`public static void TogglePause(string channel = DEFAULT_CHANNEL)`

**Returns:** `void`

**Notes:**
- Pauses if running, resumes if paused; delegates to `Pause`/`Resume`.

#### Registration

#### `MonoBehaviourManager.RegisterBehaviour`

**Signature:**
`public static void RegisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `behavior` | `IMonoBehaviour` | The behaviour instance to add. |
| `channel` | `string` | The target channel. |

**Returns:** `void`

**Notes:**
- Queued and processed at the start of the next frame; the manager calls `InvokeAwake()` then `InvokeStart()` on registration.

#### `MonoBehaviourManager.UnregisterBehaviour`

**Signature:**
`public static void UnregisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `behavior` | `IMonoBehaviour` | The behaviour instance to remove. |
| `channel` | `string` | The channel it is registered on. |

**Returns:** `void`

**Notes:**
- Queued and processed at the start of the next frame; the wrapper is returned to the object pool.

#### Configuration

#### `MonoBehaviourManager.SetTargetFPS`

**Signature:**
`public static void SetTargetFPS(int fps, string channel = DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `fps` | `int` | Target frames per second, clamped to `1..1000`. |

**Returns:** `void`

**Example:**
```text
// Source: Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs (line 50)
MonoBehaviourManager.SetTargetFPS(30, "game");
```

**Notes:**
- Applied on the next frame boundary via the config queue.

#### `MonoBehaviourManager.SetFixedUpdateInterval`

**Signature:**
`public static void SetFixedUpdateInterval(int intervalMs, string channel = DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `intervalMs` | `int` | Milliseconds between fixed updates, clamped to `1..1000`. Default `16`. |

**Returns:** `void`

#### `MonoBehaviourManager.SetTimeScale`

**Signature:**
`public static void SetTimeScale(float timeScale, string channel = DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `timeScale` | `float` | Time scale applied to `FrameEventArgs.DeltaTime`, clamped to `0..10`. Default `1.0`. |

**Returns:** `void`

**Example:**
```text
// Runtime probe, 2026-08-17: SetTimeScale(0.5f) halved DeltaTime (ratio ≈ 0.49)
MonoBehaviourManager.SetTimeScale(0.5f, "game");
```

#### `MonoBehaviourManager.ExecuteOnMainThread`

**Signature:**
`public static void ExecuteOnMainThread(Action action, string channel = DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `action` | `Action` | A delegate executed at the start of the next frame. |

**Returns:** `void`

**Notes:**
- Up to 64 actions per frame are drained by the update thread (see `ProcessMainThreadOperations`). In a UI host you still marshal to the dispatcher yourself.

#### `MonoBehaviourManager.SetUseAsyncLoop`

**Signature:**
`public static void SetUseAsyncLoop(bool useAsyncLoop, string channel = DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `useAsyncLoop` | `bool` | `true` drives the loop with `async`/`await` + `Task.Delay` instead of native threads. |

**Returns:** `void`

**Exceptions:**
| Exception | Condition |
|---|---|
| `InvalidOperationException` | The channel is already running. |

**Notes:**
- Overrides the global `UseAsyncLoop` for this channel only (verified by `MonoBehaviourManagerTests.SetUseAsyncLoop_*`).

#### `MonoBehaviourManager.ClearUseAsyncLoopOverride`

**Signature:**
`public static void ClearUseAsyncLoopOverride(string channel = DEFAULT_CHANNEL)`

**Returns:** `void`

**Exceptions:**
| Exception | Condition |
|---|---|
| `InvalidOperationException` | The channel is already running. |

**Notes:**
- Removes this channel's override and falls back to the global `UseAsyncLoop`.

#### Status queries

All status queries share the shape `(string channel = DEFAULT_CHANNEL)` and return `false`/`0`/`"Stopped"` when the channel has never been created.

| Member | Returns |
|---|---|
| `IsRunning` | `bool` |
| `IsPaused` | `bool` |
| `CurrentFPS` | `int` |
| `TargetFPS` | `int` |
| `TotalTime` | `TimeSpan` |
| `TotalTimeMs` | `long` |
| `TotalFrames` | `long` |
| `ActiveBehaviorCount` | `int` |
| `TimeScale` | `float` |
| `SystemStatus` | `string` — `"Stopped"` / `"Paused"` / `"Running"` |
| `IsUpdateThreadAlive` | `bool` (with a 2 s inactivity timeout) |
| `IsFixedUpdateThreadAlive` | `bool` (with a 2 s inactivity timeout) |

**Example (status queries):**
```text
// Source: Examples/MonoBehaviour/WPF/Demo/MainWindow.xaml.cs (lines 182-188)
MonoBehaviourManager.IsRunning();
MonoBehaviourManager.CurrentFPS();
MonoBehaviourManager.ActiveBehaviorCount();
MonoBehaviourManager.IsUpdateThreadAlive();
```

#### Events

#### `MonoBehaviourManager.OnChannelStarted`

**Signature:**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStarted`

**Notes:**
- Raised with the channel name when a channel loop starts.

#### `MonoBehaviourManager.OnChannelPaused`

**Signature:**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelPaused`

#### `MonoBehaviourManager.OnChannelResumed`

**Signature:**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelResumed`

#### `MonoBehaviourManager.OnChannelStopped`

**Signature:**
`public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStopped`

**Example (subscribing):**
```text
// Runtime probe, 2026-08-17: printed "event OnChannelStarted  -> demo"
MonoBehaviourManager.OnChannelStarted += (s, e) => Console.WriteLine(e.ChannelName);
```

#### Properties

#### `MonoBehaviourManager.UseAsyncLoop`

**Signature:**
`public static bool UseAsyncLoop { get; set; }`

**Notes:**
- Auto-enabled on browsers (WASM) and iOS via `OperatingSystem.IsBrowser() || OperatingSystem.IsIOS()`; otherwise defaults to `false` (native threads).

#### `MonoBehaviourManager.ChannelNames`

**Signature:**
`public static IEnumerable<string> ChannelNames { get; }`

**Returns:** `IEnumerable<string>` — the names of all created channels.
