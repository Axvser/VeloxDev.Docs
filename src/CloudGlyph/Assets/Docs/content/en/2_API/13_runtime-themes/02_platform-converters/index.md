# Platform Converters

A `ThemeConfigAttribute<TConverter, …>` names one converter class; the generator instantiates it once per configured property and stores the converted value for each theme. Converters live in `VeloxDev.DynamicTheme` and implement `IThemeValueConverter`. Each accepts the `object?[] parameters` array declared in the attribute.

## WPF converter set

These seven classes are shared with the Avalonia, WinUI and MAUI adapters (each uses its own framework's types).

### Class: DoubleConverter

Converts one numeric value.

| Accepted `parameters[0]` | Result |
|---|---|
| `double` | as-is |
| `int` | `(double)` |
| `float` | `(double)` |
| numeric `string` (invariant culture) | parsed `double` |

### Class: PointConverter

| Accepted form | Result |
|---|---|
| `"x,y"` | `Point(x, y)` |
| two numeric components | `Point(x, y)` |

### Class: ThicknessConverter

| Accepted form | Result |
|---|---|
| one component | uniform `Thickness` |
| `"h,v"` or two components | horizontal/vertical symmetric `Thickness` |
| `"l,t,r,b"` or four components | four-sided `Thickness` |

### Class: CornerRadiusConverter

| Accepted form | Result |
|---|---|
| one component | uniform `CornerRadius` |
| four components (or `"tl,tr,br,bl"`) | four-corner `CornerRadius` |

### Class: ColorConverter

| Accepted form | Result |
|---|---|
| color name or hex string | `SolidColorBrush.Color` from WPF's `BrushConverter` |
| `int` ARGB | `Color.FromArgb(a, r, g, b)` |
| three or four byte components | `Color.FromArgb(a?, r, g, b)`; alpha defaults to 255 |

### Class: BrushConverter

| Accepted form | Result |
|---|---|
| `Brush` instance | as-is |
| resource key resolving to a `Brush` | that brush |
| color name or hex string | `System.Windows.Media.BrushConverter` result |
| color components | `SolidColorBrush` around `ColorConverter`'s result |

### Class: ObjectConverter

The general fallback. Requires exactly one `string` parameter; tries a resource lookup first, then a fixed conversion table: `string`, `bool`, `double`, `float`, `decimal`, `int`, `long`, `TimeSpan`, `Color`, `Thickness`, `CornerRadius`, `GridLength`, `Point`, `Size`, `Rect`, `Duration`, `FontWeight`, `FontStyle`, `FontStretch`, `FontFamily`, and any enum. A target type outside the table returns `null`.

The table is deliberate: `TypeDescriptor.GetConverter(Type)` carries `RequiresUnreferencedCode`, which would make the whole theme path unavailable under trimming / AOT. A host needing another type writes its own `IThemeValueConverter` — `ThicknessConverter` and `PointConverter` are the templates.

## Per-adapter availability

All classes below are public and in `VeloxDev.DynamicTheme`.

| Adapter | Converter classes |
|---|---|
| WPF | `BrushConverter`, `ColorConverter`, `CornerRadiusConverter`, `DoubleConverter`, `ObjectConverter`, `PointConverter`, `ThicknessConverter` |
| Avalonia | `BrushConverter`, `ColorConverter`, `CornerRadiusConverter`, `DoubleConverter`, `ObjectConverter`, `PointConverter`, `ThicknessConverter` |
| WinUI | `BrushConverter`, `ColorConverter`, `CornerRadiusConverter`, `DoubleConverter`, `ObjectConverter`, `PointConverter`, `ThicknessConverter` |
| MAUI | `BrushConverter`, `ColorConverter`, `CornerRadiusConverter`, `DoubleConverter`, `ObjectConverter`, `PointConverter`, `ThicknessConverter` |
| WinForms | `ColorConverter`, `DoubleConverter`, `FloatConverter`, `FontConverter`, `IntConverter`, `ObjectConverter`, `PaddingConverter`, `PointConverter`, `PointFConverter`, `RectangleConverter`, `RectangleFConverter`, `SizeConverter`, `SizeFConverter` |
| Razor | `BoolConverter`, `DoubleConverter`, `IntConverter`, `StringConverter` |
| Jalium | none declared; supply your own `IThemeValueConverter` |

## Writing a converter

```csharp
using System;
using System.Windows;
using VeloxDev.DynamicTheme;

public sealed class GridLengthConverter : IThemeValueConverter
{
    public object? Convert(Type targetType, string propertyName, object?[] parameters)
    {
        if (parameters is not { Length: 1 } || parameters[0] is not string text)
            return null;

        return double.TryParse(text, out var value) ? new GridLength(value) : null;
    }
}
```

Then name it in the attribute: `[ThemeConfig<GridLengthConverter, Light, Dark>(nameof(ColumnWidth), ["240"], ["120"])]`.

## Notes

- A converter runs while `InitializeTheme` registers the type, not on every switch. Changing the converter's behavior after registration does not update stored values.
- Returning `null` skips that property for that theme; the property keeps its previous value during the switch.
- The attribute's context arrays become the converter's `parameters` array unchanged; the generator does not interpret them.
