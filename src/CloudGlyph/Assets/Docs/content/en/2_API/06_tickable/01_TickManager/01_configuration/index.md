# `TickManager` — Configuration

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` lines 1000-1103 (the static surface) and 201-270 (`LoopChannel` implementations).

Every member here takes `string channel = TickManager.DEFAULT_CHANNEL`.

#### `TickManager.DEFAULT_CHANNEL`

**Signature:**
`public const string DEFAULT_CHANNEL = "default";`

**Returns:** `string` — the channel name used by every member whose `channel` argument is omitted.

**Notes:**
- A compile-time constant, so it is usable as a parameter default, an attribute argument and a `switch` label.
- `Examples/Tickable/WPF/Demo/SimState.cs` line 21 shows the pattern worth copying: `public const string Name = TickManager.DEFAULT_CHANNEL;`, then `[Tickable(DemoChannel.Name)]` — the channel is named once and read back on screen.

#### Property: `TickManager.UseAsyncLoop`

**Signature:**
`public static bool UseAsyncLoop { get; set; }`

**Returns:** `bool` — whether a channel drives its frames with `async`/`await` + `Task.Delay` instead of native `Thread`s.

**Notes:**
- The initializer is build-target dependent (lines 1006-1011):

```csharp
public static bool UseAsyncLoop { get; set; } =
#if NET5_0_OR_GREATER
    OperatingSystem.IsBrowser() || OperatingSystem.IsIOS();
#else
    true;
