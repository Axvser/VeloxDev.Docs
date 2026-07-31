# 动态主题 — 快速入门

本指南带你为基于 VeloxDev 的编辑器添加**带动画过渡的运行时主题切换**。你将为一个窗口声明各主题下的属性值，在运行时于 `Light` 与 `Dark` 之间切换（带或不带平滑动画），并可随时覆盖单个主题值。

> 示例源码：`Examples/Theme/WPF/Demo` 与 `Examples/Theme/Avalonia/Demo`

## 1. 安装 / 添加依赖

添加与你的 GUI 框架匹配的适配器包即可。主题转换器与插值器都位于适配器中，因此只需引用一个包：

```bash
# WPF
dotnet add package VeloxDev.WPF

# Avalonia
dotnet add package VeloxDev.Avalonia
```

## 2. 基本设置 / 注册

**第 1 步 — 使用 `[ThemeConfig]` 声明各主题的值。** 每个特性将「一个属性」映射为「每个主题下的一个值」。泛型参数为 `<TConverter, TTheme1, TTheme2, ...>`；属性名之后的字符串数组按顺序对应每个主题的值。

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
{
    // class body ...
}
```

`VeloxDev.Generators.Theme` 源生成器会把这些特性转换为 `IThemeObject` 实现（`InitializeTheme`、`SetThemeValue<T>`、回调等）。

**第 2 步 — 初始化并注册。** 必须在 `InitializeComponent()` **之后**调用 `InitializeTheme()`。如果需要带动画的主题切换，还需安装适配器的插值器，并选择起始模型：

```csharp
private void LoadTheme()
{
    InitializeTheme(); // 必须晚于 InitializeComponent() 调用

    // 仅当需要带动画的主题切换时才需要配置插值器
    ThemeManager.SetPlatformInterpolator(new Interpolator());

    // 动画起始状态：从缓存取（Cache），还是反射读取当前属性值（Reflect）
    ThemeManager.StartModel = StartModel.Cache;
}
```

## 3. 核心用法（逐步）

**带动画切换主题** — 属性值会按效果的时长与缓动曲线逐帧插值：

```csharp
private static void ReverseThemeWithAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    else
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
}
```

**无动画即时切换**：

```csharp
private static void ReverseThemeWithOutAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
        ThemeManager.Jump<Light>();
    else
        ThemeManager.Jump<Dark>();
}
```

**响应主题变化** — 实现生成器生成的 `partial void OnThemeChanged`：

```csharp
partial void OnThemeChanged(Type? oldValue, Type? newValue)
{
    MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
}
```

**运行时覆盖单个主题值**，并可恢复：

```csharp
private void ThemeValueEx()
{
    SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" });
    RestoreThemeValue<Light>(nameof(Foreground));

    var staticCache = GetStaticThemeCache();   // 按类型的默认值
    var dynamicCache = GetActiveThemeCache();  // 运行时覆盖
}
```

## 4. 验证

运行应用并切换主题：

- 使用 `Transition<T>` 时窗口背景/前景会**平滑**变化（`TransitionEffects.Theme` 效果以 60 FPS 运行 0.46 秒）。
- `Jump<T>` 立即切换。
- 每次切换后 `OnThemeChanged` 回调触发并弹出消息框。
- 通过 `SetThemeValue<Light>` 覆盖 `Background` 会立即生效，`RestoreThemeValue` 恢复到主题默认值。

## 5. 完整代码

一个最小的 WPF 示例（`MainWindow.xaml.cs`）：

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
{
    public MainWindow()
    {
        InitializeComponent();
        LoadTheme();
    }

    private void LoadTheme()
    {
        InitializeTheme();
        ThemeManager.SetPlatformInterpolator(new Interpolator());
        ThemeManager.StartModel = StartModel.Cache;
    }

    partial void OnThemeChanged(Type? oldValue, Type? newValue)
    {
        MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
    }

    private void ReverseThemeWithAnimation()
    {
        if (ThemeManager.Current == typeof(Dark))
            ThemeManager.Transition<Light>(TransitionEffects.Theme);
        else
            ThemeManager.Transition<Dark>(TransitionEffects.Theme);
    }

    private void ReverseThemeWithOutAnimation()
    {
        if (ThemeManager.Current == typeof(Dark))
            ThemeManager.Jump<Light>();
        else
            ThemeManager.Jump<Dark>();
    }
}
```

> **提示：** Avalonia 示例结构相同，使用 `ObjectConverter`，主题顺序为 `Dark, Light`。XAML 中通过 `RelativeSource AncestorType=Window`（WPF）或 `RelativeSource AncestorType=views:MainWindow`（Avalonia）绑定主题属性。
