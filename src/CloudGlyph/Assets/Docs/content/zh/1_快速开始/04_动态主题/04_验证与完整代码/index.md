# 动态主题 — 验证与完整代码

## 1. 用最小示例验证

`Examples/Theme/WPF Trimmed/Demo` 与 `Examples/Theme/Avalonia Trimmed/Demo` 是该功能的最小形态：一个窗口、两个参与主题的属性、一个切换按钮。WPF 窗口映射 `Background` 与 `Foreground`，按钮（`Content="反转主题"`、`Click="ChangeTheme"`）调用 `ReverseThemeWithAnimation()`：

```bash
dotnet run --project "Examples/Theme/WPF Trimmed/Demo"
```

点击按钮，在一个窗口里核对本快速入门逐步搭起来的四种行为：

- 窗口的已映射颜色在 `TransitionEffects.Theme`（0.46 秒）内**平滑**插值到另一主题 —— 即 `Transition<Light/Dark>` 路径；
- 把那句调用换成 `Jump<Light/Dark>()`（示例中的 `ReverseThemeWithOutAnimation`）会用同样的颜色**立即**完成切换；
- 每次落地的切换后，生成的 `partial void OnThemeChanged(Type? oldValue, Type? newValue)` 会触发（WPF 示例弹消息框，Avalonia 示例弹窗口通知）；
- `SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" })` 与 `RestoreThemeValue<Light>(...)`（示例中的 `ThemeValueEx`）改变并放回某一个主题下的某个值。

Avalonia 版以同样的方式构建与运行，用 `[ThemeConfig<ObjectConverter, Dark, Light>]`（主题顺序 `Dark, Light`），并通过 `RelativeSource AncestorType=views:MainWindow` 绑定。

**预期结果：** 每次点击窗口都会重新着色 —— `Transition` 平滑、`Jump` 即时 —— 且每次都出现回调。

## 2. 用规模示例验证

`Examples/Theme/WPF/Demo` 与 `Examples/Theme/Avalonia/Demo` 是同一场景放到「共享时间轴变得可见」的规模上：一千个块、时间轴控制工具条，以及一个实时读数（见[控制运行中的切换](../03_运行时切换/02_控制切换/index.md)）。两者也都能无头运行该场景：

```bash
dotnet run --project "Examples/Theme/WPF/Demo" -- bench
```

`BenchRunner` 会以 1、50、200、1000 个元素各重复三次「带动画切换 + `Jump`」，一次让块位于可视化树内、一次在树外，然后把 TSV 表写到 `%TEMP%\veloxdev-theme-scale.tsv`。`prep_ms` 是 `Transition<T>` 调用中的同步部分 —— 切换在产生第一帧之前所做的一切 —— 也是随元素数增长的那部分。`anim_ms` 是其余部分，而它不随元素数增长：一场切换的每个元素都锚定在同一条时间轴上，所以一百个目标和一千个目标用同样的墙钟时间抵达终点。

2026-09-13 实测（WPF，300 毫秒 effect，块位于树内；完整运行覆盖全部四档规模）：

| size | attached | jump_ms | prep_ms | anim_ms | frames | frames_per_target |
|---|---|---|---|---|---|---|
| 1 | True | 0.7 | 0.2 | 329.2 | 14 | 14 |
| 200 | True | 0.6 | 1.7 | 316.8 | 2800 | 14 |
| 1000 | True | 7.2 | 11.7 | 341.5 | 12091 | 12 |

Avalonia 示例的那次运行形状相同（1000 元素：`jump_ms` 1.9、`prep_ms` 8.2、`anim_ms` 320.4）。`attached = False` 的行把块放在可视化树之外，因此不发生布局与渲染工作；两组行之间的差距是宿主的渲染开销，不是主题系统的。`frames_per_target` 在各档规模上都贴着该 effect 的帧预算，这是同一条共享时间轴从另一侧看到的样子。

**预期结果：** 命令打印出 TSV 文件路径，表里每个（size, attached, repetition）一行，且 `prep_ms` 随 `size` 增长而 `anim_ms` 始终接近 effect 的时长。

## 3. 用自动化测试验证

引擎契约由 `Src/Core/VeloxDev.Core.Test/DynamicTheme/` 下的两个文件锁定：

`ThemeBasicsTests.cs` —— 静态模型：

- `Dark_ImplementsITheme` / `Light_ImplementsITheme` —— 两个内置主题都实现 `ITheme`。
- `ThemeManager_DefaultCurrent_IsDark` —— `ThemeManager.Current` 初始为 `typeof(Dark)`。
- `ThemeManager_SetCurrent_Changes` —— `ThemeManager.SetCurrent<Light>()` 翻转 `Current`。
- `StartModel_DefaultIsCache` / `StartModel_FlagsEnum` —— `StartModel` 默认为 `Cache`，且是 `[Flags]` 枚举。
- `ThemeConfigAttribute_2Themes_CanBeInstantiated` —— 带两个上下文数组的 2 主题特性可构造。

`ThemeTransitionTests.cs` —— 切换运行在过渡动画之上：

