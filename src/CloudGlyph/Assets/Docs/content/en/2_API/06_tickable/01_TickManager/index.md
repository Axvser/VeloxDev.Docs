# `TickManager`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`. A static, thread-safe facade over per-name loop channels.

```csharp
public static class TickManager
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TickManager.cs` (1163 lines).

`TickManager` is the only public entry point to the feature's runtime. Every member is `static`; every member except `ChannelNames` takes a trailing `string channel = DEFAULT_CHANNEL` argument. Channels are created lazily by `GetOrCreateChannel` and held in a process-wide `ConcurrentDictionary<string, LoopChannel>` (`_channels`, line 1017) — so the manager is process-global state and its channels outlive any behaviour registered on them.

## What is public and what is not

| Public | Private (must not appear in user code) |
|---|---|
| The 34 static members documented below | nested `LoopChannel`, `BehaviorWrapper`, `ConfigChangeRequest`, `ObjectPool<T>` |
| `TickChannelEventArgs` (a separate top-level type) | `GetOrCreateChannel`, `RebuildCachedWrappers`, `ProcessAddedBehaviors`, `ExecuteBehaviors*Sync`, `CreateFrameEventArgs`, `Sleep`, `ForceCleanup`, … |

`LoopChannel` is `private sealed` (line 99). It is where the two pumps, the channel's time source and the channel's own events live, and nothing outside `TickManager` can name it. The only public door to a channel's clock is `TickManager.Bus`.

## Member index

| Group | Members | Page |
|---|---|---|
| Lifecycle & registration | `Start`, `StopAsync`, `Pause`, `Resume`, `TogglePause`, `RestartAsync`, `RegisterBehaviour`, `UnregisterBehaviour` | [lifecycle](00_lifecycle/index.md) |
| Configuration | `DEFAULT_CHANNEL`, `UseAsyncLoop`, `ChannelNames`, `SetTargetFPS`, `SetFixedUpdateInterval`, `SetTimeScale`, `ExecuteOnMainThread`, `SetUseAsyncLoop`, `ClearUseAsyncLoopOverride` | [configuration](01_configuration/index.md) |
| Status queries | `IsRunning`, `IsPaused`, `CurrentFPS`, `TargetFPS`, `TotalTime`, `TotalTimeMs`, `TotalFrames`, `ActiveBehaviorCount`, `TimeScale`, `SystemStatus`, `IsUpdateThreadAlive`, `IsFixedUpdateThreadAlive`, `Bus` | [status queries](02_status-queries/index.md) |
| Events | `OnChannelStarted`, `OnChannelPaused`, `OnChannelResumed`, `OnChannelStopped` | [events](03_events/index.md) |

## Defaults and limits

These constants are `private` but they define the public behaviour, so they are recorded here rather than left to be discovered:

| Constant | Value | Effect |
|---|---|---|
| `DEFAULT_CHANNEL` | `"default"` | **public.** The channel used when the argument is omitted |
| `DEFAULT_TARGET_FPS` | `60` | Initial target FPS of a new channel |
| `MIN_FPS` / `MAX_FPS` | `1` / `1000` | Accepted range of `SetTargetFPS`; outside it the call is ignored |
| `DEFAULT_FIXED_UPDATE_INTERVAL_MS` | `16` | Initial `FixedUpdate` step |
| `MIN_UPDATE_INTERVAL_MS` / `MAX_UPDATE_INTERVAL_MS` | `1` / `1000` | Accepted range of `SetFixedUpdateInterval`; outside it the call is ignored |
| `DEFAULT_TIME_SCALE` | `1.0f` | Reported by `TimeScale` for a channel that does not exist |
| `DEFAULT_OBJECT_POOL_SIZE` | `50` | Capacity of each of the channel's three pools |
| `MAX_CONFIG_CACHE_DURATION_MS` | `1000` | How long the sorted behaviour array is cached |
| `THREAD_INACTIVITY_TIMEOUT_MS` | `2000` | The inactivity window used by the two liveness queries |
| `RESTART_SHUTDOWN_TIMEOUT_MS` | `1000` | How long `StopAsync` / `RestartAsync` wait for the pumps |
| `RESTART_QUEUE_CLEAR_TIMEOUT_MS` | `500` | How long `RestartAsync` waits for the queues to drain |
| `MAX_SLEEP_CHUNK_MS` | `50` | Long sleeps are chunked so a stop is noticed within this |
| `MIN_SLEEP_MS` | `1` | Back-off when the clock advanced by zero |

Source: `TickManager.cs` lines 10-33.

## Other types on this page's boundary

- **`TickChannelEventArgs`** — the payload of the four static events; documented separately ([TickChannelEventArgs](../04_TickChannelEventArgs/index.md)).
- **`ITickable`** — what `RegisterBehaviour` accepts; documented separately ([ITickable](../06_ITickable/index.md)).
- **`ITimeSourceControl`** (`VeloxDev.Timing`) — what `Bus` returns. It is shared infrastructure documented with the transition feature; the members this feature's users need are `IsAdvancing`, `IsPaused`, `Rate`, `Position`, `Epoch`, `Pause()`, `Resume()`, `SetRate(double)` and `WaitWhileStalledAsync(CancellationToken)`.
