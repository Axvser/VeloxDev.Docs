# Transition — Core Contracts: `VeloxDev.TransitionSystem`

This section documents the core, UI-agnostic contracts of the animation engine. They are declared in the `VeloxDev.TransitionSystem` namespace of the `VeloxDev.Core` assembly (source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/*.cs` and `Src/Core/VeloxDev.Core/TransitionSystem/**/*.cs`) and never reference any platform type. Platform adapters implement these contracts with concrete types documented in [adapter-provided](../03_adapter-provided/index.md).

## Roles

The engine separates six concerns, each expressed as interfaces:

- **Sampling** — `ISampler` interpolates one property per normalized time; `ISampleable` lets a **value type** declare its own animatable members (struct assembly) without registering a sampler.
- **Property addressing** — `ITransitionProperty` names a (possibly nested) property path; `IFrameState` is the bag of declared values / samplers / options for one transition.
- **Timing descriptor** — `IEaseCalculator`, `ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>` describe how a single animation pass behaves.
- **Execution** — `ITransitionSchedulerCore` serializes animations per target; `ITransitionInterpreter<TPriorityCore>` runs the sampling loop; `FramePacerCore` decides when the loop's next frame happens. Adapters whose host has no dispatcher priority fill `TPriorityCore` with `NonPriority`.
- **Host / UI marshaling** — `ITransitionHost<TPriorityCore>` is everything the engine asks of a host: which thread a target belongs to (`IThreadAffinity`), how to carry work there (`IThreadDispatcher<TPriorityCore>`) and whether the host is still running (`IApplicationState`). It is a *composition*, not a new contract — it adds no member.
- **Clock** — the engine reads time from `VeloxDev.Timing`'s `ITimeSource`, not from a framework clock. That layer has its own section: [timing](../05_timing/index.md).

Besides the event payloads, the remaining members of this namespace — the `RotationDirection` enum and the `Eases` factory / concrete ease classes — are listed with the sampling contracts.

## Sub-pages

- [sampling-capture](00_sampling-capture/index.md) — `ISampler`, `ISampleable`, `ITransitionProperty`, `IFrameState` (sampling + property addressing contracts), the `BoundedProgress` group helper, plus the two path exceptions.
- [effect-engine](01_effect-engine/index.md) — `ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>`, the scheduler and interpreter interfaces, and the `FramePacerCore` pacing base.
- [eases](02_eases/index.md) — `RotationDirection`, `Eases`, and the 31 concrete ease classes.
- [host](03_host/index.md) — the host-thread contracts: `ITransitionHost<TPriorityCore>`, `IThreadAffinity`, `IThreadDispatcher<TPriorityCore>`, `ThreadRef`, `NonPriority`, `IApplicationState`, and the `ThreadDispatcherBase<TPriorityCore>` base.
- [transition-event-args](04_transition-event-args/index.md) — the payloads of the effect callbacks: `TransitionEventArgs` (with `Loop` / `Cycle`), the typed `TransitionEventArgs<TStage, TValue>`, and the `WarnStage` / `ErrorStage` enums.
