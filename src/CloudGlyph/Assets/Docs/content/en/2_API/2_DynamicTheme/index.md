# Dynamic Theme — API Reference

## Namespace: `VeloxDev.DynamicTheme`

### Class: `ThemeManager`

Static entry point for theme state and switching. All members are static.

##### Properties

| Name | Type | Description |
|---|---|---|
| `Current` | `Type` | The active theme type. Default: `typeof(Dark)`. |
| `StartModel` | `StartModel` | How the start value of an animated switch is obtained. Default: `StartModel.Cache`. |

##### Methods

#### ThemeManager.SetPlatformInterpolator

**Signature:**
`public static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore`

| Parameter | Type | Description |
|---|---|---|
| `interpolator` | `T` | The platform interpolator instance (e.g. `new Interpolator()` from the adapter). |

**Returns:** `void`

**Notes:**
- Required once for animated theme transitions.

#### ThemeManager.SetCurrent

**Signature:**
`public static void SetCurrent<T>() where T : ITheme`

**Returns:** `void`

**Notes:**
- Sets `Current` to `typeof(T)`. Primarily used internally; prefer `Transition<T>` / `Jump<T>`.

#### ThemeManager.Register / Unregister

**Signature:**
`public static void Register(IThemeObject target)`
`public static void Unregister(IThemeObject target)`

| Parameter | Type | Description |
|---|---|---|
| `target` | `IThemeObject` | A theme-aware object (typically auto-registered by `InitializeTheme()`). |

**Returns:** `void`

**Notes:**
- Live instances are tracked via `ConditionalWeakTable` + `WeakReference`, so registration never leaks.

#### ThemeManager.Transition

**Signature:**
`public static void Transition<T>(ITransitionEffectCore effect) where T : ITheme`
`public static async void Transition(Type themeType, ITransitionEffectCore effect)`

| Parameter | Type | Description |
|---|---|---|
| `themeType` / `T` | `Type` / `ITheme` | Target theme. |
| `effect` | `ITransitionEffectCore` | Transition effect (FPS, duration, easing). |

**Returns:** `void` (asynchronous)

**Exceptions:** none — invalid theme types are ignored with a debug message.

**Example:**
```text
// Source: Demo
ThemeManager.Transition<Light>(TransitionEffects.Theme);
```

**Notes:**
- Interpolates every registered object's themed properties frame by frame, then raises `ExecuteThemeChanged`.

#### ThemeManager.Jump

**Signature:**
`public static void Jump<T>() where T : ITheme`
`public static async void Jump(Type themeType)`

**Returns:** `void`

**Example:**
```text
// Source: Demo
ThemeManager.Jump<Dark>();
```

**Notes:**
- Switches instantly without animation.

---

### Enum: `StartModel`

`[Flags] public enum StartModel : int { Reflect = 1, Cache = 2 }`

| Value | Description |
|---|---|
| `Reflect` | Read the object's current property value as animation start (via reflection). |
| `Cache` | Use the cached theme value for the current theme as animation start. |

---

### Class: `Dark` / `Light`

`public class Dark : ITheme` — empty marker types implementing `ITheme`.

---

### Class: `ThemeCache`

Central store of theme property values.

##### Methods

| Member | Signature | Description |
|---|---|---|
| `IsTypeRegistered` | `public static bool IsTypeRegistered(Type type)` | Whether the type has cached theme properties. |
| `RegisterType` | `public static void RegisterType(Type type, Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)> properties)` | Registers a type's theme properties. |
| `RegisterConverter` | `public static string RegisterConverter(IThemeValueConverter converter)` | Registers a converter and returns its key. |
| `GetConverter` | `public static IThemeValueConverter? GetConverter(string key)` | Looks up a converter by key. |
| `GetStaticForType` | `public static Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticForType(Type type)` | Static default values for a type. |
| `GetOrCreateActiveEntry` | `public static InstanceCache GetOrCreateActiveEntry(IThemeObject instance)` | Active (runtime) overrides for an instance. |
| `TryGetActiveEntry` | `public static InstanceCache? TryGetActiveEntry(IThemeObject instance)` | |
| `RemoveActiveEntry` | `public static void RemoveActiveEntry(IThemeObject instance)` | |
| `TryGetDefaultValue` | `public static bool TryGetDefaultValue(Type type, string propertyName, Type themeType, out object? value)` | |