#endif
```

  So on .NET 5+ it starts `true` only in a browser or on iOS, and `false` everywhere else; on the `netstandard2.0` / `netcoreapp3.0` / `netframework4.6.1` targets the API is unavailable and it falls back to `true`.
- Setting this property after channels exist does not change channels that are already running — the value is read at `Start` through `EffectiveUseAsyncLoop`. Use `SetUseAsyncLoop` per channel to override it.

#### Property: `TickManager.ChannelNames`

**Signature:**
`public static IEnumerable<string> ChannelNames { get; }`

**Returns:** `IEnumerable<string>` — the keys of the static `_channels` dictionary, i.e. every channel that has ever been created in this process.

**Notes:**
- A live view over a `ConcurrentDictionary.Keys`; enumerating it while another thread starts a channel is safe but may or may not include that channel.
- Created channels are never removed. There is no `CloseChannel` — only `StopAsync`, which leaves the channel and its time source in place.

#### `TickManager.SetTargetFPS`

**Signature:**
`public static void SetTargetFPS(int fps, string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `fps` | `int` | Target frames per second. Accepted range `1..1000`. |
| `channel` | `string` | Target channel. |

**Returns:** `void`.

**Exceptions:** none — an out-of-range value is **silently ignored**, not clamped and not reported (lines 205-206).

**Example:**
```text
// Source: Examples/Tickable/WPF/Demo/MainWindow.xaml.cs (line 75)
TickManager.SetTargetFPS(60, DemoChannel.Name);
```

**Notes:**
- Queued as a `ConfigChangeRequest` pulled from `_configRequestPool`; the update pump applies it in `ProcessConfigChanges` (lines 768-783), where the target FPS field and the cached frame duration are written together.
- Default 60. The pacing constrains the *sampling cadence*, not the virtual clock — halving the time scale does not halve the frame rate.

#### `TickManager.SetFixedUpdateInterval`

**Signature:**
`public static void SetFixedUpdateInterval(int intervalMs, string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `intervalMs` | `int` | Milliseconds between fixed steps. Accepted range `1..1000`. |
| `channel` | `string` | Target channel. |

**Returns:** `void`.

**Exceptions:** none — out of range is ignored (line 223).

**Example:**
```text
// Source: Examples/Tickable/WPF/Demo/MainWindow.xaml.cs (line 83)
TickManager.SetFixedUpdateInterval(16, DemoChannel.Name);
```

**Notes:**
- Deliberately **not** routed through the config queue: that queue is drained by the *update* loop, while the sampler belongs to the *fixed* loop. The value goes into a volatile field (`_pendingFixedIntervalMs`) and the fixed pump writes `_fixedSampler.Step` on its own thread (lines 457-463) — writing it from the update thread would race `Advance` over the accumulator it resets.
- Default 16 ms. A step of zero is not a legal value, which is why zero is free to mean "nothing pending".

#### `TickManager.SetTimeScale`

**Signature:**
`public static void SetTimeScale(float timeScale, string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `timeScale` | `float` | The rate of the channel's clock, applied verbatim to the bus. `1.0f` is real time. |
| `channel` | `string` | Target channel. |

**Returns:** `void`.

**Exceptions:**
| Exception | Condition |
|---|---|
| `ArgumentOutOfRangeException` | `timeScale` is negative. The bus rejects a backwards clock rather than clamping it. |

**Example:**
```text
// Source: Examples/Tickable/WPF/Demo/MainWindow.xaml.cs (line 91)
TickManager.SetTimeScale(1f, DemoChannel.Name);

// Source: Src/Core/VeloxDev.Core.Test/TimeLine/TickableBusTests.cs (line 252)
Assert.ThrowsExactly<ArgumentOutOfRangeException>(() => TickManager.SetTimeScale(-1f, channel));
```

**Notes:**
- Applied straight to the bus (line 238) instead of through the config queue: the bus serialises its own writers, and the queue only existed when the rate was a channel-owned field.
- Because it is the *clock's* rate, `FrameEventArgs.DeltaTime` and `FrameEventArgs.TotalTime` both follow it, and so does every animation anchored to `TickManager.Bus(channel)` — while the frame *cadence* does not (`TickableBusTests.TheChannelsRateScalesTheAnimationButNotTheFrameCadence`).
- A rate of `0` freezes the clock without pausing it: no frames are dispatched, `IsPaused` stays `false`, `SystemStatus` still reports `"Running"`, and `Resume()` will not restart it. Only a non-zero rate does.

#### `TickManager.ExecuteOnMainThread`

**Signature:**
`public static void ExecuteOnMainThread(Action action, string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `action` | `Action` | Delegate to run at the start of a future frame. |
| `channel` | `string` | Target channel. |

**Returns:** `void`.

**Notes:**
- "Main thread" means the channel's **update** thread, not a UI thread. `ProcessMainThreadOperations` (lines 753-766) drains at most 64 actions per frame before processing config, add and remove queues.
- Actions are wrapped in `try/catch` and failures go to `Debug.WriteLine` only.
- In a UI host you still marshal to the dispatcher yourself, and doing it from inside a hook is the failure mode with no symptom — the engine swallows every hook exception.

#### `TickManager.SetUseAsyncLoop`

**Signature:**
`public static void SetUseAsyncLoop(bool useAsyncLoop, string channel = TickManager.DEFAULT_CHANNEL)`

| Parameter | Type | Description |
|---|---|---|
| `useAsyncLoop` | `bool` | `true` drives this channel's loop with `async`/`await` + `Task.Delay`. |
| `channel` | `string` | Target channel. |

**Returns:** `void`.

**Exceptions:**
| Exception | Condition |
|---|---|
| `InvalidOperationException` | The channel is already running. Stop it first. |

**Example:**
```text
// Source: Src/Core/VeloxDev.Core.Test/TimeLine/TickManagerTests.cs (line 36)
TickManager.SetUseAsyncLoop(true, TestChannel);   // before Start: succeeds

// line 56
Assert.Throws<InvalidOperationException>(() => TickManager.SetUseAsyncLoop(true, ch));  // while running
```

**Notes:**
- Per-channel override of the global `UseAsyncLoop` property, stored as a nullable bool; the running value is `_useAsyncLoopOverride ?? TickManager.UseAsyncLoop`.
- The value takes effect at the next `Start`, not at the call. Both the async path and the thread path drive the same bus, so pausing and rate behave identically on either (`TickableBusTests.TheAsyncLoopPathDrivesTheSameBus`).

#### `TickManager.ClearUseAsyncLoopOverride`

**Signature:**
`public static void ClearUseAsyncLoopOverride(string channel = TickManager.DEFAULT_CHANNEL)`

**Returns:** `void`.

**Exceptions:**
| Exception | Condition |
|---|---|
| `InvalidOperationException` | The channel is already running. |

**Notes:**
- Drops the per-channel override so the channel follows the global `UseAsyncLoop` again. Calling it when no override was ever set does not throw (`TickManagerTests.ClearUseAsyncLoopOverride_WithoutSetting_DoesNotThrow`).
