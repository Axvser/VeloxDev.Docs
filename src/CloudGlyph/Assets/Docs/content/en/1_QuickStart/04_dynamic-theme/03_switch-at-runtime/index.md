# Dynamic Theme — Switch at Runtime

## 1. Prepare animated switching

Theme switching interpolates the property values frame by frame through the TransitionSystem engine. The engine resolves a sampler for each property's runtime type through a platform `Interpolator`, so install one before the first animated switch (the setting is global; call it once). You usually do this together with the registration from [Declare & Register](../02_declare-and-register/index.md):

```csharp
private void LoadTheme()
{
    InitializeTheme();

    // Global: required only for animated switching. Interpolator is the adapter type.
    ThemeManager.SetPlatformInterpolator(new Interpolator());

    // Global: where does each animation start from?
    ThemeManager.StartModel = StartModel.Cache;
}
```

`StartModel` chooses the animation's starting value (enum `StartModel`, default `Cache`): `Cache` starts each interpolation from the value already cached for the property, `Reflect` reads the object's current property value through reflection instead. `Interpolator` and `TransitionEffects` come from your platform adapter (namespace `VeloxDev.TransitionSystem`); `TransitionEffects.Theme` is the preset the demos use:

```csharp
TransitionEffects.Theme.Duration // 0.46 s
TransitionEffects.Empty.Duration // TimeSpan.Zero
```

**Expected result:** `ThemeManager.SetPlatformInterpolator(new Interpolator())` compiles against the adapter and `StartModel` reads back `StartModel.Cache` (pinned by `ThemeBasicsTests.StartModel_DefaultIsCache`).

## 2. Animated vs instant switching

Switch to another theme **with** an animation through `Transition<T>(effect)`:

```csharp
private static void ReverseThemeWithAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    else
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
}
```

or **without** interpolation through `Jump<T>()`:

```csharp
private static void ReverseThemeWithOutAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Jump<Light>();
    else
        ThemeManager.Jump<Dark>();
}
```

Both notify every registered `IThemeObject`: `ExecuteThemeChanging(old, new)` fires before the values move and `ExecuteThemeChanged(old, new)` fires after the target values are applied. The generator surfaces these as partial hooks you can implement — `OnThemeChanged` in the demos shows a message box:

```csharp
partial void OnThemeChanged(Type? oldValue, Type? newValue)
{
    MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
}
```

`SetCurrent<T>()` only updates `ThemeManager.Current` without touching registered objects — useful to seed the starting theme before any window registers.

**Expected result:** clicking the toggle animates the mapped properties to the target theme over `TransitionEffects.Theme` (0.46 s); `Jump<T>()` applies the target values instantly; the partial hooks fire with `(oldValue, newValue)`.

## 3. Runtime overrides and the UI-thread note

The generated API also lets you override and restore a value for one instance and one theme at runtime:

```csharp
// Override the Light value of Background, then re-apply immediately if Light is current
SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" });

// Remove the override; the static Light value is used again
RestoreThemeValue<Light>(nameof(Foreground));
```

`SetThemeValue<T>` records a per-instance override for theme `T` in the instance's active cache and re-applies the property if `T` is the theme currently active; otherwise the override is picked up as soon as a switch to `T` runs (active values take precedence over the static `ThemeCache` values). `GetStaticThemeCache()` and `GetActiveThemeCache()` expose both caches for inspection.

**UI-thread note.** In a desktop app, apply the initial theme and start a switch from the **UI thread**. The animation loop inside `ThemeManager.Transition` awaits its frames and resumes on the synchronization context that was current when the switch was invoked — normally the dispatcher of the window you switched from — so every per-frame property write lands back on the UI thread. Starting a switch from a thread with no captured UI synchronization context runs the frames on a thread-pool thread, which is unsafe for UI-bound property writes. `Jump<T>()` applies its values with no interpolation and (without a concurrent transition holding the internal lock) completes on the calling thread.

**Expected result:** while `Light` is current, the `SetThemeValue` override is visible immediately; `RestoreThemeValue` returns the property to its static `Light` value.
