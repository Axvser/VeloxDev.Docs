# Transition — Core Contracts: `VeloxDev.TransitionSystem`

This section documents the core, UI-agnostic contracts of the animation engine. They are declared in the `VeloxDev.TransitionSystem` namespace of the `VeloxDev.Core` assembly (source: `Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/*.cs` and `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`) and never reference any platform type. Platform adapters implement these contracts with concrete types documented in [adapter-provided](../03_adapter-provided/index.md).

## Roles

The engine separates five concerns, each expressed as interfaces:

- **Sampling** — `ISampler` interpolates one property per normalized time; `ISampleable` lets a **value type** declare its own animatable members (struct assembly) without registering a sampler.
- **Property addressing** — `ITransitionProperty` names a (possibly nested) property path; `IFrameState` is the bag of declared values / samplers / options for one transition.
- **Timing** — `IEaseCalculator`, `ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>` describe how a single animation pass behaves.
- **Execution** — `ITransitionSchedulerCore` serializes animations per target; `ITransitionInterpreter<TPriorityCore>` runs the sampling loop. Adapters whose host has no dispatcher priority fill `TPriorityCore` with `NonPriority`.
- **UI marshaling** — `IUIThreadInspectorCore` answers thread questions and marshals reads/writes to the UI thread; `IUIThreadInspector<TPriorityCore>` adds the priority-taking dispatch.

The remaining members of this namespace — the `RotationDirection` enum and the `Eases` factory / concrete ease classes — are listed with the sampling contracts.

## Sub-pages

- [sampling-capture](00_sampling-capture/index.md) — `ISampler`, `ISampleable`, `ITransitionProperty`, `IFrameState` (sampling + property addressing contracts), plus the two path exceptions.
- [effect-engine](01_effect-engine/index.md) — `ITransitionEffectCore` / `ITransitionEffect<TPriorityCore>`, the scheduler and interpreter interfaces, and the UI-thread inspector interfaces.
- [eases](02_eases/index.md) — `RotationDirection`, `Eases`, and the 31 concrete ease classes.
