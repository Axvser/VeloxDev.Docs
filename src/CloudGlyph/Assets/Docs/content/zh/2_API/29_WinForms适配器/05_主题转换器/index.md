# 主题转换器

命名空间：`VeloxDev.DynamicTheme`。

每个类型实现 `IThemeValueConverter.Convert(Type targetType, string propertyName, object?[] parameters)`，返回 `System.Drawing` 或 WinForms 值；参数无法转换时返回 `null`。

| 转换器 | 输出 | 接受的参数 |
| --- | --- | --- |
| `DoubleConverter` | `double` | `double`、`int`、`float`、不变文化数字字符串。 |
| `IntConverter` | `int` | `int`、`double`、`float`、不变文化数字字符串。 |
| `FloatConverter` | `float` | `float`、`double`、`int`、不变文化数字字符串。 |
| `PointConverter` | `System.Drawing.Point` | `"x,y"`，或 `[x, y]`。 |
| `PointFConverter` | `System.Drawing.PointF` | `"x,y"`，或 `[x, y]`。 |
| `SizeConverter` | `System.Drawing.Size` | `"width,height"`，或 `[width, height]`。 |
| `SizeFConverter` | `System.Drawing.SizeF` | `"width,height"`，或 `[width, height]`。 |
| `RectangleConverter` | `System.Drawing.Rectangle` | `"x,y,width,height"`，或四值列表。 |
| `RectangleFConverter` | `System.Drawing.RectangleF` | `"x,y,width,height"`，或四值列表。 |
| `PaddingConverter` | `System.Windows.Forms.Padding` | 一个、两个或四个值，逗号分隔或作为独立参数。 |
| `ColorConverter` | `System.Drawing.Color` | 颜色名或十六进制字符串、ARGB `int`，或 3/4 个字节分量。 |
| `FontConverter` | `System.Drawing.Font` | `"family,size[,style]"`、系统字体名，或 `[family, size, style]`。 |
| `ObjectConverter` | 取决于目标类型 | 一个字符串；可转换 `Brush`、`Color`、`Font`、`string`、`bool`、`double`、`float`、`decimal`、`int`、`long`、`TimeSpan`、`Point`、`Size`、`SizeF`、`Rectangle`、`Padding` 与枚举。 |

### 备注

- `ColorConverter` 接受八个已知系统字体键（`CaptionFont`、`DefaultFont`、`DialogFont` 等）。
- `ObjectConverter` 刻意不用 `TypeDescriptor.GetConverter(Type)`：该 API 标了 `RequiresUnreferencedCode`。未列出的目标类型返回 `null`；请为它写一个专用转换器。
- 所有转换器在解析失败时返回 `null`，不抛异常。

### 示例

```csharp
var converter = new ObjectConverter();
var brush = converter.Convert(typeof(SolidBrush), "Background", ["#FF1E1E1E"]);
// Source: source
```
