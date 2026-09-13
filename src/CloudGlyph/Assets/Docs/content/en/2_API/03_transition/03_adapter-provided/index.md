# Transition — Adapter-Provided Surface

Each platform adapter (`Src/Adapters/VeloxDev.WPF|Avalonia|WinUI|MAUI|WinForms|Razor|Jalium`) provides, in its own assembly and in the **same** `VeloxDev.TransitionSystem` namespace, a full set of concrete types that subclass the engine base types from [abstractions](../01_abstractions/index.md). Programs `using VeloxDev.TransitionSystem;` therefore see one uniform API on every platform; only the platform value types differ.

## What each adapter ships

| Type | Role | Derives from |
|---|---|---|
| `Transition` | Non-generic static entry (cancel / exit helpers) | `TransitionCore` |
| `Transition<T>` | Generic entry point, fluent builder and executor in one type (`Create` / `Property` / `Effect`, plus the inherited `Execute` / `Exit` / `GetState`) | `TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>` |
| `Interpolator` | Platform sampler registry (subclasses `InterpolatorCore` and registers platform types in its static ctor) | `InterpolatorCore` |
| `State` | Declared-state bag | `StateCore` |
| `TransitionEffect` | Timing descriptor with a default priority where applicable | `TransitionEffectCore` or `TransitionEffectCore<TPriorityCore>` |
| `TransitionEffects` | `Empty` / `Theme` / `Hover` presets | static class (instance class on WinUI) |
| `UIThreadInspector` | Platform UI-thread marshaling | `UIThreadInspectorCore` or `UIThreadInspectorCore<TPriorityCore>` |
| `TransitionScheduler` | Per-target scheduler | `TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter[, TPriorityCore]>` |
| `TransitionInterpreter` | Sampling-loop interpreter | `TransitionInterpreterCore<TransitionEffect[, TPriorityCore]>` |
| platform samplers | Registered value-type interpolators | `ISampler` (namespace `VeloxDev.Adapters.NativeSamplers` per adapter) |

Priority-typed adapters (WPF, Avalonia, Jalium, WinUI) marshal writes at a dispatcher priority; MAUI, WinForms and Razor are non-priority.

| Adapter | Framework | Priority type | Priority default |
|---|---|---|---|
| WPF | `System.Windows.Threading` | `DispatcherPriority` | `DispatcherPriority.Render` |
| Avalonia | Avalonia | `DispatcherPriority` | `DispatcherPriority.Render` |
| Jalium | Jalium | `DispatcherPriority` | `DispatcherPriority.Render` |
| WinUI | Microsoft.UI | `DispatcherQueuePriority` | `DispatcherQueuePriority.High` |
| MAUI | .NET MAUI | — (no priority) | — |
| WinForms | System.Windows.Forms | — | — |
| Razor | Blazor / Razor | — | — |

## Sub-pages

- [transition](00_transition/index.md) — `Transition`, `Transition<T>` (the `Property` / `Effect` overload sets, and the inherited `Execute` / `Exit` / `GetState`).
- [effect-interpolator](01_effect-interpolator/index.md) — `Interpolator` and its per-adapter sampler registrations, `TransitionEffect`, `TransitionEffects`, and `State`.
- [ui-inspector](02_ui-inspector/index.md) — `UIThreadInspector` per adapter, plus the `TransitionScheduler` / `TransitionInterpreter` adapter subclasses.
