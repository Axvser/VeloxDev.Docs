# API — Dynamic Theme · ThemeManager

## Namespace: `VeloxDev.DynamicTheme`

### Class: `ThemeManager`

Static entry point for theme state and switching. All members are static. Live instances are tracked through a `ConditionalWeakTable<IThemeObject, ...>` plus a `List<WeakReference<IThemeObject>>`, so registration never leaks. The manager does not time a switch itself: an animated switch is run by the platform's `TransitionSchedulerCore`, resolved per target through `InterpolatorCore.CreateScheduler`, and every target of one switch is anchored to a single `ITimeSourceControl`. Lifecycle callbacks are raised on every registered object around each switch.

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
// Source: Demo (Examples/Theme/WPF/Demo/App.xaml.cs)
ThemeManager.SetPlatformInterpolator(new Interpolator());
```

**Notes:**
- Must be called once before any animated transition so that themed property types resolve to platform samplers. `InterpolatorCore` is declared in `VeloxDev.TransitionSystem.Abstractions`; the concrete adapter type is the platform `Interpolator` in `VeloxDev.TransitionSystem` (see [04 PlatformAdapters](../04_PlatformAdapters/index.md)).
- Beyond forcing the adapter's sampler registrations to run, this is what makes an animated switch possible at all: `Transition` asks this instance for a scheduler through `InterpolatorCore.CreateScheduler` (`ThemeManager.cs`, `RunSwitch`). Without it, the switch still happens — immediately, with no animation.
- Without a registered sampler for a property type, an animated switch still runs, but that property holds its old value for the whole switch and is written to its target value once the switch ends (`ThemeManager.cs`, `ApplyHeldValues`).

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
// Source: Demo (Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs, ReverseThemeWithAnimation)
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
| `effect` | `ITransitionEffectCore` | The transition effect that drives the switch. It must be the platform's own effect type so that `InterpolatorCore.CreateScheduler` accepts it. |

**Returns:** `void` (asynchronous — the method is `async void`)

**Exceptions:** none declared — an invalid `themeType` (`themeType == Current`, or not assignable to `ITheme`) is ignored with `Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")`. An exception raised inside the switch is caught by `Transition` itself and written as `Debug.WriteLine("[ThemeManager] Error during theme transition: ...")`; an `async void` caller cannot receive it.

**Notes:**
- Cancels any switch in flight (`CancelActiveSwitch`), prunes dead `WeakReference`s, then calls `ExecuteThemeChanging(oldValue, newValue)` on every registered object.
- Awaits the private `async Task<bool> RunSwitch`, which builds the per-target entries with `PrepareSamplers`, resolves each target's scheduler through `InterpolatorCore.CreateScheduler`, and runs them all on one shared `ITimeSourceControl`. `RunSwitch` returns `false` when the switch was cancelled or superseded, and `Transition` then announces nothing and leaves `Current` unchanged.
- Falls back to an immediate, un-animated switch (`ApplyImmediately`) when no platform interpolator is set, when no target has an animatable property, or when the platform's scheduler declines the effect.
- `RunSwitch` is a private `async Task<bool>` precisely because `Transition` is `async void`: exceptions thrown by the adapters' samplers and schedulers are caught inside it (`Debug.WriteLine("[ThemeManager] Error during transition execution: ...")`) instead of escaping into the process.
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
- Delegates to `Jump(typeof(T))`. Switches instantly without animation and cancels any animated switch in flight.

#### ThemeManager.Jump(Type)

**Signature:**
`public static void Jump(Type themeType)`

| Parameter | Type | Description |
|---|---|---|
| `themeType` | `Type` | Target theme type. |

**Returns:** `void` (synchronous)

**Exceptions:** none declared — an invalid `themeType` is ignored with the same debug message as `Transition`.

**Notes:**
- Cancels any switch in flight (`CancelActiveSwitch`) before applying, so a jump supersedes a running `Transition` rather than racing it.
- Applies end values directly through `ApplyImmediately`: no timeline, no effect, no sampling. It therefore does not depend on `SetPlatformInterpolator` and is not constrained by the platform's `ITransitionEffect<TPriority>` type.
- Raises `ExecuteThemeChanging` before and `ExecuteThemeChanged` after, and updates `Current`.

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
