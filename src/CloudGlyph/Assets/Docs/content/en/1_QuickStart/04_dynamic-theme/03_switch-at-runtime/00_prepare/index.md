# Dynamic Theme — Prepare an Animated Switch

## 1. Install the platform interpolator

`ThemeManager.Transition` resolves one scheduler per target through the platform seam — `InterpolatorCore.CreateScheduler(object target, ITransitionEffectCore effect)` — because which inspector, interpreter and dispatcher priority to animate with is the one thing the framework-agnostic core cannot name. The adapter answers that seam, so install it once, globally, before the first animated switch:

```csharp
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

The call is **mandatory for an animated switch, and only for an animated switch**. Without it a switch still happens — it is applied at once, with no animation and no error (`ThemeManager.RunSwitch` degrades to `ApplyImmediately` when no interpolator is installed). `Jump<T>()` never needs it ([Animated vs Instant Switching](../01_transition-and-jump/index.md)).

`Interpolator` is the adapter type in the `VeloxDev.TransitionSystem` namespace (`VeloxDev.WPF`, `VeloxDev.Avalonia`). Its static constructor registers that framework's samplers — WPF registers `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect`, `Point3D` and `Vector3D` — and its `CreateScheduler` returns the platform scheduler when the effect it is handed is the platform's own `TransitionEffect`, or `null` otherwise. One `null` answer makes the whole switch fall back to an instant apply.

The setting is process-wide, so the scale demos do it once in `App` (`OnStartup` for WPF, `OnFrameworkInitializationCompleted` for Avalonia) so that it is in place before any element registers itself.

**Expected result:** `SetPlatformInterpolator(new Interpolator())` compiles against the adapter, and a later `ThemeManager.Transition<T>(...)` animates rather than jumping. Pinned by `ThemeTransitionTests.Switch_WithNoPlatformSeam_AppliesImmediately`, which passes an interpolator whose seam answers `null` and observes the switch land immediately.

## 2. Choose where each animation starts

`StartModel` (`[Flags]` enum, default `Cache`) decides the value each property starts interpolating from:

- `StartModel.Cache` — the value already cached for the property: the instance's **active** cache first (runtime overrides, see [Runtime Overrides & Threading](../03_overrides-and-threading/index.md)), then the shared static cache. This is what makes a switch read as "from the current theme's value to the target theme's value".
- `StartModel.Reflect` — `PropertyInfo.GetValue(target)`: whatever the object happens to hold right now.

`ThemeManager` writes the chosen start value back onto the target before the run begins, so the cached start is the one that is actually animated from — the engine's own `Prepare` can only read the start off the target.

```csharp
ThemeManager.StartModel = StartModel.Cache;
```

**Expected result:** `StartModel` reads back `StartModel.Cache` unless you set it otherwise. Pinned by `ThemeBasicsTests.StartModel_DefaultIsCache` and `StartModel_FlagsEnum`.

## 3. One call site

The minimal demo does all of the above in one method, after `InitializeComponent()` has made the window usable:

```csharp
private void LoadTheme()
{
    InitializeTheme(); // this call is required and must come after InitializeComponent()

    // [ Applies globally ]
    // If you do not use themed transitions, the interpolator does not need to be configured;
    // otherwise this call is mandatory.
    ThemeManager.SetPlatformInterpolator(new Interpolator());

    // [ Applies globally ]
    // When the theme changes, should the animation's starting state come from the cache, or
    // should reflection read the current state as the starting point?
    ThemeManager.StartModel = StartModel.Cache;
}
```

Source: `Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`, member `LoadTheme`; the Avalonia twin (`Examples/Theme/Avalonia Trimmed/Demo/Views/MainWindow.axaml.cs`, same member name) has the same body.

**Expected result:** after `LoadTheme()` the window is registered, the seam is installed and the start model is set — the first `Transition<T>` animates.

## 4. Pick an effect

The adapter ships presets in `TransitionEffects`: `Theme` (0.46 s), `Hover` (0.32 s) and `Empty` (`TimeSpan.Zero`). An effect is read by every target on every frame, so pass a shared preset as given and never mutate one while a switch that uses it is running. The scale demos instead build their own effect long enough for the controls to have something to interrupt:

```csharp
// Long enough that pause and seek have something to interrupt.
private readonly TransitionEffect _effect = new() { Duration = TimeSpan.FromSeconds(3), FPS = 60 };
```

Source: `Examples/Theme/WPF/Demo/MainWindow.xaml.cs`, field `_effect` (the Avalonia demo's `Views/MainWindow.axaml.cs` declares the same field). `FPS` is a maximum sample rate, not a frame grid.

**Expected result:** `TransitionEffects.Theme.Duration` is 0.46 s and `TransitionEffects.Empty.Duration` is `TimeSpan.Zero`.
