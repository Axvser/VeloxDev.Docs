# Transition — Engine Implementation: `VeloxDev.TransitionSystem.Abstractions`

Namespace `VeloxDev.TransitionSystem.Abstractions` in the `VeloxDev.Core` assembly (source: `Src/Core/VeloxDev.Core/TransitionSystem/**/*.cs`). These concrete / abstract base types implement the contracts documented in [transitionsystem](../00_transitionsystem/index.md). Each platform adapter subclasses them to produce the `VeloxDev.TransitionSystem` types you actually construct (see [adapter-provided](../03_adapter-provided/index.md)).

## Map of the namespace

| Type family | Role |
|---|---|
| `TransitionCore` (static entry points) and `TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore>` (builder + executor) | Describe a target state and a segment chain, then run it |
| `StateSnapshotCore` / `StateSnapshotCore<T>` | The abstract builder root; the `Execute` overloads and the per-instance control methods |
| `StateCore : IFrameState` | The declared-state bag (values / samplers / options) |
| `InterpolatorCore` | The sampler registry, the `CreateScheduler` platform seam, and `Prepare` |
| `SamplerSet<TPriorityCore>` | One prepared, per-property sampling container the interpreter drives |
| `TransitionEffectCore[<TPriorityCore>]` | The timing descriptor with lifecycle + diagnostic events |
| `TransitionSchedulerCore[<THost, TTransitionInterpreterCore, TPriorityCore>]` | The per-target execution coordinator and its registry tables |
| `TransitionInterpreterCore[<…>]` | The timeline-driven sampling loop and its pacing seams |
| `TransitionHostBase<TPriorityCore>` | The base an adapter's host derives from (see [host](../00_transitionsystem/03_host/index.md)) |
| `TransitionProperty` | The compiled property path (the identity a state is keyed by) |

The types marked *internal* below (`TransitionRun`, `TransitionDiagnostics`, `StructAssembler`, `ReusableTimerWait`, `PathSegment` and its subclasses, the index-argument family) are not public API but their behavior is observable, and each is documented next to the type that uses it.

## Sub-pages

- [builder](00_builder/index.md) — `TransitionCore`, `TransitionCore<…>`, `StateSnapshotCore` / `StateSnapshotCore<T>` (including the shared-timeline `Execute` overload and the `Repeat` loop semantics), `TransitionCoreEx`, `StateCore`.
- [engine](01_engine/index.md) — `InterpolatorCore`, `SamplerSet<TPriorityCore>`, `TransitionEffectCore[<…>]`, `TransitionSchedulerCore[<…>]` (and `ExecuteCapturing` / `Replay`), `TransitionInterpreterCore[<…>]`, plus `TransitionRun`, `TransitionDiagnostics` and `ReusableTimerWait`.
- [paths](02_paths/index.md) — `TransitionProperty`, `PathIndex` and `PathIndex.Frozen`, and the two path guards.
