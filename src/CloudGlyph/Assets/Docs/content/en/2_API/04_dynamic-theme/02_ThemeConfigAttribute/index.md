# API — Dynamic Theme · ThemeConfigAttribute and Contracts

## Namespace: `VeloxDev.DynamicTheme`

### Attribute: `ThemeConfigAttribute<TConverter, TTheme1, ...>`

Six generic arities, each decorating a class to map one property to one converted value per theme type. The attribute is repeatable on a single class (`AllowMultiple = true`), applies to classes only, and is not inherited.

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeConfigAttribute.cs`.

| Theme types | Generic parameters | Constraints |
|---|---|---|
| 2 | `<TConverter, TTheme1, TTheme2>` | `TConverter : class, IThemeValueConverter`; each `TThemeN : ITheme` |
| 3 | `<TConverter, TTheme1, TTheme2, TTheme3>` | same |
| 4 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4>` | same |
| 5 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4, TTheme5>` | same |
| 6 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4, TTheme5, TTheme6>` | same |
| 7 | `<TConverter, TTheme1, TTheme2, TTheme3, TTheme4, TTheme5, TTheme6, TTheme7>` | same |

Each arity declares one constructor:

`public ThemeConfigAttribute(string propertyName, object?[] themeContext1, object?[] themeContext2, ..., object?[] themeContextN)`

| Parameter | Type | Description |
|---|---|---|
| `propertyName` | `string` | Target property name (e.g. `nameof(Background)`). |
| `themeContextN` | `object?[]` | Raw value parameters for the Nth theme, in the order of the generic theme arguments. |

**Example:**
```csharp
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs)
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
```

**Notes:**
- `TConverter` is the strategy that turns a raw `object?[]` parameter list into the property's platform type (e.g. `BrushConverter` → a `Brush`; the Avalonia demo uses `ObjectConverter`). Converter implementations ship with each platform adapter and live in the same `VeloxDev.DynamicTheme` namespace (see [04 PlatformAdapters](../04_PlatformAdapters/index.md)).
- The attribute only declares data — applying it does nothing by itself. The theme source generator consumes it to emit the `IThemeObject` partial implementation.

### Source Generator: `Theme` (namespace `VeloxDev.Generators`)

`[Generator(LanguageNames.CSharp)] public class Theme : IIncrementalGenerator`

Source: `Src/Generators/VeloxDev.Core.Generator/Theme.cs`.

The generator reacts to `[ThemeConfig<...>]` on a **partial class** (currently the 2-to-6-theme arities, i.e. metadata arities 3–7) and emits an additional partial declaration for that class:

- Adds `: IThemeObject` when the base type does not already implement it.
- Emits `ExecuteThemeChanging(Type? oldValue, Type? newValue)` / `ExecuteThemeChanged(...)` that call the base implementation (when one exists) and then the **partial hooks** `partial void OnThemeChanging(Type? oldValue, Type? newValue)` / `partial void OnThemeChanged(...)` — declared without a body so the user can implement them in their own part of the class. The WPF demo implements `OnThemeChanged` to show a `MessageBox`; the Avalonia demo shows a `WindowNotificationManager` notification.
- Emits `InitializeTheme()`, which registers the type's static values through `ThemeCache.RegisterType`, calls `ThemeManager.Register(this)`, and applies the current theme's values to the decorated properties. The demos call `InitializeTheme()` right after `InitializeComponent()`.
- Emits `SetThemeValue<T>` / `RestoreThemeValue<T>` (runtime overrides) and the cache accessors `GetStaticThemeCache()` / `GetActiveThemeCache()`, plus `UpdatePropertyToCurrentTheme` / `UpdateAllPropertiesToCurrentTheme` helpers.

**Notes:**
- A class that merely implements `IThemeObject` without `[ThemeConfig]` is not processed.
- The converter is instantiated inline via `Activator.CreateInstance` at registration time — the generator does not use `ThemeCache.RegisterConverter`.

---

### Interface: `ITheme`

`public interface ITheme`

Empty marker interface for theme types. Implemented by `Dark`, `Light`, and any custom theme type.

Source: `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/ITheme.cs`.

---

### Interface: `IThemeObject`

Contract implemented (via the source generator) on any class decorated with `[ThemeConfig]` on a partial class. Source: `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeObject.cs`.

| Member | Signature |
|---|---|
| `InitializeTheme` | `void InitializeTheme()` |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` |
| `GetStaticThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticThemeCache()` |
| `GetActiveThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetActiveThemeCache()` |

**Notes:**
- `InitializeTheme()` must be called after `InitializeComponent()` (WPF/Avalonia) to register the instance; both demos do this in `LoadTheme()`.
- `SetThemeValue<T>` / `RestoreThemeValue<T>` manage runtime overrides: the WPF demo calls `SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" })` and `RestoreThemeValue<Light>(nameof(Foreground))`, then inspects `GetStaticThemeCache()` and `GetActiveThemeCache()`.
- The cache shape is `propertyName → PropertyInfo → themeType → value`.

---

### Interface: `IThemeValueConverter`

`public interface IThemeValueConverter`

Strategy that adapts raw theme parameters to a platform value.

Source: `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeValueConverter.cs`.

| Member | Signature |
|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` |

**Notes:**
- Platform adapters ship implementations — `BrushConverter`, `ColorConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ThicknessConverter`, `ObjectConverter` (all in namespace `VeloxDev.DynamicTheme`, in the adapter assemblies) — see [04 PlatformAdapters](../04_PlatformAdapters/index.md).
- `ThemeCache` also exposes a converter registry (`RegisterConverter` / `GetConverter`) for scenarios that want to share a single converter instance across types.
