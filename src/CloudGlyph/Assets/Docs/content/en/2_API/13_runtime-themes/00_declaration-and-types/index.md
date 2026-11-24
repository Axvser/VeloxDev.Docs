# Declaration and Types

The attribute that declares a themed property, the interfaces the generator targets, the two built-in themes, the global cache, and the members the generator emits.

## VeloxDev.DynamicTheme

### Class: ThemeConfigAttribute<TConverter, TTheme1, TTheme2 … TTheme7>

Declares one property's value in each of two to seven themes. There are six generic arities (`TTheme1`–`TTheme2` through `TTheme1`–`TTheme7`).

**Signature (two-theme form):**
`public class ThemeConfigAttribute<TConverter, TTheme1, TTheme2> : Attribute where TConverter : class, IThemeValueConverter where TTheme1 : ITheme where TTheme2 : ITheme`

**Constructor:** `ThemeConfigAttribute(string propertyName, object?[] themeContext1, object?[] themeContext2)` — one value array per theme, in declaration order.

The three-, four-, five-, six- and seven-theme forms add one `object?[] themeContextN` per extra theme.

**Attribute usage:** `AttributeTargets.Class`, `AllowMultiple = true`, `Inherited = false`. Apply it to the partial class that declares (or inherits) the property.

Each context array is passed to the converter as its `parameters` argument. A converter may interpret one string, several components or a type token; see [Platform converters](../02_platform-converters/index.md).

### Interface: ITheme

A marker for one theme definition. A custom theme is an empty class.

**Signature:** `public interface ITheme`

### Interface: IThemeObject

The contract the generator implements on a themed class.

**Signature:** `public interface IThemeObject`

| Member | Signature | Description |
|---|---|---|
| `InitializeTheme` | `void InitializeTheme()` | Registers the type's configuration and applies the current theme's values. Must run after `InitializeComponent()` when there is one. |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` | Runs the changing hooks as a switch begins. |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` | Runs the changed hooks after a switch lands. |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` | Writes a per-instance override for one property and one theme. |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` | Removes the override and re-applies the declared value. |
| `GetStaticThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticThemeCache()` | The declared values, per property and theme. |
| `GetActiveThemeCache` | `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetActiveThemeCache()` | The per-instance overrides. |

### Interface: IThemeValueConverter

**Signature:** `public interface IThemeValueConverter`

| Member | Signature | Description |
|---|---|---|
| `Convert` | `object? Convert(Type targetType, string propertyName, object?[] parameters)` | Converts a stored value for the property; `null` means it cannot be converted and the property is skipped. |

### Class: Light / Dark

The two built-in themes, both implementing `ITheme`.

**Signatures:** `public class Light : ITheme`, `public class Dark : ITheme`

`ThemeManager.Current` defaults to `typeof(Dark)`.

### Class: ThemeCache

The process-wide store: a static per-type table of declared values and a weak per-instance table of overrides.

**Signature:** `public static class ThemeCache`

| Member | Signature | Description |
|---|---|---|
| `InstanceCache` | `public sealed class InstanceCache` | Holds `Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> Overrides { get; set; }`. |
| `IsTypeRegistered` | `static bool IsTypeRegistered(Type type)` | Whether the type's declared configuration is registered. |
| `RegisterType` | `static void RegisterType(Type type, Dictionary<string, (PropertyInfo Property, Dictionary<Type, object?> Values)> properties)` | Registers the declared values; a duplicate registration is ignored. Thread-safe. |
| `GetStaticForType` | `static Dictionary<string, Dictionary<PropertyInfo, Dictionary<Type, object?>>> GetStaticForType(Type type)` | Merged declared values, walking the inheritance chain base-first so derived entries win. |
| `GetOrCreateActiveEntry` | `static InstanceCache GetOrCreateActiveEntry(IThemeObject instance)` | The instance's override entry, created on first use. |
| `TryGetActiveEntry` | `static InstanceCache? TryGetActiveEntry(IThemeObject instance)` | The override entry, or `null`. |
| `TryGetDefaultValue` | `static bool TryGetDefaultValue(Type type, string propertyName, Type themeType, out object? value)` | Looks up a declared value, walking base types. |

The instance table is a `ConditionalWeakTable`, so a theme object is never kept alive by the cache.

## Generated members

For a partial class with one or more `[ThemeConfig<…>]` attributes, the generator emits (file `{Class}_{Namespace}_ThemeConfig.g.cs`):

| Member | Signature | Notes |
|---|---|---|
| `InitializeTheme` | `(virtual/override) void InitializeTheme()` | Registers the type once, registers the instance with `ThemeManager`, applies the current theme. `override` when a base type already implements `IThemeObject` and carries `[ThemeConfig]`. |
| `ExecuteThemeChanging` | `void ExecuteThemeChanging(Type? oldValue, Type? newValue)` | Calls the base implementation when there is one, then `OnThemeChanging`. |
| `ExecuteThemeChanged` | `void ExecuteThemeChanged(Type? oldValue, Type? newValue)` | Calls the base implementation when there is one, then `OnThemeChanged`. |
| `OnThemeChanging` | `partial void OnThemeChanging(Type? oldValue, Type? newValue)` | Implementation optional. |
| `OnThemeChanged` | `partial void OnThemeChanged(Type? oldValue, Type? newValue)` | Implementation optional. |
| `SetThemeValue<T>` | `void SetThemeValue<T>(string propertyName, object? newValue) where T : ITheme` | Writes an override and re-applies the property if `T` is current. |
| `RestoreThemeValue<T>` | `void RestoreThemeValue<T>(string propertyName) where T : ITheme` | Removes the override and re-applies the property. |
| `GetStaticThemeCache` | `Dictionary<…> GetStaticThemeCache()` | Returns `ThemeCache.GetStaticForType(GetType())`. |
| `GetActiveThemeCache` | `Dictionary<…> GetActiveThemeCache()` | Returns the instance override map. |
| `UpdatePropertyToCurrentTheme` | `void UpdatePropertyToCurrentTheme(string propertyName)` | Re-applies one property from the override or declared value. |
| `UpdateAllPropertiesToCurrentTheme` | `void UpdateAllPropertiesToCurrentTheme()` | Re-applies every declared property. |

The generated class also implements `IThemeObject` when no base type already does.

## Example

```csharp
using System;
using System.Windows;
using VeloxDev.DynamicTheme;

[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class ThemedWindow : Window
{
    public ThemedWindow() => InitializeTheme();

    partial void OnThemeChanged(Type? oldValue, Type? newValue)
        => Console.WriteLine($"{oldValue?.Name} -> {newValue?.Name}");
}
```

`BrushConverter` is the WPF adapter's converter; see [Platform converters](../02_platform-converters/index.md). The complete runnable window is in the [quick start](../../../1_QuickStart/13_runtime-themes/index.md).
