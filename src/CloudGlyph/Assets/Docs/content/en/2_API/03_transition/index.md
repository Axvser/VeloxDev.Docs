# Transition — API Reference

The transition system is the animation engine shared by every VeloxDev UI adapter. The engine itself lives in the `VeloxDev.Core` assembly — implementations under `Src/Core/VeloxDev.Core/TransitionSystem/**`, contracts under `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/**` — and its public API spans four core namespaces:

| Namespace | Contents |
|---|---|
| `VeloxDev.TransitionSystem` | Core contracts (`IEaseCalculator`, `ISampler`, `ISampleable`, `ITransitionProperty`, `IFrameState`, `ITransitionEffect*`, `ITransitionScheduler*`, `ITransitionInterpreter*`, `IUIThreadInspector*`), the `RotationDirection` enum, `NonPriority`, the path exceptions (`TransitionPathConflictException`, `TransitionPathUnsampleableException`), the `Eases` factory with the concrete ease classes, and the `TransitionCoreEx` chaining extensions |
| `VeloxDev.TransitionSystem.Abstractions` | Engine base types: `TransitionCore`, the `StateSnapshotCore` family, `StateCore`, `InterpolatorCore`, `SamplerSet<TPriorityCore>`, `TransitionEffectCore`, `TransitionSchedulerCore`, `TransitionInterpreterCore`, `UIThreadInspectorCore`, `TransitionProperty` |
| `VeloxDev.TransitionSystem.NativeSamplers` | Built-in stateless samplers (`DoubleSampler`, `QuaternionSampler`, ...) |
| `VeloxDev.TimeLine` | `TransitionEventArgs` (and its base `TimeLineEventArgs`) |

Each platform adapter — WPF, Avalonia, WinUI, MAUI, WinForms, Razor, Jalium (`Src/Adapters/VeloxDev.*`) — re-exposes the same public shapes in the `VeloxDev.TransitionSystem` namespace: its own `Transition`, `Transition<T>` (the static entry point, the fluent builder and the executor in one type), `Interpolator`, `TransitionEffect`, `TransitionEffects`, `State`, `UIThreadInspector`, `TransitionScheduler`, and `TransitionInterpreter`, plus the platform samplers it registers.

Members below are verified against the source files above. Behavioral claims cite `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` and the demos under `Examples/Transition/*`; signatures not confirmed by a demo or a test are marked *inferred*.

## Sections

This feature's API reference is split into five sections:

- [00_transitionsystem](00_transitionsystem/index.md) — the `VeloxDev.TransitionSystem` core contracts: sampling / property contracts, effect-scheduler-interpreter contracts, `RotationDirection`, `Eases`, and the concrete ease classes.
- [01_abstractions](01_abstractions/index.md) — the engine implementation base types in `VeloxDev.TransitionSystem.Abstractions`.
- [02_nativesamplers](02_nativesamplers/index.md) — the built-in samplers in `VeloxDev.TransitionSystem.NativeSamplers`.
- [03_adapter-provided](03_adapter-provided/index.md) — the per-platform surface each adapter ships in `VeloxDev.TransitionSystem`.
- [04_timeline](04_timeline/index.md) — `VeloxDev.TimeLine.TransitionEventArgs` and `Handled` cancellation.
