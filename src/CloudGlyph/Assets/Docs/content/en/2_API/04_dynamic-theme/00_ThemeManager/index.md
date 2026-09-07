# API — Dynamic Theme · ThemeManager

## Namespace: `VeloxDev.DynamicTheme`

### Class: `ThemeManager`

Static entry point for theme state and switching. All members are static. Live instances are tracked through a `ConditionalWeakTable<IThemeObject, ...>` plus a `List<WeakReference<IThemeObject>>`, so registration never leaks. The manager drives its own Stopwatch-based sampling loop and raises lifecycle callbacks on every registered object around each switch.

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`.

##### Properties

| Name | Type | Description |
|---|---|---|
| `Current` | `Type` | The active theme type. Default: `typeof(Dark)`. The setter is `internal`; external callers switch through `Transition`/`Jump`/`SetCurrent`. |
| `StartModel` | `StartModel` | How the start value of an animated switch is obtained. Default: `StartModel.Cache`. |

#### ThemeManager.SetPlatformInterpolator

**Signature:**
`public static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore`

| Parameter | Type | Description |
|---|---|---|
| `interpolator` | `T` | The platform interpolator instance (e.g. the adapter's `new Interpolator()`). |

**Returns:** `void`

**Example:**
```csharp
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs, LoadTheme)
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

**Notes:**
- Must be called once before any animated transition so that themed property types resolve to platform samplers. `InterpolatorCore` is declared in `VeloxDev.TransitionSystem.Abstractions`; the concrete adapter type is the platform `Interpolator` in `VeloxDev.TransitionSystem` (see [04 PlatformAdapters](../04_PlatformAdapters/index.md)).
- Without a registered sampler for a property type, `Transition` still runs but that property is applied as a simple hold-until-end switch.

#### ThemeManager.SetCurrent

**Signature:**
`public static void SetCurrent<T>() where T : ITheme`

**Returns:** `void`

**Example:**
```csharp
// Source: Test (ThemeBasicsTests.ThemeManager_SetCurrent_Changes)
ThemeManager.SetCurrent<Light>();
```

**Notes:**
- Sets `Current` to `typeof(T)` without raising any theme-change callbacks and without applying values. Prefer `Transition<T>` / `Jump<T>` for visible switches.

#### ThemeManager.Register

**Signature:**
`public static void Register(IThemeObject target)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `IThemeObject` | A theme-aware object. |

**Returns:** `void`

**Notes:**
- Adds the target to the active cache and to the `WeakReference` list. Calling `Register` on an already-registered target is a no-op (guarded by the `ConditionalWeakTable` lookup).
- Normally invoked automatically by the generated `InitializeTheme()`; see [02 ThemeConfigAttribute](../02_ThemeConfigAttribute/index.md).

#### ThemeManager.Unregister

**Signature:**
`public static void Unregister(IThemeObject target)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `IThemeObject` | A theme-aware object. |

**Returns:** `void`

**Notes:**
- Removes the target's active cache entry and removes its `WeakReference` from the tracking list.

#### ThemeManager.Transition<T>

**Signature:**
`public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme`

| Parameter | Type | Description |
|---|---|---|
| `effect` | `ITransitionEffectCore` | Transition effect (ease and duration). |

**Returns:** `void` (delegates to the `Type` overload, which is `async void`)

**Example:**
```csharp
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs)
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**Notes:**
- Delegates to `Transition(typeof(T), effect)`.

#### ThemeManager.Transition(Type, ITransitionEffectCore)

**Signature:**
`public static async void Transition(Type themeType, ITransitionEffectCore effect)`

| Parameter | Type | Description |
|---|---|---|
| `themeType` | `Type` | Target theme type. |
| `effect` | `ITransitionEffectCore` | Transition effect whose `Ease` and `Duration` drive the animation. |

**Returns:** `void` (asynchronous)

**Exceptions:** none declared — an invalid `themeType` (`themeType == Current`, or not assignable to `ITheme`) is ignored with `Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")`.

**Notes:**
- Cancels any running transition, prunes dead `WeakReference`s, then calls `ExecuteThemeChanging(oldValue, newValue)` on every registered object.
- Resolves the per-property start/target values (per `StartModel`), normalizes endpoints through each property's `ISampler`, and drives a Stopwatch-based sampling loop that calls `ISampler.InsertFrame` with the eased time until `effect.Duration` elapses (≈1 ms yield per frame).
- On completion sets `Current = themeType` and calls `ExecuteThemeChanged(oldValue, newValue)` on every registered object.

#### ThemeManager.Jump<T>

**Signature:**
`public static void Jump<T>() where T : ITheme`

**Returns:** `void`

**Example:**
```csharp
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
- Runs a zero-duration pass (`durationMs = 0`, `Eases.Default`), so the first sample already has `t = 1` and every property is written directly to its target-theme value with no interpolation. Raises `ExecuteThemeChanging` before and `ExecuteThemeChanged` after, and updates `Current`.

---

## Enum: `StartModel`

`[Flags] public enum StartModel : int { Reflect = 1, Cache = 2 }`

Declared in `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs`.

| Value | Description |
|---|---|
| `Reflect` | Read the object's current property value (via `PropertyInfo.GetValue`) as the animation start value. |
| `Cache` | Use the cached value for the current theme as the animation start value (dynamic cache first, then the static default). |

**Notes:**
- Default is `StartModel.Cache` (verified by `ThemeBasicsTests.StartModel_DefaultIsCache`).
- The demos set `ThemeManager.StartModel = StartModel.Cache;` explicitly before any switch.
- It is marked `[Flags]` — `StartModel.Reflect | StartModel.Cache` is a valid value (verified by `ThemeBasicsTests.StartModel_FlagsEnum`).

---

## Classes: `Dark` / `Light`

`public class Dark : ITheme` — empty marker type implementing `ITheme`.
`public class Light : ITheme` — empty marker type implementing `ITheme`.

Source: `Src/Core/VeloxDev.Core/DynamicTheme/Dark.cs`, `Src/Core/VeloxDev.Core/DynamicTheme/Light.cs`.

**Notes:**
- `ThemeManager.Current` defaults to `typeof(Dark)`; both implement `ITheme` (verified by `ThemeBasicsTests.Dark_ImplementsITheme`, `Light_ImplementsITheme`, `ThemeManager_DefaultCurrent_IsDark`).
- The demos pass them only as generic arguments (`Transition<Light>`, `ThemeConfig<..., Light, Dark>`); neither demo subclasses them.
