# 平台转换器

`ThemeConfigAttribute<TConverter, …>` 指定一个转换器类；生成器为每个配置属性实例化它一次，并按主题保存转换结果。转换器位于 `VeloxDev.DynamicTheme`，实现 `IThemeValueConverter`。每个转换器接收特性中声明的 `object?[] parameters` 数组。

## WPF 转换器集

这七个类与 Avalonia、WinUI、MAUI 适配器共用（各自使用其框架类型）。

### 类：DoubleConverter

转换一个数值。

| 接受的 `parameters[0]` | 结果 |
|---|---|
| `double` | 原样 |
| `int` | `(double)` |
| `float` | `(double)` |
| 数字字符串（不变文化） | 解析为 `double` |

### 类：PointConverter

| 接受形式 | 结果 |
|---|---|
| `"x,y"` | `Point(x, y)` |
| 两个数值分量 | `Point(x, y)` |

### 类：ThicknessConverter

| 接受形式 | 结果 |
|---|---|
| 一个分量 | 均匀 `Thickness` |
| `"h,v"` 或两个分量 | 水平/垂直对称 `Thickness` |
| `"l,t,r,b"` 或四个分量 | 四边 `Thickness` |

### 类：CornerRadiusConverter

| 接受形式 | 结果 |
|---|---|
| 一个分量 | 均匀 `CornerRadius` |
| 四个分量（或 `"tl,tr,br,bl"`） | 四角 `CornerRadius` |

### 类：ColorConverter

| 接受形式 | 结果 |
|---|---|
| 颜色名或十六进制字符串 | 经 WPF `BrushConverter` 得到的 `SolidColorBrush.Color` |
| `int` ARGB | `Color.FromArgb(a, r, g, b)` |
| 三个或四个字节分量 | `Color.FromArgb(a?, r, g, b)`；alpha 默认 255 |

### 类：BrushConverter

| 接受形式 | 结果 |
|---|---|
| `Brush` 实例 | 原样 |
| 解析为 `Brush` 的资源键 | 该画刷 |
| 颜色名或十六进制字符串 | `System.Windows.Media.BrushConverter` 的结果 |
| 颜色分量 | 包裹 `ColorConverter` 结果的 `SolidColorBrush` |

### 类：ObjectConverter

通用回退。要求恰好一个 `string` 参数；先尝试资源查找，再走固定转换表：`string`、`bool`、`double`、`float`、`decimal`、`int`、`long`、`TimeSpan`、`Color`、`Thickness`、`CornerRadius`、`GridLength`、`Point`、`Size`、`Rect`、`Duration`、`FontWeight`、`FontStyle`、`FontStretch`、`FontFamily` 以及任意枚举。表外目标类型返回 `null`。

该表是刻意的：`TypeDescriptor.GetConverter(Type)` 带有 `RequiresUnreferencedCode`，会让整条主题路径在裁剪 / AOT 下不可用。需要其他类型的宿主应自写 `IThemeValueConverter`——`ThicknessConverter` 与 `PointConverter` 就是模板。

## 各适配器可用性

下列类均为公开，位于 `VeloxDev.DynamicTheme`。

| 适配器 | 转换器类 |
|---|---|
| WPF | `BrushConverter`、`ColorConverter`、`CornerRadiusConverter`、`DoubleConverter`、`ObjectConverter`、`PointConverter`、`ThicknessConverter` |
| Avalonia | `BrushConverter`、`ColorConverter`、`CornerRadiusConverter`、`DoubleConverter`、`ObjectConverter`、`PointConverter`、`ThicknessConverter` |
| WinUI | `BrushConverter`、`ColorConverter`、`CornerRadiusConverter`、`DoubleConverter`、`ObjectConverter`、`PointConverter`、`ThicknessConverter` |
| MAUI | `BrushConverter`、`ColorConverter`、`CornerRadiusConverter`、`DoubleConverter`、`ObjectConverter`、`PointConverter`、`ThicknessConverter` |
| WinForms | `ColorConverter`、`DoubleConverter`、`FloatConverter`、`FontConverter`、`IntConverter`、`ObjectConverter`、`PaddingConverter`、`PointConverter`、`PointFConverter`、`RectangleConverter`、`RectangleFConverter`、`SizeConverter`、`SizeFConverter` |
| Razor | `BoolConverter`、`DoubleConverter`、`IntConverter`、`StringConverter` |
| Jalium | 未声明；请自写 `IThemeValueConverter` |

## 编写转换器

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

然后在特性中命名它：`[ThemeConfig<GridLengthConverter, Light, Dark>(nameof(ColumnWidth), ["240"], ["120"])]`。

## 说明

- 转换器在 `InitializeTheme` 注册类型时运行，而不是每次切换。注册后改变转换器行为不会更新已存值。
- 返回 `null` 会为该主题跳过该属性；切换期间属性保持原值。
- 特性的上下文数组原样成为转换器的 `parameters` 数组；生成器不解释它们。
