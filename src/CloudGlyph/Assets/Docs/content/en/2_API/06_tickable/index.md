# Tickable — API Reference

The tickable feature provides a Unity-style, frame-driven behaviour loop on the .NET side. Mark a `partial` class with `[Tickable]` and the Roslyn source generator (`VeloxDev.Core.Generator`) makes the class implement `VeloxDev.TimeLine.ITickable`; the static `TickManager` then drives per-channel Update / LateUpdate / FixedUpdate loops and forwards each frame to the behaviour's `partial void` hooks.

## Name map — everything that was renamed on 2026-10-01

The feature was formerly called *monobehaviour*. The namespace `VeloxDev.TimeLine` never changed; these names did. Only the API reference uses the new names — there is no compatibility alias, and the old names no longer exist in the assembly.

| Old (before 2026-10-01) | Current |
|---|---|
| `MonoBehaviourAttribute` | `TickableAttribute` |
| `MonoBehaviourManager` | `TickManager` |
| `IMonoBehaviour` | `ITickable` |
| `MonoBehaviourChannelEventArgs` | `TickChannelEventArgs` |
| `InitializeMonoBehaviour` | `InitializeTickable` |
| `CloseMonoBehaviour` | `CloseTickable` |
| `TickManager.SetUseAsyncLoop` (unchanged) | `TickManager.SetUseAsyncLoop` |
| namespace `VeloxDev.MonoBehaviour` | namespace `VeloxDev.TimeLine` |
| `Interfaces/MonoBehaviour/` | `Interfaces/Tickable/` |
| `MonoWriter.cs` (generator) | `TickWriter.cs` |
| `Examples/MonoBehaviour/WPF/Demo/` | `Examples/Tickable/WPF/Demo/` |
| `MonoBehaviourManagerTests.cs` (tests) | `TickManagerTests.cs` |

**Unchanged:** the five lifecycle hook names — `Awake`, `Start`, `Update`, `LateUpdate`, `FixedUpdate` — and the namespace `VeloxDev.TimeLine`.

## Namespaces

Everything ships in the `VeloxDev.Core` package, and since the rename everything lives in **one** namespace.

| Namespace | Hosted public API |
|---|---|
| `VeloxDev.TimeLine` | `TickableAttribute`, `TickManager`, `TickChannelEventArgs`, `ITickable`, `TimeLineEventArgs`, `FrameEventArgs` |
| `VeloxDev.Timing` | `ITimeSourceControl`, `ITimeSource` — the channel's clock, reached through `TickManager.Bus`. Shared infrastructure, documented with the transition feature |

## Model

```csharp
// User partial class: source generator emits the ITickable implementation.
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
- `TickManager` owns the per-channel loops; lifecycle and configuration are thread-safe and applied on frame boundaries.
- A behaviour sets `FrameEventArgs.Handled = true` to stop the remaining behaviours of that frame phase.
- Per-channel `OnChannelStarted` / `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` events report lifecycle transitions.

Evidence: source (`Src/Core/VeloxDev.Core/TimeLine/`, `Src/Core/VeloxDev.Core/Interfaces/Tickable/`), the generator (`Src/Generators/VeloxDev.Core.Generator/Tickable.cs` + `Writers/TickWriter.cs`), the WPF demo (`Examples/Tickable/WPF/Demo/`), and the MSTest suite (`Src/Core/VeloxDev.Core.Test/TimeLine/`).

## Public surface, by type

| Type | Kind | Public members | Page |
|---|---|---|---|
| `TickableAttribute` | sealed class : `Attribute` | 2 properties, 1 constructor | [TickableAttribute](00_TickableAttribute/index.md) |
| `TickManager` | static class | 4 events, 2 public properties (`UseAsyncLoop`, `ChannelNames`), 1 public constant (`DEFAULT_CHANNEL`), 27 public static methods — 34 public members in all | [TickManager](01_TickManager/index.md) |
| `TimeLineEventArgs` | abstract class | 3 properties | [TimeLineEventArgs](02_TimeLineEventArgs/index.md) |
| `FrameEventArgs` | class : `TimeLineEventArgs` | 2 read-only properties + 3 inherited | [FrameEventArgs](03_FrameEventArgs/index.md) |
| `TickChannelEventArgs` | sealed class : `EventArgs` | 1 property | [TickChannelEventArgs](04_TickChannelEventArgs/index.md) |
| `ITickable` | interface | 7 methods | [ITickable](05_ITickable/index.md) |

`TransitionEventArgs` is **no longer part of this feature**: it moved out of `VeloxDev.TimeLine` into `VeloxDev.TransitionSystem`, is no longer `sealed`, and now carries `Loop` / `Cycle` (plus the typed `TransitionEventArgs<TStage, TValue>` and the `WarnStage` / `ErrorStage` enums). It is documented with the transition feature — see [transition event arguments](../03_transition/00_transitionsystem/04_transition-event-args/index.md).

Not part of the public surface, and deliberately so — these are `private` inside `TickManager` and must not appear in user code: the nested `LoopChannel`, `BehaviorWrapper`, `ConfigChangeRequest` and `ObjectPool<T>` types, and the `GetOrCreateChannel`, `LoopChannel`-returning and pump methods. The only public way to reach a channel is the static facade and `TickManager.Bus`.

## Type-level index of `TickManager`

Because `TickManager` is a facade with 34 public members, its reference is split by member group:

| Group | Members |
|---|---|
| Lifecycle & registration | `Start`, `StopAsync`, `Pause`, `Resume`, `TogglePause`, `RestartAsync`, `RegisterBehaviour`, `UnregisterBehaviour` |
| Configuration | `UseAsyncLoop`, `SetTargetFPS`, `SetFixedUpdateInterval`, `SetTimeScale`, `ExecuteOnMainThread`, `SetUseAsyncLoop`, `ClearUseAsyncLoopOverride`, `DEFAULT_CHANNEL`, `ChannelNames` |
| Status queries | `IsRunning`, `IsPaused`, `CurrentFPS`, `TargetFPS`, `TotalTime`, `TotalTimeMs`, `TotalFrames`, `ActiveBehaviorCount`, `TimeScale`, `SystemStatus`, `IsUpdateThreadAlive`, `IsFixedUpdateThreadAlive`, `Bus` |
| Events | `OnChannelStarted`, `OnChannelPaused`, `OnChannelResumed`, `OnChannelStopped` |
