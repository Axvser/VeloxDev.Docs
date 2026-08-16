# API — Dynamic Theme · ThemeConfigAttribute and Contracts

## Namespace: `VeloxDev.DynamicTheme`

### Attribute: `ThemeConfigAttribute<TConverter, TTheme1, ...>`

Six generic arities, each decorating a class to map one property to one value per theme. The source generator `VeloxDev.Generators.Theme` reads these attributes and emits an `IThemeObject` implementation on the decorated class.

Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeConfigAttribute.cs`.

| Arities | Generic parameters | Constraint |
|---|---|---|
| 2 themes | `<TConverter, TTheme1, TTheme2>` | `TConverter : class, IThemeValueConverter`; `TTheme1, TTheme2 : ITheme` |
| 3 themes | `<TConverter, TTheme1, TTheme2, TTheme3>` | `TConverter : class, IThemeValueConverter`; each `TThemeN : ITheme` |
| 4 themes | `<TConverter, TTheme1..TTheme4>` | `TConverter : class, IThemeValueConverter`; each `TThemeN : ITheme` |
| 5 themes | `<TConverter, TTheme1..TTheme5>` | `TConverter : class, IThemeValueConverter`; each `TThemeN : ITheme` |
| 6 themes | `<TConverter, TTheme1..TTheme6>` | `TConverter : class, IThemeValueConverter`; each `TThemeN : ITheme` |
| 7 themes | `<TConverter, TTheme1..TTheme7>` | `TConverter : class, IThemeValueConverter`; each `TThemeN : ITheme` |

**Constructors** (one per arity):

`public ThemeConfigAttribute(string propertyName, object?[] themeContext1, object?[] themeContext2, ..., object?[] themeContextN)`

| Parameter | Type | Description |
|---|---|---|
| `propertyName` | `string` | Target property name (e.g. `nameof(Background)`). |
| `themeContextN` | `object?[]` | Value parameters for the Nth theme, in the order of the generic theme arguments. |

**Attribute metadata:** `[AttributeUsage(AttributeTargets.Class, AllowMultiple = true, Inherited = false)]`.

**Example:**
```text
// Source: Demo (Examples/Theme/WPF/Demo/MainWindow.xaml.cs)
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
```

**Notes:**
- `TConverter` is the strategy that turns the raw `object?[]` parameters into the property's platform type (e.g. `BrushConverter` → `Brush`).
- A minimum of two themes is required; up to seven themes are supported per attribute.

---

### Interface: `ITheme`

`public interface ITheme`

Empty marker interface for theme types. Implemented by `Dark`, `Light`, and any custom theme type.

Source: `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/ITheme.cs`.

---

### Interface: `IThemeObject`

Implemented (via the source generator) on any class decorated with `[ThemeConfig]`. The generator also produces `partial void OnThemeChanging(Type? oldValue, Type? newValue)` / `partial void OnThemeChanged(Type? oldValue, Type? newValue)` hooks.

Source: `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeObject.cs`.

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
- `InitializeTheme()` must be called after `InitializeComponent()` (WPF/Avalonia) to register the instance.
- `SetThemeValue<T>` / `RestoreThemeValue<T>` are runtime value overrides; `SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" })` appears in the WPF demo.
- The cache structure is `propertyName → PropertyInfo → themeType → value`.

---

### Interface: `IThemeValueConverter`

`public interface IThemeValueConverter`

Strategy that adapts raw theme parameters to a platform type.

Source: `Src/Core/VeloxDev.Core/Interfaces/DynamicTheme/IThemeValueConverter.cs`.

| Member | Signature |
|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` |

**Notes:**
- Platform adapters ship implementations: `BrushConverter`, `ColorConverter`, `ThicknessConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ObjectConverter` (all in namespace `VeloxDev.DynamicTheme`).
- The `ThemeCache` converter registry allows converters to be registered once and reused across types (`RegisterConverter` / `GetConverter`).
