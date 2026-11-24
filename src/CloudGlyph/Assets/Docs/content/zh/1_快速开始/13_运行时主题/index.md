# 运行时主题

给一个 WPF 窗口准备两套主题值，用动画过渡在它们之间切换，并通过生成的回调观察切换。主题值由平台转换器一次性构造；切换过程只对已有值采样。

## 1. 前置条件

- **WPF 适配器支持的目标框架**：`netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows`；本示例使用 `net8.0-windows`。带动画的切换还需要同一适配器的过渡系统。
- **`VeloxDev.WPF`**（会引入 `VeloxDev.Core`）与 **`VeloxDev.Core.Generator`**。生成器是分析器（NuGet 引用 Core 会带上它；`ProjectReference` 不会），不是运行时依赖。示例显式安装生成器包，是为了构建期 Roslyn 检查。
- Windows 上 .NET SDK 8.0 或更高，并安装 Windows Desktop 工作负载。无需任何服务。

## 2. 安装/引入依赖

```text
dotnet new console -n ThemeQuickStart
cd ThemeQuickStart
dotnet add package VeloxDev.WPF --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

```xml
<PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
</PropertyGroup>
```

**预期结果：** 两个包都还原成功。首次构建后即可使用生成的 `InitializeTheme`、`SetThemeValue`、`RestoreThemeValue` 与两个分部回调；设置 `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` 可把 `*_ThemeConfig.g.cs` 写到 `obj/` 下。

## 3. 基础配置/注册

`[ThemeConfig]` 用在持有主题属性的类上。每个特性指定一个属性、一个转换器与二到七个主题类型，并按主题各给一个值数组。`Light` 与 `Dark` 已随 `VeloxDev.DynamicTheme` 提供并实现 `ITheme`，可直接使用；自定义主题就是一个空的 `public sealed class Ocean : ITheme { }`。

```csharp
using System;
using System.Windows;
using VeloxDev.DynamicTheme;

