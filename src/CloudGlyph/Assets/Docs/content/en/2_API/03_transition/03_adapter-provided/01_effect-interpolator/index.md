# Transition — Adapter: `Interpolator`, `TransitionEffect`, `TransitionEffects`, `State`

Each adapter provides an `Interpolator` registry subclass, an `Effect` descriptor with a platform default, a set of preset effects, and a `State` declared-state bag. All live in the `VeloxDev.TransitionSystem` namespace of the adapter assembly.

### Class: `Interpolator : InterpolatorCore`

The adapter registry subclass. It inherits the engine defaults (see [abstractions](../../01_abstractions/index.md)) and its static constructor additionally registers the platform value types:

| Adapter | Platform sampler registrations (`RegisterInterpolator(typeof(X), ...)`) |
|---|---|
| WPF | `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect`, `Point3D`, `Vector3D` |
| Avalonia | `IBrush`, `ITransform`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows`, `GridLength` |
| WinUI | `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Projection`, `Size`, `Rect`, `GridLength`, `Color` |
| MAUI | `Brush`, `Thickness`, `Point`, `PointF`, `CornerRadius`, `Transform`, `Color`, `Size`, `SizeF`, `Rect`, `RectF`, `Shadow` |
| WinForms | `Padding` |
| Razor | `string` (via `StringSampler`) |
| Jalium | `Point`, `Rect`, `Thickness`, `CornerRadius`, `Size`, `Color`, `Brush`, `SolidColorBrush`, `Transform`, `Jalium.UI.Media.Media3D.Transform3D` |

**Notes:**
- The registered samplers implement `ISampler` and are shipped by the same adapter under `PlatformAdapters/Samplers/*.cs` (namespace `VeloxDev.Adapters.NativeSamplers` inside each adapter assembly). Brush/transform-like reference targets are interpolated without mutating the transition declaration's shared start/end instances (see `ISampler` contract in [transitionsystem/sampling-capture](../../00_transitionsystem/00_sampling-capture/index.md)).
- Registration is *in addition to* the engine default samplers seeded by the `InterpolatorCore` static constructor, so numeric, `System.Drawing` and (non-`netstandard2.0`) `System.Numerics` types always interpolate.

### Override: `Interpolator.CreateScheduler`

Every adapter also overrides `InterpolatorCore.CreateScheduler` (see [abstractions](../../01_abstractions/index.md)). WPF, Avalonia and Jalium write it exactly like this:

```csharp
public override TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)
    => effect is ITransitionEffect<DispatcherPriority>
        ? (TransitionSchedulerCore)TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>.FindOrCreate(target)
        : null;
```

WinUI substitutes `DispatcherQueuePriority`; MAUI, WinForms and Razor substitute `NonPriority`. It is the seam the theme system runs on — a theme switch spans targets of many runtime types, so Core cannot name the type argument of `Transition<T>`, and which inspector, interpreter and priority make up a scheduler is the one thing only the platform knows. The `null` branch is the honest answer for "this effect does not belong to this platform" (a `DispatcherPriority` effect handed to WinUI's interpolator), mirroring the cast the scheduler itself performs before running; the caller then switches without animating instead of starting a run that draws nothing. Going through `FindOrCreate` — never `new` — is what files the scheduler under the target, so that a later `Transition.Pause` / `Transition.Seek` / `Transition.Exit(target)` can find it (see [ui-inspector](../02_ui-inspector/index.md)). *Verified by:* each adapter's `PlatformAdapters/Interpolator.cs`.

### Class: `TransitionEffect` — priority default

Each adapter's effect subclasses `TransitionEffectCore` (MAUI, WinForms, Razor) or `TransitionEffectCore<TPriorityCore>` (WPF, Avalonia, Jalium, WinUI). Where a priority exists it sets a default that overrides the base's zero value:

| Adapter | Base type | Default `Priority` |
|---|---|---|
| WPF | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| Avalonia | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| Jalium | `TransitionEffectCore<DispatcherPriority>` | `DispatcherPriority.Render` |
| WinUI | `TransitionEffectCore<DispatcherQueuePriority>` | `DispatcherQueuePriority.High` |
| MAUI / WinForms / Razor | `TransitionEffectCore` | — (no priority) |

All timing members (`Duration`, `IsAutoReverse`, `LoopTime`, `Ease`, `FPS`) are inherited from `TransitionEffectCore` (see [abstractions](../../01_abstractions/index.md)).

### Class: `TransitionEffects` — presets

A per-adapter effect factory exposing three read/write static presets:

```csharp
public static class TransitionEffects       // (an instance class, but identical static members, on WinUI)
{
    public static TransitionEffect Empty { get; set; }   // Duration = 0
    public static TransitionEffect Theme { get; set; }   // Duration = 0.46 s
    public static TransitionEffect Hover { get; set; }   // Duration = 0.32 s
}
```

**Notes:**
- On every adapter except WinUI, `TransitionEffects` is a `static class`. On WinUI the type is a plain class whose members are still static, so usage is identical.
- *Verified by:* WPF demo `Animation0`/`CreateResetRec0` pass `.Effect(TransitionEffects.Empty)`.

### Class: `State : StateCore`

An empty subclass of `StateCore`; it is the `TStateCore` type parameter the adapter's `Transition<T>` uses, so `GetState()` returns this concrete `State` (an `IFrameState`). All behavior is inherited from `StateCore` (see [abstractions](../../01_abstractions/index.md)).
