# Dynamic Theme — Animated vs Instant Switching

## 1. Animated switching — `Transition`

```csharp
public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme
public static async void Transition(Type themeType, ITransitionEffectCore effect)
```

`Transition<T>` forwards to the `Type` overload, which is `async void`: it returns to the caller once every registered target has been prepared, written and scheduled — its first await is the join over the per-target runs — and it advances `ThemeManager.Current` only when the runs actually land. Because it is `async void`, a fault inside the run is reported through `Debug.WriteLine` rather than thrown at the caller; nothing awaits this call.

A switch is rejected before anything happens when the target theme is the theme already current, or when the type does not implement `ITheme`. Both guards are shared with `Jump`.

```csharp
private static void ReverseThemeWithAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
    {
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    }
    else
    {
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
    }
}
```

Source: `Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`, member `ReverseThemeWithAnimation` (identical in `Examples/Theme/Avalonia Trimmed/Demo/Views/MainWindow.axaml.cs`).

**Expected result:** the mapped properties interpolate to the target theme over `TransitionEffects.Theme` (0.46 s) and land exactly on the declared end values — the last frame is pinned to the endpoint, so the result does not depend on the easing curve returning exactly `1`. Pinned by `ThemeTransitionTests.Switch_LandsExactlyOnTheTargetValue`.

## 2. Instant switching — `Jump`

```csharp
public static void Jump(Type themeType)
public static void Jump<T>() where T : ITheme
```

`Jump(Type)` is **synchronous `void`** — it has no timeline and no effect, so the whole switch is over before the call returns. It:

1. cancels the switch in flight, if any (`CancelActiveSwitch`),
2. announces `ExecuteThemeChanging(old, new)` to every registered target,
3. writes every target value through `ApplyImmediately`,
4. advances `ThemeManager.Current` and announces `ExecuteThemeChanged(old, new)`.

Because there is no timeline and no effect, `Jump` is not constrained by the platform's `ITransitionEffect<TPriority>` type and does **not** require `SetPlatformInterpolator` — it is self-contained. It also skips targets that were never registered with `ThemeManager`.

```csharp
private static void ReverseThemeWithOutAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
    {
        ThemeManager.Jump<Light>();
    }
    else
    {
        ThemeManager.Jump<Dark>();
    }
}
```

Source: `Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`, member `ReverseThemeWithOutAnimation`.

**Expected result:** the mapped properties hold the target theme's values as soon as the call returns, and a target that was never registered is left untouched. Pinned by `ThemeTransitionTests.Jump_WritesTheTargetValue` and `Jump_SkipsAnUnregisteredTarget`.

## 3. The hooks and `SetCurrent`

Both paths notify the same two members of every registered `IThemeObject`: `ExecuteThemeChanging(old, new)` before any value moves, and `ExecuteThemeChanged(old, new)` after the target values are applied. The generator surfaces them as partial hooks you implement — implementing them is the whole subscription mechanism, there is no event to attach a handler to:

```csharp
partial void OnThemeChanged(Type? oldValue, Type? newValue)
{
    MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
}
```

Source: `Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs` — the Avalonia twin shows a window notification instead.

`ExecuteThemeChanged` fires only for a switch that lands. A switch superseded by a newer one — `Transition` cancels the running switch when the next one starts — never advances `Current` and never announces its end, so `OnThemeChanging` can be seen more often than `OnThemeChanged`. The scale demo prints both hooks into one line of its UI precisely so the difference is visible, and labels an interrupted switch `被中断` (interrupted).

`SetCurrent<T>()` sets `ThemeManager.Current` and nothing else: no callbacks, no values written. Use it to seed the starting theme before any element registers itself — the scale demos do it in `App`, right after installing the interpolator, so that the values each element applies as it initialises are the ones for that theme.

**Expected result:** `OnThemeChanged` runs once per landed switch with the old and new theme types; `SetCurrent<Dark>()` flips `ThemeManager.Current` without touching registered objects. Pinned by `ThemeBasicsTests.ThemeManager_SetCurrent_Changes`.
