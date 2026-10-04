# Transition — API Reference

The transition system is the animation engine shared by every VeloxDev UI adapter. The engine itself lives in the `VeloxDev.Core` assembly — implementations under `Src/Core/VeloxDev.Core/TransitionSystem/**`, contracts under `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/**` — and it stands on two more Core subsystems added 2026-09-14: the time layer (`VeloxDev.Timing`, `Src/Core/VeloxDev.Core/Timing/**` + `Interfaces/Timing/**`) and the thread/host layer (`VeloxDev.Threading`, `VeloxDev.Lifetime`). Its public API spans these namespaces:

| Namespace | Contents |
|---|---|
| `VeloxDev.TransitionSystem` | Core contracts (`IEaseCalculator`, `ISampler`, `ISampleable`, `ITransitionProperty`, `IFrameState`, `ITransitionEffect*`, `ITransitionScheduler*`, `ITransitionInterpreter*`, `ITransitionHost<TPriorityCore>`), the `RotationDirection` enum, the `BoundedProgress` struct, the abstract `FramePacerCore`, the path exceptions (`TransitionPathConflictException`, `TransitionPathUnsampleableException`), `PathIndex`, the `Eases` factory with the 31 concrete ease classes, and the `TransitionCoreEx` chaining extensions |
| `VeloxDev.TransitionSystem.Abstractions` | Engine base types: `TransitionCore`, the `StateSnapshotCore` family, `StateCore`, `InterpolatorCore`, `SamplerSet<TPriorityCore>`, `TransitionEffectCore[<TPriorityCore>]`, `TransitionSchedulerCore`, `TransitionInterpreterCore`, `TransitionHostBase<TPriorityCore>`, `TransitionProperty` |
| `VeloxDev.TransitionSystem.NativeSamplers` | Built-in stateless samplers (`DoubleSampler`, `QuaternionSampler`, ...) |
| `VeloxDev.Timing` | The shared clock: `ITimeSource` / `ITimeSourceControl`, the two sampler contracts (`IUncompensatedTimeSampler`, `ICompensatingTimeSampler`) and their `TimeSample`, the default implementations (`TimeSourceCore`, `UncompensatedTimeSampler`, `CompensatingTimeSampler`), the `TimeConversion` arithmetic, and the `TimerCore` registry |
| `VeloxDev.Threading` | The host's thread surface: `IThreadAffinity`, `IThreadDispatcher<TPriorityCore>`, `ThreadDispatcherBase<TPriorityCore>`, `ThreadRef`, `NonPriority` |
| `VeloxDev.Lifetime` | `IApplicationState` and the `ApplicationState` liveness flag |
| `VeloxDev.TimeLine` | `TransitionEventArgs` (carrying `Stage` / `Message` / `Exception`) and its base `TimeLineEventArgs` |

Each platform adapter — WPF, Avalonia, WinUI, MAUI, WinForms, Razor, Jalium (`Src/Adapters/VeloxDev.*`) — re-exposes the same public shapes in the `VeloxDev.TransitionSystem` namespace: its own `Transition`, `Transition<T>` (the static entry point, the fluent builder and the executor in one type), `Interpolator`, `TransitionEffect`, `TransitionEffects`, `State`, `UIThreadInspector` (the adapter's `TransitionHostBase<TPriorityCore>` subclass), `TransitionScheduler`, and `TransitionInterpreter`, plus the platform samplers it registers. The per-adapter derivations themselves — the adapter packages, their templates and their attached behaviours — are **feature 08**: see [platform-adapters](../08_platform-adapters/index.md).

Members below are verified against the source files above. Behavioral claims cite `Src/Core/VeloxDev.Core.Test/TransitionSystem/*`, `Src/Core/VeloxDev.Core.Test/Timing/*`, the `Examples/Transition/AUTO TEST` conformance harness and the demos under `Examples/Transition/*`; signatures not confirmed by a demo, a test or the harness are marked *inferred*.

## Sections

This feature's API reference is split into six sections:

- [transitionsystem](00_transitionsystem/index.md) — the `VeloxDev.TransitionSystem` core contracts: sampling / property contracts, effect-scheduler-interpreter contracts, the host-thread contracts, `RotationDirection`, `BoundedProgress`, `FramePacerCore`, `Eases`, and the concrete ease classes.
- [abstractions](01_abstractions/index.md) — the engine implementation base types in `VeloxDev.TransitionSystem.Abstractions`.
- [nativesamplers](02_nativesamplers/index.md) — the built-in samplers in `VeloxDev.TransitionSystem.NativeSamplers`.
- [adapter-provided](03_adapter-provided/index.md) — the per-platform surface each adapter ships in `VeloxDev.TransitionSystem`.
- [timeline](04_timeline/index.md) — `VeloxDev.TimeLine.TransitionEventArgs` and `Handled` cancellation.
- [timing](05_timing/index.md) — the `VeloxDev.Timing` clock the frame loop and the transition engine share.
