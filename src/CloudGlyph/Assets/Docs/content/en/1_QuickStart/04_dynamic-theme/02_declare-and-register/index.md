# Dynamic Theme — Declare & Register

## 1. Choose theme types

A theme is any class implementing the marker interface `ITheme`. Two are built in and cover the usual Light/Dark split (`Src/Core/VeloxDev.Core/DynamicTheme/Light.cs`, `Dark.cs`):

```csharp
using VeloxDev.DynamicTheme;

public class Dark : ITheme { }
public class Light : ITheme { }
```

A theme is identified by its `Type` — there is no global registration step for it. It becomes the identity used in the `[ThemeConfig]` generic arguments and in the `ThemeManager` switching calls. Add your own themes by implementing `ITheme`:

```csharp
public class Solarized : ITheme { }
```

## 2. Map properties with [ThemeConfig]

Decorate the **partial** class that owns the properties. Each `[ThemeConfig<TConverter, TTheme1, ...>]` maps **one property** to **one value per theme**. The generic arguments are the converter first, then the theme types; the constructor takes the property name followed by one `object?[]` context array per theme, in the same order:

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow : Window { }
```

The converter type must implement `IThemeValueConverter` (`object? Convert(Type targetType, string propertyName, object?[] parameters)`); it builds the concrete property value from its context array — `BrushConverter` turns `["#ffffff"]` into a `SolidColorBrush`. When `InitializeTheme()` runs, the generator-emitted code instantiates the converter and calls `Convert(propertyType, propertyName, context)` once per theme, storing the results in the shared `ThemeCache`.

The attribute supports **one converter plus 2–7 themes** (6 generic arities in `ThemeConfigAttribute.cs`). A three-theme mapping uses a third theme type and a third context array:

```csharp
[ThemeConfig<BrushConverter, Light, Dark, Solarized>(
    nameof(Background), ["#ffffff"], ["#1e1e1e"], ["#002b36"])]
```

The platform adapters (`VeloxDev.WPF`, `VeloxDev.Avalonia`) each ship these converter types under `VeloxDev.DynamicTheme`: `BrushConverter`, `ColorConverter`, `ThicknessConverter`, `DoubleConverter`, `PointConverter`, `CornerRadiusConverter`, `ObjectConverter`. `ObjectConverter` is the generic fallback used when the target value cannot be expressed by a dedicated converter (the Avalonia demo maps its brushes with it).

**Expected result:** the class type-checks; the generator emits no diagnostic for the attributes.

## 3. Register the instance

Keep the class `partial` so the generator can append the `IThemeObject` implementation. The generated `InitializeTheme()`:

- registers the class's property configuration in the shared `ThemeCache` once per type (lazy; duplicates are ignored),
- calls `ThemeManager.Register(this)` so future theme switches reach this instance,
- applies the current theme's values to the mapped properties immediately.

Call it once the element is usable — after `InitializeComponent()` for a XAML window, or once the object is fully constructed otherwise:

```csharp
public MainWindow()
{
    InitializeComponent();
    LoadTheme();
}

private void LoadTheme()
{
    InitializeTheme(); // generated; must run after InitializeComponent()
}
```

Instances are tracked with weak references, so a collected object stops receiving switches automatically. To stop tracking an object explicitly, use `ThemeManager.Unregister(target)`; `Register`/`Unregister` both take the `IThemeObject` instance.

**Expected result:** after `InitializeTheme()`, `ThemeManager.Current == typeof(Dark)` by default and the mapped properties already hold the `Dark` values (pinned by `ThemeBasicsTests.ThemeManager_DefaultCurrent_IsDark`).
