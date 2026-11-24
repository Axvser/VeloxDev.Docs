# Tick Loop

`VeloxDev.TimeLine` drives an object's five lifecycle hooks from a named clock channel. `[Tickable]` generates the `ITickable` plumbing; `TickManager` owns the threads, frame rate, fixed step and time scale. Namespace `VeloxDev.TimeLine`.

## Type groups

| Group | Types | Page |
|---|---|---|
| Contract and generated members | `TickableAttribute`, `ITickable`, `TimeLineEventArgs`, `FrameEventArgs`, generated `InitializeTickable` / `CloseTickable` / `Invoke*` / partial hooks | [Tickable contract](00_tickable-contract/index.md) |
| Manager | `TickManager`, `TickChannelEventArgs`, `TickBehaviorErrorEventArgs` | [Tick manager](01_tick-manager/index.md) |

## Hook order

| Hook | Clock | Runs |
|---|---|---|
| `Awake` | — | Once per registration, before the first frame |
| `Start` | — | Once per registration, after `Awake` |
| `Update` | update thread, variable delta | Once per frame |
| `LateUpdate` | update thread, variable delta | After `Update` in the same frame, unless `Update` set `Handled` |
| `FixedUpdate` | fixed thread, fixed delta | Once per owed fixed step; a stall is repaid as several calls |

The same `FrameEventArgs` instance is reused for every hook of one frame; a hook must not retain it. `Handled` suppresses the remaining behaviours and `LateUpdate` in that frame, but does not affect `FixedUpdate`.

See [Tick Loop quick start](../../1_QuickStart/15_tick-loop/index.md) for a complete program.

## Targets

`VeloxDev.Core` targets `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0` and `net8.0`. On platforms without threads (browser, iOS) `TickManager.UseAsyncLoop` defaults to `true`, so the loops use `async` / `Task.Delay` instead of dedicated threads. On older targets without the platform checks it defaults to `true` as well.
