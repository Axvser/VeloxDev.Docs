# Transition — Quick Start

## Overview

**Transition** is VeloxDev's cross-platform, code-driven interpolation engine. Its core idea is **"everything is a state"**: you declare the state an object should reach, path by path (`Transition<T>.Create().Property(x => x.Foo, value)`), and execute it — the engine reads each declared property's current value when the run starts and interpolates it to the declared target over a timed, eased, frame-based timeline. There is no capture step: nothing is discovered or recorded from a live object.

The engine ships in three layers:

- **Engine core** (`VeloxDev.Core`) — framework-agnostic types under `VeloxDev.TransitionSystem` / `VeloxDev.TransitionSystem.Abstractions`: `Eases` and the `Ease*` classes, `TransitionEffectCore` (duration / FPS / easing / loop / events), `InterpolatorCore` (the sampler registry + `NativeSamplers/*`), the per-target `TransitionSchedulerCore`, the frame-loop `TransitionInterpreterCore` with its `FramePacerCore` pacing seam, the abstract `TransitionHostBase<TPriorityCore>`, `BoundedProgress`, the path exceptions, and the open-generic builder base `TransitionCore<...>` / `StateSnapshotCore<...>`.
- **Time layer** (`VeloxDev.Timing` + `VeloxDev.Threading` / `VeloxDev.Lifetime`, all in `VeloxDev.Core`) — the clock every run is anchored to (`ITimeSource` / `ITimeSourceControl`) and the host seam (`ITransitionHost<TPriorityCore>`) that answers "which thread" and "is the app alive". See [Timing Layer](07_timing-layer/index.md).
- **GUI adapter layer** (the Platform Adapters packages, e.g. `VeloxDev.WPF`) — re-exports the friendly, closed types under the single namespace `VeloxDev.TransitionSystem`: `Transition`, `Transition<T>` (the static entry point *and* the fluent builder and executor), `State`, `TransitionEffect`, `TransitionEffects` (Empty / Theme / Hover presets), `Interpolator` (per-framework samplers registered in its static ctor), `TransitionInterpreter`, `TransitionScheduler`, `UIThreadInspector` (the adapter's host), plus the Core-side `TransitionCoreEx` chaining extensions (`Await` / `Then` / `AwaitThen` / `Repeat` / `Interpolator`).

Animating **UI-bound properties** needs the adapter package for your GUI framework: it brings the per-framework value samplers (`Brush`, `Color`, `Transform`, ...) and marshals every frame write to the UI thread. Animating **pure, non-UI values** needs no adapter — the engine core types run headless (see [Install & Add Dependency](01_install/index.md)), and the Timing layer runs headless on its own ([Timing Layer](07_timing-layer/index.md)).

The authoritative examples live under `Examples/Transition/*` (WPF, Avalonia, WinUI, WinForms, MAUI, Blazor/Razor, Jalium). The engine's contracts are pinned twice over: by the unit tests in `Src/Core/VeloxDev.Core.Test/TransitionSystem/*` and `Src/Core/VeloxDev.Core.Test/Timing/*` (285 tests), and by the **`Examples/Transition/AUTO TEST`** conformance harness, which drives all seven real demos over UI Automation and a browser and checks sampler arithmetic against an independently written closed form.

## Quick Start — Sub-pages

- [00 Prerequisites](00_prerequisites/index.md) — supported target frameworks, SDK/workloads, the demos and the `AUTO TEST` harness
- [01 Install & Add Dependency](01_install/index.md) — `VeloxDev.Core` + the platform adapter package for UI-bound props
- [02 Easing & Interpolators](02_easing-and-interpolators/index.md) — the built-in easing catalog, custom `IEaseCalculator`, custom `ISampler` registration
- [03 Declare State Explicitly](03_declare-state/index.md) — declare target values path by path with `Transition<T>.Create().Property(...)`, and express a reset as a zero-duration write-back
- [04 Sequence & Repeat](04_sequence-and-repeat/index.md) — multi-segment timelines, auto-reverse/loops, the chain-level `Repeat(n)`, FPS cap, effect events and diagnostics, presets
- [05 Execute & Control](05_execute-and-control/index.md) — one-shot execution, mutual vs. parallel, a shared timeline, exit, pause / rate / seek, per-target scheduler
- [06 UI Thread & Marshaling](06_ui-thread-marshaling/index.md) — per-platform host wiring and the thread-marshaling contract
- [07 Timing Layer](07_timing-layer/index.md) — drive `VeloxDev.Timing` headlessly: a time source, both sampler modes, and the park signal
- [08 Verify & Complete Code](08_verify-and-complete-code/index.md) — demos, the `AUTO TEST` harness, the single runnable program, and the run declaration
