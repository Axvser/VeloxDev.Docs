# Transition Animation

The animation engine is split between Core (the control plane, sampling contract, easing and state model) and each GUI adapter (the frame scheduler, interpreter, host and platform samplers). A transition is a chain of snapshots; `Transition<T>` in an adapter is the fluent front end over `TransitionCore<T, …>`.

The Core assembly targets `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0` and `net8.0`. Adapter transition types live in `VeloxDev.TransitionSystem` too, but are supplied by the package that references the adapter.

## Type groups

| Group | Types | Page |
|---|---|---|
| Control plane and chain | `TransitionCore`, `TransitionCore<T, …>`, `StateSnapshotCore<T>`, `StateSnapshotCore`, `StateCore`, `TransitionCoreEx`, `TransitionProperty`, `PathIndex`, path exceptions | [Transition core](00_transition-core/index.md) |
| Effects and easing | `ITransitionEffectCore`, `ITransitionEffect<TPriorityCore>`, `TransitionEffectCore`, `TransitionEffectCore<TPriorityCore>`, `IEaseCalculator`, `Eases` and its curve classes | [Effects and easing](01_effects-and-easing/index.md) |
| Sampling | `ISampler`, `ISampleable`, `InterpolatorCore`, `ITransitionProperty`, `IFrameState`, `SamplerSet<TPriorityCore>`, `BoundedProgress`, `RotationDirection`, native samplers | [Sampling](02_sampling/index.md) |
| Scheduling and events | `ITransitionSchedulerCore`, `ITransitionScheduler`, `ITransitionScheduler<TPriorityCore>`, `FramePacerCore`, `TransitionSchedulerCore`, `TransitionInterpreterCore`, `ITransitionHost<TPriorityCore>`, `TransitionHostBase<TPriorityCore>` | [Scheduling and events](03_scheduling-and-events/index.md) |
| Platform adapter types | `Transition`, `Transition<T>`, `State`, `Interpolator`, `TransitionEffect`, `TransitionEffects`, `TransitionInterpreter`, `TransitionScheduler`, `UIThreadInspector` | [Platform adapter types](04_platform-adapter-types/index.md) |

## Typical flow

1. Build a chain: `Transition<T>.Create()`, then `Property(lambda, endValue, options?)` for each animated value and `Effect(...)` for timing.
2. Optionally extend the chain with `Then()`, `Await(TimeSpan)`, `AwaitThen(TimeSpan)` and `Repeat(int)`.
3. Run it with `Execute(target, CanMutualTask)` or against a shared timeline.
4. Control the run by target with `Transition.Pause`, `Resume`, `SetRate`, `Seek`, `Exit`, `Position`, `Cycle` and `IsPaused`.

See [Transition Animation quick start](../../1_QuickStart/12_transition-animation/index.md) for a runnable WPF window.

## Exceptions

| Exception | Thrown by |
|---|---|
| `TransitionPathUnsampleableException` | Chain validation, when a declared path ends in a reference type with no sampler. |
| `TransitionPathConflictException` | `StateCore.SetValue`, when a path sits above or below one already declared. |
| `InvalidOperationException` | A chain builder receives a segment of the wrong type. |
| `ArgumentOutOfRangeException` | `SetRate` receives a negative rate. |
