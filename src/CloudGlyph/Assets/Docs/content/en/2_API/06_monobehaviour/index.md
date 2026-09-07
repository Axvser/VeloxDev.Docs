# MonoBehaviour — API Reference

The MonoBehaviour feature provides a Unity-style, frame-driven behaviour loop on the .NET side. Mark a `partial` class with `[MonoBehaviour]` and the Roslyn source generator (`VeloxDev.Core.Generator`) makes the class implement `IMonoBehaviour`; the static `MonoBehaviourManager` then drives per-channel Update / LateUpdate / FixedUpdate loops and forwards each frame to the behaviour's `partial void` hooks.

## Namespaces

Two namespaces are involved; everything ships in the `VeloxDev.Core` package.

| Namespace | Hosted public API |
|---|---|
| `VeloxDev.TimeLine` | `MonoBehaviourAttribute`, `MonoBehaviourManager`, `MonoBehaviourChannelEventArgs`, `TimeLineEventArgs`, `FrameEventArgs`, `ThreadSafeFrameEventArgs`, `TransitionEventArgs` |
| `VeloxDev.MonoBehaviour` | `IMonoBehaviour` |

## Model

```csharp
// User partial class: source generator emits the IMonoBehaviour implementation.
[MonoBehaviour]
public partial class Behaviour
{
    public Behaviour() => InitializeMonoBehaviour();

    partial void Awake();
    partial void Start();
    partial void Update(FrameEventArgs e);
    partial void LateUpdate(FrameEventArgs e);
    partial void FixedUpdate(FrameEventArgs e);
}
```

- `[MonoBehaviour]` selects the loop channel and, optionally, a per-registration target FPS.
- `InitializeMonoBehaviour()` (generated) registers the instance; `CloseMonoBehaviour()` (generated) unregisters it.
- `MonoBehaviourManager` owns the per-channel loops; lifecycle and configuration are thread-safe and applied on frame boundaries.
- A behaviour sets `FrameEventArgs.Handled = true` to stop the remaining behaviours of that frame phase.
- Per-channel `OnChannelStarted` / `OnChannelPaused` / `OnChannelResumed` / `OnChannelStopped` events report lifecycle transitions.

Evidence: source (`Src/Core/VeloxDev.Core/TimeLine/`, `Src/Core/VeloxDev.Core/Interfaces/MonoBehaviour/`), the generator (`Src/Generators/VeloxDev.Core.Generator/`), the WPF demo (`Examples/MonoBehaviour/WPF/Demo/`), and the MSTest suite (`Src/Core/VeloxDev.Core.Test/TimeLine/`).

## API by type

This feature's API reference is split by type. Each page documents the full public surface of one type.

| Type | Namespace | Kind | Page |
|---|---|---|---|
| `MonoBehaviourAttribute` | `VeloxDev.TimeLine` | Class attribute | [MonoBehaviourAttribute](00_MonoBehaviourAttribute/index.md) |
| `MonoBehaviourManager` | `VeloxDev.TimeLine` | Static manager | [MonoBehaviourManager](01_MonoBehaviourManager/index.md) |
| `TimeLineEventArgs` | `VeloxDev.TimeLine` | Abstract base | [TimeLineEventArgs](02_TimeLineEventArgs/index.md) |
| `FrameEventArgs` | `VeloxDev.TimeLine` | Class | [FrameEventArgs](03_FrameEventArgs/index.md) |
| `ThreadSafeFrameEventArgs` | `VeloxDev.TimeLine` | Class | [ThreadSafeFrameEventArgs](04_ThreadSafeFrameEventArgs/index.md) |
| `MonoBehaviourChannelEventArgs` | `VeloxDev.TimeLine` | Class | [MonoBehaviourChannelEventArgs](05_MonoBehaviourChannelEventArgs/index.md) |
| `TransitionEventArgs` | `VeloxDev.TimeLine` | Class | [TransitionEventArgs](06_TransitionEventArgs/index.md) |
| `IMonoBehaviour` | `VeloxDev.MonoBehaviour` | Interface | [IMonoBehaviour](07_IMonoBehaviour/index.md) |
