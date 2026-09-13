# Transition — Quick Start

## Overview

**Transition** is VeloxDev's cross-platform, code-driven interpolation engine. Its core idea is **"everything is a state"**: you declare the state an object should reach, path by path (`Transition<T>.Create().Property(x => x.Foo, value)`), and execute it — the engine reads each declared property's current value when the run starts and interpolates it to the declared target over a timed, eased, frame-based timeline. There is no capture step: nothing is discovered or recorded from a live object.

The engine ships in two layers:

- **Engine core** (`VeloxDev.Core`) — framework-agnostic types under `VeloxDev.TransitionSystem` / `VeloxDev.TransitionSystem.Abstractions`: `Eases` and the `Ease*` classes, `TransitionEffectCore` (duration / FPS / easing / loop / events), `InterpolatorCore` (the sampler registry + `NativeInterpolators`), the built-in samplers in `NativeSamplers/*`, the per-target `TransitionSchedulerCore`, the frame-loop `TransitionInterpreterCore`, the abstract `UIThreadInspectorCore`, `NonPriority`, the path exceptions, and the open-generic builder base `TransitionCore<...>` / `StateSnapshotCore<...>`.
- **GUI adapter layer** (the Platform Adapters packages, e.g. `VeloxDev.WPF`) — re-exports the friendly, closed types under the single namespace `VeloxDev.TransitionSystem`: `Transition`, `Transition<T>` (the static entry point *and* the fluent builder: `Create` / `Property` / `Effect`), `State`, `TransitionEffect`, `TransitionEffects` (Empty / Theme / Hover presets), `Interpolator` (per-framework samplers registered in its static ctor), `TransitionInterpreter`, `TransitionScheduler`, `UIThreadInspector`, plus the Core-side `TransitionCoreEx` chaining extensions (`Await` / `Then` / `AwaitThen` / `Interpolator`).

Animating **UI-bound properties** needs the adapter package for your GUI framework: it brings the per-framework value samplers (`Brush`, `Color`, `Transform`, ...) and marshals every frame write to the UI thread. Animating **pure, non-UI values** needs no adapter — the engine core types run headless (see [Install & Add Dependency](01_install/index.md)).

The authoritative examples live under `Examples/Transition/*` (WPF, Avalonia, WinUI, WinForms, MAUI, Blazor/Razor, Jalium) and the engine contract is pinned by `Src/Core/VeloxDev.Core.Test/TransitionSystem/*`.

## Quick Start — Sub-pages

- [00 Prerequisites](00_prerequisites/index.md) — supported target frameworks, SDK/workloads, demos
- [01 Install & Add Dependency](01_install/index.md) — `VeloxDev.Core` + the platform adapter package for UI-bound props
- [02 Easing & Interpolators](02_easing-and-interpolators/index.md) — the built-in easing catalog, custom `IEaseCalculator`, custom `ISampler` registration
- [03 Declare State Explicitly](03_declare-state/index.md) — declare target values path by path with `Transition<T>.Create().Property(...)`, and express a reset as a zero-duration write-back
- [04 Sequence & Repeat](04_sequence-and-repeat/index.md) — multi-segment timelines, auto-reverse/loops, FPS cap, effect events, presets
- [05 Execute & Control](05_execute-and-control/index.md) — one-shot execution, mutual vs. parallel, exit, per-target scheduler
- [06 UI Thread & Marshaling](06_ui-thread-marshaling/index.md) — per-platform UI-thread wiring and `CaptureUIThread`
- [07 Verify & Complete Code](07_verify-and-complete-code/index.md) — demos & tests, the single runnable program, and the run declaration