##### Nested Type

`public sealed class InstanceCache { public Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> Overrides { get; set; } = []; }`

---

### Attribute: `ThemeConfigAttribute<TConverter, TTheme1, ...>`

Six arities: `<TConverter, TTheme1..TTheme2>` up to `<TConverter, TTheme1..TTheme7>`, where `TConverter : class, IThemeValueConverter` and each `TThemeN : ITheme`.

**Constructors:**
`(string propertyName, object?[] themeContext1, object?[] themeContext2, ... , object?[] themeContextN)`

| Parameter | Type | Description |
|---|---|---|
| `propertyName` | `string` | Target property name (e.g. `nameof(Background)`). |
| `themeContextN` | `object?[]` | Value parameters for the Nth theme. |

**Attributes:** `AttributeTargets.Class`, `AllowMultiple = true`, `Inherited = false`.

**Example:**
```text
// Source: Demo
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
```

---

### Interface: `ITheme`

`public interface ITheme` — empty marker interface for theme types.

---

### Interface: `IThemeObject`

Implemented (via source generator) on any class decorated with `[ThemeConfig]`.

| Member | Signature |
|---|---|
| `InitializeTheme` | `void InitializeTheme()` |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` |
| `GetStaticThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticThemeCache()` |
| `GetActiveThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetActiveThemeCache()` |

---

### Interface: `IThemeValueConverter`

| Member | Signature |
|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` |

**Notes:**
- Platform adapters ship implementations: `BrushConverter`, `ColorConverter`, `ThicknessConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ObjectConverter`.

---

## Namespace: `VeloxDev.TransitionSystem` (backing engine, referenced by Theme)

### Abstract Class: `InterpolatorCore`

`public abstract class InterpolatorCore : IFrameInterpolatorCore`

##### Static Members

| Member | Signature | Description |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` | Registry of per-type interpolators. |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` | |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` | |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` | |

### Interface: `ITransitionEffectCore`

| Member | Type / Signature |
|---|---|
| `FPS` | `int FPS { get; }` |
| `Duration` | `TimeSpan Duration { get; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; }` |
| `LoopTime` | `int LoopTime { get; }` |
| `Ease` | `IEaseCalculator Ease { get; }` |
| Events | `Awaked / Start / Update / LateUpdate / Canceled / Completed / Finally` — `EventHandler<TransitionEventArgs>` |
| `Clone` | `ITransitionEffectCore Clone()` |

### Interface: `IEaseCalculator`

`public interface IEaseCalculator { double Ease(double t); }`

### Static Class: `Eases`

Exposes `Default` plus `Sine`, `Quad`, `Cubic`, `Quart`, `Quint`, `Expo`, `Circ`, `Back`, `Elastic`, `Bounce` — each with `In` / `Out` / `InOut` members returning `IEaseCalculator`.

---

## Namespace: platform adapters (`VeloxDev.WPF` / `VeloxDev.Avalonia`)

### Class: `Interpolator`

`public class Interpolator : InterpolatorCore<InterpolatorOutput, DispatcherPriority>`

- WPF static ctor registers interpolators for `Brush`, `Thickness`, `Point`, `CornerRadius`, `Transform`, `Size`, `Rect`, `Vector`, `Color`, `DropShadowEffect`, `Point3D`, `Vector3D`.
- Avalonia registers `IBrush`, `ITransform`, `Thickness`, `Point`, `CornerRadius`, `Size`, `PixelPoint`, `PixelSize`, `PixelRect`, `RelativePoint`, `RelativeRect`, `Color`, `BoxShadows`, `GridLength`.

### Class: `TransitionEffect`

`public class TransitionEffect : TransitionEffectCore<DispatcherPriority>` — `Priority = DispatcherPriority.Render`.

### Static Class: `TransitionEffects`

| Member | Value |
|---|---|
| `Empty` | `Duration = TimeSpan.Zero` |
| `Theme` | `Duration = TimeSpan.FromSeconds(0.46)` |
| `Hover` | `Duration = TimeSpan.FromSeconds(0.32)` |

### Value Converters

`DoubleConverter`, `PointConverter`, `ThicknessConverter`, `CornerRadiusConverter`, `ColorConverter`, `BrushConverter`, `ObjectConverter` — all implement `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`.
