# Transition — Install & Add Dependency

## 1. Add the engine core

Every Transition app references `VeloxDev.Core`. Add it to any .NET project:

```bash
dotnet add package VeloxDev.Core
```

`VeloxDev.Core` contains the framework-agnostic engine: `Eases` and the `Ease*` classes, the sampler registry (`InterpolatorCore` + `NativeSamplers/*`), `TransitionEffectCore`, the scheduler/interpreter and the snapshot machinery. Nothing here depends on a GUI framework.

**Expected result:** the package appears in the `.csproj`; after restore, `using VeloxDev.TransitionSystem;` resolves and `Eases.Cubic.InOut.Ease(0.5)` runs in a plain console.

## 2. Add the platform adapter for UI-bound properties

Animating **UI-bound properties** needs the adapter for your GUI framework. The adapter re-exports the closed, friendly types under the same namespace (`Transition<T>`, `Transition<T>.StateSnapshot`, `TransitionEffect`, `TransitionEffects`, `Interpolator`, `UIThreadInspector`, `TransitionEx`), registers the per-framework value samplers, and marshals each frame write to the UI thread:

```bash
dotnet add package VeloxDev.WPF      # WPF
dotnet add package VeloxDev.Avalonia # Avalonia
dotnet add package VeloxDev.WinUI    # WinUI 3
dotnet add package VeloxDev.MAUI     # .NET MAUI
dotnet add package VeloxDev.WinForms # Windows Forms
dotnet add package VeloxDev.Razor    # Blazor (Razor components)
```

The adapter packages belong to VeloxDev's Platform Adapters suite; each one carries its own per-framework transition/theme wiring (`Interpolator`, `TransitionEffect(s)`, `UIThreadInspector`, ...) on top of `VeloxDev.Core`.

**Expected result:** the matching package is referenced; `Transition<Rectangle>.Create()` compiles (WPF example) and the WPF-specific samplers (`Brush`, `Color`, `Transform`, `CornerRadius`, `Thickness`, `Point3D`, ...) are registered.

## 3. When can you skip the adapter?

The engine core alone is enough when you drive the primitives directly and the values need no UI-thread marshaling — the pattern exercised by `Src/Core/VeloxDev.Core.Test/TransitionSystem/SamplingLoopTests.cs` (a `StateCore` holding `double` targets, a `TransitionEffectCore`, a `InterpolatorCore`-derived producer, and an interpreter that applies frames inline). This is what "Transition needs no adapter for non-UI values" means.

The out-of-box `Transition<T>` builder, however, is shipped by each adapter package, so the simplest path to the top-level API — including for targets that are plain objects inside a running app — is to reference the adapter for your framework. UI-bound targets additionally require the adapter so that property writes are dispatched on the owning UI thread (see [UI Thread & Marshaling](../06_ui-thread-marshaling/index.md)).
