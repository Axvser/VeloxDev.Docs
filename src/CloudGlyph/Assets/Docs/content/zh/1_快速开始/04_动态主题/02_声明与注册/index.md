# 动态主题 — 声明与注册

## 1. 选择主题类型

主题是任何实现了标记接口 `ITheme` 的类。内置两个主题覆盖常见的亮/暗划分（`Src/Core/VeloxDev.Core/DynamicTheme/Light.cs`、`Dark.cs`）：

```csharp
using VeloxDev.DynamicTheme;

public class Dark : ITheme { }
public class Light : ITheme { }
```

主题以其 `Type` 作为标识——没有「全局注册主题」这一步。它只作为 `[ThemeConfig]` 泛型参数与 `ThemeManager` 切换调用里的身份。自己实现 `ITheme` 即可添加新主题：

```csharp
public class Solarized : ITheme { }
```

## 2. 用 [ThemeConfig] 映射属性

装饰拥有这些属性的 **partial** 类。每个 `[ThemeConfig<TConverter, TTheme1, ...>]` 将**一个属性**映射为「每个主题下一个值」。泛型参数第一个是转换器，随后是各主题类型；构造函数第一参是属性名，其后按顺序为每个主题提供一个 `object?[]` 上下文数组：

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow : Window { }
```

转换器类型必须实现 `IThemeValueConverter`（`object? Convert(Type targetType, string propertyName, object?[] parameters)`）；它由上下文数组构造出具体属性值 —— `BrushConverter` 会把 `["#ffffff"]` 变成 `SolidColorBrush`。当 `InitializeTheme()` 运行时，生成器产出的代码会实例化转换器并对每个主题调用一次 `Convert(propertyType, propertyName, context)`，结果存入共享的 `ThemeCache`。

该特性支持**1 个转换器 + 2–7 个主题**（`ThemeConfigAttribute.cs` 中共 6 个泛型元数）。三主题映射使用第三个主题类型与第三个上下文数组：

```csharp
[ThemeConfig<BrushConverter, Light, Dark, Solarized>(
    nameof(Background), ["#ffffff"], ["#1e1e1e"], ["#002b36"])]
```

平台适配器（`VeloxDev.WPF`、`VeloxDev.Avalonia`）各在 `VeloxDev.DynamicTheme` 命名空间提供这些转换器：`BrushConverter`、`ColorConverter`、`ThicknessConverter`、`DoubleConverter`、`PointConverter`、`CornerRadiusConverter`、`ObjectConverter`。`ObjectConverter` 是通用兜底转换器，用于无法用专用转换器表达目标值的场景（Avalonia 示例用它映射画笔）。

**预期结果：** 类类型检查通过；生成器对这些特性不产生诊断。

## 3. 注册实例

保持类为 `partial`，生成器才能追加 `IThemeObject` 实现。生成的 `InitializeTheme()` 会：

- 将该类的属性配置按类型一次性（惰性）注册进共享的 `ThemeCache`（重复注册会被忽略）；
- 调用 `ThemeManager.Register(this)`，让后续主题切换能到达该实例；
- 立即把当前主题的值应用到已映射属性上。

在元素可用后调用它 —— XAML 窗口在 `InitializeComponent()` 之后，其它对象在完整构造之后：

```csharp
public MainWindow()
{
    InitializeComponent();
    LoadTheme();
}

private void LoadTheme()
{
    InitializeTheme(); // 生成方法；必须晚于 InitializeComponent() 调用
}
```

实例以弱引用跟踪，因此已回收的对象会自动停止接收切换。要显式停止跟踪某对象，用 `ThemeManager.Unregister(target)`；`Register`/`Unregister` 都接收 `IThemeObject` 实例。

由于注册发生在生成的 `InitializeTheme()` 里，一个参与主题的控件只要被构造出来就完成了自注册。规模示例正是靠这一点：`Examples/Theme/WPF/Demo/ThemeTile.cs`（以及 Avalonia 版）是一个 26×26 的 `Border`，映射 `Background` 与 `BorderBrush`，在构造函数中调用 `InitializeTheme()`；除此之外没有任何接线，一千个这样的元素就能一起加入下一次切换。对这些声明值的运行时覆盖见[运行时覆盖与线程](../03_运行时切换/03_运行时覆盖与线程/index.md)。

**预期结果：** `InitializeTheme()` 之后，默认 `ThemeManager.Current == typeof(Dark)`，且已映射属性已持有 `Dark` 主题值（由 `ThemeBasicsTests.ThemeManager_DefaultCurrent_IsDark` 锁定）。