- `Switch_LandsExactlyOnTheTargetValue` —— 末帧被钉在声明的终值上。
- `Switch_EveryTargetIsAnchoredToTheSameTimeline` —— 暂停一个目标即暂停全部。
- `Switch_SeekIsReachableAndFinishesThePass` —— seek 过末尾会把这一程跑完并落在终点。
- `Switch_HonoursAutoReverseAndLoopTime` —— effect 自己的标志被遵守。
- `Switch_HoldsAnUnsampledPropertyUntilTheEnd` —— 没有采样器的属性全程保持原值，最后跳变。
- `Switch_WithNoPlatformSeam_AppliesImmediately` —— 没有 scheduler 就是瞬时切换，而不是卡住不动。
- `Jump_WritesTheTargetValue` / `Jump_SkipsAnUnregisteredTarget` —— `Jump` 写入目标值，并忽略未注册对象。

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"
```

**预期结果：** 全部 15 个 DynamicTheme 测试通过。

## 4. 完整代码

一个单文件、自包含的 WPF 程序（无 XAML）：先创建空工程（`dotnet new console -n DynamicThemeQuickStart`），通过目标框架开启 WPF，再替换工程文件与 `Program.cs`。它在 `Window` 上声明两个参与主题的属性，并用 `ThemeManager` 切换：

```xml
<Project Sdk="Microsoft.NET.Sdk">

    <PropertyGroup>
        <OutputType>WinExe</OutputType>
        <TargetFramework>net9.0-windows</TargetFramework>
        <UseWPF>true</UseWPF>
        <Nullable>enable</Nullable>
        <ImplicitUsings>enable</ImplicitUsings>
    </PropertyGroup>

    <ItemGroup>
        <PackageReference Include="VeloxDev.WPF" Version="8.0.0" />
    </ItemGroup>

</Project>
```

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using VeloxDev.DynamicTheme;
using VeloxDev.TransitionSystem;

namespace DynamicThemeQuickStart;

[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow : Window
{
    public MainWindow()
    {
        Title = "Dynamic Theme Quick Start";
        Width = 480;
        Height = 320;

        var text = new TextBlock
        {
            Text = "VeloxDev Dynamic Theme",
            FontSize = 28,
            Margin = new Thickness(16),
        };
        text.SetBinding(Control.ForegroundProperty, new Binding(nameof(Foreground)) { Source = this });

        var button = new Button
        {
            Content = "Reverse theme",
            Margin = new Thickness(16),
            HorizontalAlignment = HorizontalAlignment.Left,
        };
        button.Click += OnReverseThemeClick;

        var panel = new StackPanel();
        panel.Children.Add(text);
        panel.Children.Add(button);
        Content = panel;

        Loaded += OnLoaded;
    }

    private void OnLoaded(object sender, RoutedEventArgs e)
    {
        InitializeTheme(); // generated; must run after the window is usable
        ThemeManager.SetPlatformInterpolator(new Interpolator()); // once, for animated switches
        ThemeManager.StartModel = StartModel.Cache;
    }

    private void OnReverseThemeClick(object sender, RoutedEventArgs e)
    {
        if (ThemeManager.Current == typeof(Dark))
            ThemeManager.Transition<Light>(TransitionEffects.Theme);
        else
            ThemeManager.Transition<Dark>(TransitionEffects.Theme);
    }

    partial void OnThemeChanged(Type? oldValue, Type? newValue)
    {
        MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
    }
}

internal static class Program
{
    [STAThread]
    public static void Main()
    {
        var app = new Application();
        app.Run(new MainWindow());
    }
}
```

上文每个标识符都已定义或来自被引用包：两行 `[ThemeConfig]` 映射 `Background`（`Light` = 白，`Dark` = 近黑）与 `Foreground`（`Light` = 近黑，`Dark` = 白）；`OnLoaded` 注册窗口、安装适配器 `Interpolator` 并选定起始模型；按钮在 `Dark` 与 `Light` 之间以 `TransitionEffects.Theme`（0.46 秒）切换。仓库中的最小示例结构相同，另有 `Jump<T>`、`SetThemeValue` / `RestoreThemeValue` 与两个缓存 getter；规模示例则多了块集合、时间轴工具条与 bench 模式。

## 5. 运行声明

- ✅ **2026-09-13 实际构建并测量。** 记录输出：
    - `dotnet build "Examples/Theme/WPF Trimmed/Demo/Demo.csproj" -c Debug` —— `已成功生成。 0 个警告 0 个错误`。
    - `dotnet build "Examples/Theme/Avalonia Trimmed/Demo/Demo.csproj" -c Debug` —— 同上，0 警告 / 0 错误。
    - `dotnet build "Examples/Theme/WPF/Demo/Demo.csproj" -c Debug` 与 `dotnet build "Examples/Theme/Avalonia/Demo/Demo.csproj" -c Debug` —— 均为 0 警告 / 0 错误。
    - `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"` —— 在 `net10.0` 上 `已通过! - 失败: 0，通过: 15，已跳过: 0，总计: 15`。
    - `dotnet run --project "Examples/Theme/WPF/Demo" -- bench` 与 Avalonia 版各跑一次 —— 均正常结束并打印 `%TEMP%\veloxdev-theme-scale.tsv`；第 2 节的数字就是从这两个文件读出的。
    - 上文单文件程序已对照当前 `VeloxDev.WPF` 适配器源码在 `net9.0-windows` 上编译核验（**0 错误 / 0 警告**）并冒烟启动：`Loaded` 主题初始化路径（`InitializeTheme`、`SetPlatformInterpolator`）运行无异常，窗口持续存活。
- ⚠️ **未用鼠标实际点击。** 示例的按钮处理器没有手工驱动过；带动画与即时两条切换路径是通过示例自带的 `bench` 模式实测的 —— 它直接调用 `ThemeManager.Transition` 与 `ThemeManager.Jump`，并等待 `ThemeManager.Current` 推进。在运行中的窗口里观察一次点击，留给读者作端到端核验。
