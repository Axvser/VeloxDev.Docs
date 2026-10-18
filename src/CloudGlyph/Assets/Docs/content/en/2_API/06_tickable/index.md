# Tickable — API Reference

The tickable feature provides a frame-driven behaviour loop on the .NET side. Mark a `partial` class with `[Tickable]` and the Roslyn source generator (`VeloxDev.Core.Generator`) makes the class implement `VeloxDev.TimeLine.ITickable`; the static `TickManager` then drives per-channel Update / LateUpdate / FixedUpdate loops and forwards each frame to the behaviour's `partial void` hooks.

## Namespaces

Everything ships in the `VeloxDev.Core` package.

| Namespace | Hosted public API |
|---|---|
| `VeloxDev.TimeLine` | `TickableAttribute`, `TickManager`, `TickChannelEventArgs`, `ITickable`, `TimeLineEventArgs`, `FrameEventArgs` |
| `VeloxDev.Timing` | `ITimeSource`, `ITimeSourceControl` — the channel's clock, reached through `TickManager.Bus`. Shared infrastructure, documented with the transition feature |

## Model

```csharp
// User partial class: the source generator emits the ITickable implementation.
[Tickable("demo", 60)]
public partial class Behaviour
{
    public Behaviour() => InitializeTickable();      // generated

    partial void Awake();
    partial void Start();
    partial void Update(FrameEventArgs e);
    partial void LateUpdate(FrameEventArgs e);
    partial void FixedUpdate(FrameEventArgs e);
}
```

- `[Tickable]` selects the loop channel and, optionally, a per-registration target FPS.
- `InitializeTickable()` (generated) registers the instance; `CloseTickable()` (generated) unregisters it.
- `TickManager` owns the per-channel loops. Every mutator is safe from any thread; target-FPS changes are applied at a frame boundary, while rate changes go straight to the bus and step-size changes go to the fixed pump.
- A behaviour sets `FrameEventArgs.Handled = true` to stop the remaining behaviours of that frame phase.
- The `OnChannelStarted` / `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` events report lifecycle transitions for every channel.

Evidence: source (`Src/Core/VeloxDev.Core/TimeLine/`, `Src/Core/VeloxDev.Core/Interfaces/Tickable/`), the generator (`Src/Generators/VeloxDev.Core.Generator/Tickable.cs` + `Writers/TickWriter.cs`), the WPF demo (`Examples/Tickable/WPF/Demo/`), and the MSTest suite (`Src/Core/VeloxDev.Core.Test/TimeLine/`).

## Public surface, by type

| Type | Kind | Public members | Page |
|---|---|---|---|
| `TickableAttribute` | sealed class : `Attribute` | 2 properties, 1 constructor | [TickableAttribute](00_TickableAttribute/index.md) |
| `TickManager` | static class | 4 events, 3 properties/constants (`DEFAULT_CHANNEL`, `UseAsyncLoop`, `ChannelNames`), 27 static methods — 34 public members in all | [TickManager](01_TickManager/index.md) |
| `TimeLineEventArgs` | abstract class | 3 properties | [TimeLineEventArgs](02_TimeLineEventArgs/index.md) |
| `FrameEventArgs` | class : `TimeLineEventArgs` | 2 get-only properties (internal set) + 3 inherited | [FrameEventArgs](03_FrameEventArgs/index.md) |
| `TickChannelEventArgs` | sealed class : `EventArgs` | 1 property | [TickChannelEventArgs](04_TickChannelEventArgs/index.md) |
| `ITickable` | interface | 7 methods | [ITickable](05_ITickable/index.md) |

`TransitionEventArgs` is **not part of this feature**: it lives in `VeloxDev.TransitionSystem` and is documented with the transition feature.

Not part of the public surface, and deliberately so — these are `private` inside `TickManager` and must not appear in user code: the nested `LoopChannel`, `BehaviorWrapper`, `ConfigChangeRequest` and `ObjectPool<T>` types, and the `GetOrCreateChannel`, `LoopChannel`-returning and pump methods. The only public way to reach a channel is the static facade and `TickManager.Bus`.

## Type-level index of `TickManager`

Because `TickManager` is a facade with 34 public members, its reference is split by member group:

| Group | Members |
|---|---|
| Lifecycle & registration | `Start`, `StopAsync`, `Pause`, `Resume`, `TogglePause`, `RestartAsync`, `RegisterBehaviour`, `UnregisterBehaviour` |
| Configuration | `UseAsyncLoop`, `SetTargetFPS`, `SetFixedUpdateInterval`, `SetTimeScale`, `ExecuteOnMainThread`, `SetUseAsyncLoop`, `ClearUseAsyncLoopOverride`, `DEFAULT_CHANNEL`, `ChannelNames` |
| Status queries | `IsRunning`, `IsPaused`, `CurrentFPS`, `TargetFPS`, `TotalTime`, `TotalTimeMs`, `TotalFrames`, `ActiveBehaviorCount`, `TimeScale`, `SystemStatus`, `IsUpdateThreadAlive`, `IsFixedUpdateThreadAlive`, `Bus` |
| Events | `OnChannelStarted`, `OnChannelPaused`, `OnChannelResumed`, `OnChannelStopped` |