[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class ThemedWindow : Window
{
    public ThemedWindow()
    {
        InitializeTheme();   // 必需，且要在任何 InitializeComponent() 之后
    }

    partial void OnThemeChanged(Type? oldValue, Type? newValue)
        => Console.WriteLine($"theme: {oldValue?.Name} -> {newValue?.Name}");
}
```

`BrushConverter` 是 WPF 适配器的 `IThemeValueConverter`，把 `"#ffffff"` 转成 `SolidColorBrush`。生成的 `InitializeTheme()` 注册当前实例并应用当前主题的值。

**预期结果：** 构造 `ThemedWindow` 后，它的 `Background` 与 `Foreground` 与 `ThemeManager.Current` 一致，后者默认为 `Dark`。

## 4. 核心用法（逐步构建）

### 4.1 选择平台插值器

`ThemeManager` 位于 Core，无法指名 WPF 的采样器集合。只需提供一次适配器的 `Interpolator`。缺少它时切换仍会到达终值，但会瞬切而不是动画。

```csharp
using VeloxDev.TransitionSystem;

ThemeManager.SetPlatformInterpolator(new Interpolator());
ThemeManager.StartModel = StartModel.Cache;   // 从缓存的主题值出发，而不是控件当前值
```

**预期结果：** 调用返回；之后的 `Transition<T>` 会产生帧。`StartModel.Cache` 同时也是默认值。

### 4.2 动画切换与瞬切

`Transition<T>(effect)` 通过效果对每个已注册目标采样。`Jump<T>()` 立即写入所有终值，不需要插值器。

```csharp
if (ThemeManager.Current == typeof(Dark))
{
    ThemeManager.Transition<Light>(TransitionEffects.Theme);   // 0.46 秒动画切换
}
else
{
    ThemeManager.Jump<Dark>();                                 // 立即切换
}
```

`TransitionEffects.Theme` 是共享的 WPF 效果（`Duration = 0.46 s`）。它每帧都会被读取，因此切换运行期间不要修改它。`TransitionEffects.Hover`（0.32 秒）是悬停默认值；`Empty` 时长为零。

**预期结果：** 动画调用把 `Background` 与 `Foreground` 渐变到目标值，落定后才触发 `OnThemeChanged`；瞬切调用一步写入并立即触发回调。

### 4.3 每次切换共用一条时间轴

一次切换中的所有目标锚定在同一条时间轴上。因此对任一目标调用 `Transition.Pause`、`Resume` 或 `SetRate` 都会移动整场切换；`Seek` 只重锚该目标的运行，`Exit` 只取消该目标的运行。

```csharp
Transition.Pause(window, IncludeMutual: true, IncludeNoMutual: true);
Transition.Resume(window, IncludeMutual: true, IncludeNoMutual: true);
```

**预期结果：** 主题渐变途中暂停，所有主题对象会停在同一进度；恢复后一起继续。

### 4.4 单实例覆盖

生成的 `SetThemeValue<T>` 为某个实例、某个主题写入覆盖值；`RestoreThemeValue<T>` 删除覆盖并重新应用声明值。`GetStaticThemeCache()` 与 `GetActiveThemeCache()` 分别暴露声明表与覆盖表。

```csharp
window.SetThemeValue<Light>(nameof(Background), Brushes.White);
window.RestoreThemeValue<Light>(nameof(Background));
```

**预期结果：** 当 `Light` 为当前主题时覆盖值生效；还原后该属性回到 `#ffffff`。

### 4.5 回调与生命周期

`OnThemeChanging` 在切换开始前运行，`OnThemeChanged` 在切换落定后运行。注册是弱引用：`ThemeManager` 持有 `WeakReference<IThemeObject>`，不再被引用的对象会在下一次切换时被清除。只有新实例才需要再次调用 `InitializeTheme()`。

**预期结果：** 已关闭的窗口不会被主题管理器保活，下一次切换会跳过它。

## 5. 验证

运行完整程序。窗口以深色打开；每两秒渐变到另一套主题。控制台每完成一次切换打印一行 `theme: Dark -> Light` 或 `theme: Light -> Dark`。无需点击，定时器同时演示 `Transition<T>` 与共享时间轴。

## 6. 完整代码

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Threading;
using VeloxDev.DynamicTheme;
using VeloxDev.TransitionSystem;

[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class ThemedWindow : Window
{
    public ThemedWindow()
    {
        InitializeTheme();
        ThemeManager.SetPlatformInterpolator(new Interpolator());
        ThemeManager.StartModel = StartModel.Cache;
    }

    partial void OnThemeChanged(Type? oldValue, Type? newValue)
        => Console.WriteLine($"theme: {oldValue?.Name} -> {newValue?.Name}");
}

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        var app = new Application();

        app.Startup += (_, _) =>
        {
            var window = new ThemedWindow
            {
                Title = "Theme quick start",
                Width = 420,
                Height = 240
            };

            var text = new TextBlock { Text = "Theme Manager", FontSize = 48 };
            text.SetBinding(TextBlock.ForegroundProperty,
                new Binding(nameof(Window.Foreground)) { Source = window });
            window.Content = text;

            var timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(2) };
            timer.Tick += (_, _) =>
            {
                if (ThemeManager.Current == typeof(Dark))
                {
                    ThemeManager.Transition<Light>(TransitionEffects.Theme);
                }
                else
                {
                    ThemeManager.Transition<Dark>(TransitionEffects.Theme);
                }
            };

            window.Show();
            timer.Start();
        };

        app.Run();
    }
}
```

声明模式与 `Transition`/`Jump` 组合取自 `Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`；`Examples/Theme/WPF/Demo/MainWindow.xaml.cs` 的方块演示补上了共享时间轴控制面。

## 7. 运行声明

- ⚠️ 未实际运行——仅于 2026-11-25 静态核验。已对照 `Src/Core/VeloxDev.Core/DynamicTheme/ThemeConfigAttribute.cs`、`ThemeManager.cs`、`Src/Generators/VeloxDev.Core.Generator/Theme.cs`、`Src/Adapters/VeloxDev.WPF/TransitionSystem/TransitionEffects.cs`、`Src/Adapters/VeloxDev.WPF/DynamicTheme/ThemeValueConverters.cs` 以及两个 WPF 主题 demo 核验。本环境未启动窗口。
