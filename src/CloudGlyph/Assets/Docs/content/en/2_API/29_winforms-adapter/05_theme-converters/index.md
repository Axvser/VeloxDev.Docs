# Theme converters

Namespace: `VeloxDev.DynamicTheme`.

Each type implements `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)` and returns a `System.Drawing` or WinForms value, or `null` when the parameters cannot be converted.

| Converter | Output | Accepted parameters |
| --- | --- | --- |
| `DoubleConverter` | `double` | `double`, `int`, `float`, invariant numeric string. |
| `IntConverter` | `int` | `int`, `double`, `float`, invariant numeric string. |
| `FloatConverter` | `float` | `float`, `double`, `int`, invariant numeric string. |
| `PointConverter` | `System.Drawing.Point` | `"x,y"`, or the pair `[x, y]`. |
| `PointFConverter` | `System.Drawing.PointF` | `"x,y"`, or the pair `[x, y]`. |
| `SizeConverter` | `System.Drawing.Size` | `"width,height"`, or the pair `[width, height]`. |
| `SizeFConverter` | `System.Drawing.SizeF` | `"width,height"`, or the pair `[width, height]`. |
| `RectangleConverter` | `System.Drawing.Rectangle` | `"x,y,width,height"`, or the four-value list. |
| `RectangleFConverter` | `System.Drawing.RectangleF` | `"x,y,width,height"`, or the four-value list. |
| `PaddingConverter` | `System.Windows.Forms.Padding` | One, two or four values, comma-separated or as separate arguments. |
| `ColorConverter` | `System.Drawing.Color` | Name or hex string, ARGB `int`, or 3/4 byte components. |
| `FontConverter` | `System.Drawing.Font` | `"family,size[,style]"`, a system-font name, or `[family, size, style]`. |
| `ObjectConverter` | Target-dependent | One string; converts `Brush`, `Color`, `Font`, `string`, `bool`, `double`, `float`, `decimal`, `int`, `long`, `TimeSpan`, `Point`, `Size`, `SizeF`, `Rectangle`, `Padding` and enums. |

### Notes

- `ColorConverter` accepts the eight known system-font keys (`CaptionFont`, `DefaultFont`, `DialogFont`, …).
- `ObjectConverter` deliberately does not use `TypeDescriptor.GetConverter(Type)`: that API is marked `RequiresUnreferencedCode`. Unlisted target types return `null`; add a dedicated converter instead.
- Every converter returns `null` instead of throwing when parsing fails.

### Example

```csharp
var converter = new ObjectConverter();
var brush = converter.Convert(typeof(SolidBrush), "Background", ["#FF1E1E1E"]);
// Source: source
```
