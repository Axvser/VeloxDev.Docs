# API — Dynamic Theme · ThemeManager

## Namespace: `VeloxDev.DynamicTheme`

### Class: `ThemeManager`

Static entry point for theme state and switching. All members are static. Live instances are tracked through a `ConditionalWeakTable<IThemeObject, ...>` plus a `List<WeakReference<IThemeObject>>`, so registration never leaks.

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`.

##### Properties

| Name | Type | Description |
|---|---|---|
| `Current` | `Type` | The active theme type. Default: `typeof(Dark)`. Setter is `internal`. |
| `StartModel` | `StartModel` | How the start value of an animated switch is obtained. Default: `StartModel.Cache`. |

#### ThemeManager.SetPlatformInterpolator

**Signature:**
`public static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore`

| Parameter | Type | Description |
|---|---|---|
| `interpolator` | `T` | The platform interpolator instance (e.g. `new Interpolator()` from the adapter). |

**Returns:** `void`

**Example:**
```text
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs)
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

**Notes:**
- Required once for animated theme transitions. Without it, `Transition<T>` still runs but properties without a registered interpolator are applied as a simple two-frame switch.

#### ThemeManager.SetCurrent

**Signature:**
`public static void SetCurrent<T>() where T : ITheme`

**Returns:** `void`

**Example:**
```text
// Source: Test (ThemeBasicsTests.ThemeManager_SetCurrent_Changes)
ThemeManager.SetCurrent<Light>();
```

**Notes:**
- Sets `Current` to `typeof(T)` without raising any theme-change callbacks. Primarily used internally; prefer `Transition<T>` / `Jump<T>`.

#### ThemeManager.Register

**Signature:**
`public static void Register(IThemeObject target)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `IThemeObject` | A theme-aware object (typically auto-registered by the generated `InitializeTheme()`). |

**Returns:** `void`

**Notes:**
- Adds the target to the active cache and to the `WeakReference` list. Calling `Register` on an already-registered target is a no-op.
- Duplicate registrations are guarded by the `ConditionalWeakTable` lookup.

#### ThemeManager.Unregister

**Signature:**
`public static void Unregister(IThemeObject target)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `IThemeObject` | A theme-aware object. |

**Returns:** `void`

**Notes:**
- Removes the target's active cache entry and removes its `WeakReference` from the list.

#### ThemeManager.Transition<T>

**Signature:**
`public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme`

| Parameter | Type | Description |
|---|---|---|
| `effect` | `ITransitionEffectCore` | Transition effect (FPS, duration, easing). |

**Returns:** `void` (asynchronous)

**Example:**
```text
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs)
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**Notes:**
- Delegates to `Transition(typeof(T), effect)`.
- Invalid theme types are ignored with a debug message.

#### ThemeManager.Transition(Type, ITransitionEffectCore)

**Signature:**
`public static async void Transition(Type themeType, ITransitionEffectCore effect)`

| Parameter | Type | Description |
|---|---|---|
| `themeType` | `Type` | Target theme type. |
| `effect` | `ITransitionEffectCore` | Transition effect (FPS, duration, easing). |

**Returns:** `void` (asynchronous)

**Exceptions:** none declared — an invalid `themeType` (`themeType == Current` or not assignable to `ITheme`) is ignored with `Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")`.

**Notes:**
- Cancels any running transition, prunes dead `WeakReference`s, then calls `ExecuteThemeChanging(old, new)` on every registered object.
- Prepares per-property samplers (`PrepareSamplers`) and drives a Stopwatch-based sampling loop (`ExecuteTransition`) over the effect's duration.
- After the final sample, sets `Current = themeType` and calls `ExecuteThemeChanged(old, new)` on every registered object.

#### ThemeManager.Jump<T>

**Signature:**
`public static void Jump<T>() where T : ITheme`

**Returns:** `void`

**Example:**
```text
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs)
ThemeManager.Jump<Dark>();
```

**Notes:**
- Delegates to `Jump(typeof(T))`. Switches instantly without animation.

#### ThemeManager.Jump(Type)

**Signature:**
`public static async void Jump(Type themeType)`

| Parameter | Type | Description |
|---|---|---|
| `themeType` | `Type` | Target theme type. |

**Returns:** `void` (asynchronous)

**Exceptions:** none declared — an invalid `themeType` is ignored with the same debug message as `Transition`.

**Notes:**
- Runs a zero-duration pass (`durationMs = 0`), so the first sample has `rawT = 1` and all properties are set directly to the target theme value without interpolation. Raises `ExecuteThemeChanging` before and `ExecuteThemeChanged` after.

---

## Enum: `StartModel`

`[Flags] public enum StartModel : int { Reflect = 1, Cache = 2 }`

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`.

| Value | Description |
|---|---|
| `Reflect` | Read the object's current property value (via `PropertyInfo.GetValue`) as the animation start value. |
| `Cache` | Use the cached value for the current theme as the animation start value. |

**Notes:**
- Default is `StartModel.Cache` (verified by `ThemeBasicsTests.StartModel_DefaultIsCache`).
- It is a `[Flags]` enum — `StartModel.Reflect | StartModel.Cache` is a valid combination (verified by `ThemeBasicsTests.StartModel_FlagsEnum`).

---

## Class: `Dark` / `Light`

`public class Dark : ITheme` — empty marker type implementing `ITheme`.
`public class Light : ITheme` — empty marker type implementing `ITheme`.

Source: `Src/Core/VeloxDev.Core/DynamicTheme/Dark.cs`, `Src/Core/VeloxDev.Core/DynamicTheme/Light.cs`.

**Notes:**
- `ThemeManager.Current` defaults to `typeof(Dark)` (verified by `ThemeBasicsTests.Dark_ImplementsITheme`, `Light_ImplementsITheme`, `ThemeManager_DefaultCurrent_IsDark`).
