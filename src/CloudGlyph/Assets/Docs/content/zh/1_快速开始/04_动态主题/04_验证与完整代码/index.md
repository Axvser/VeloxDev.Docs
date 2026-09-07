# 动态主题 — 验证与完整代码

## 1. 用示例验证

`Examples/Theme/` 下提供两个 GUI 示例（WPF 与 Avalonia），每个都是通过点击在主题间切换已映射颜色的小窗口。启动一个（例如 `dotnet run --project Examples/Theme/WPF/Demo`）并点击主题切换按钮：

- 运行 `Transition<T>(...)` 时，窗口已映射属性（WPF 示例映射 `Background`/`Foreground`）在 `TransitionEffects.Theme`（0.46 秒）内**平滑**插值到另一主题。
- `Jump<T>()` 应用同样的值但**立即**完成、无插值。
- 每次切换后，生成的 `partial void OnThemeChanged(Type? oldValue, Type? newValue)` 会触发（WPF 示例弹出一个消息框）。
- 通过 `SetThemeValue<T>(nameof(...), new object?[] { ... })` 的运行时覆盖对当前主题立即生效；`RestoreThemeValue<T>` 恢复静态值。

**预期结果：** 每次点击窗口都会重新着色 —— `Transition` 平滑、`Jump` 即时 —— 且每次都弹出回调消息。

## 2. 用自动化测试验证

引擎契约由 `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs` 锁定：

- `Dark_ImplementsITheme` / `Light_ImplementsITheme` —— 两个内置主题都实现 `ITheme`。
- `ThemeManager_DefaultCurrent_IsDark` —— `ThemeManager.Current` 初始为 `typeof(Dark)`。
- `ThemeManager_SetCurrent_Changes` —— `ThemeManager.SetCurrent<Light>()` 翻转 `Current`。
- `StartModel_DefaultIsCache` / `StartModel_FlagsEnum` —— `StartModel` 默认为 `Cache`，且是 `[Flags]` 枚举。
- `ThemeConfigAttribute_2Themes_CanBeInstantiated` —— 带两个上下文数组的 2 主题特性可构造。

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"
```

**预期结果：** 全部 7 个 DynamicTheme 测试通过。

## 3. 完整代码

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
        InitializeTheme(); // 生成方法；必须在窗口可用后调用
        ThemeManager.SetPlatformInterpolator(new Interpolator()); // 一次，用于带动画切换
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

上文每个标识符都已定义或来自被引用包：两行 `[ThemeConfig]` 映射 `Background`（`Light` = 白，`Dark` = 近黑）与 `Foreground`（`Light` = 近黑，`Dark` = 白）；`OnLoaded` 注册窗口并安装适配器 `Interpolator`；按钮在 `Dark` 与 `Light` 之间以 `TransitionEffects.Theme`（0.46 秒）切换。仓库中的示例（`Examples/Theme/WPF/Demo/MainWindow.xaml.cs`）结构相同，另演示了 `Jump<T>`、`SetThemeValue`/`RestoreThemeValue` 以及 `GetStaticThemeCache`/`GetActiveThemeCache`。Avalonia 示例（`Examples/Theme/Avalonia/Demo`）用 `[ThemeConfig<ObjectConverter, Dark, Light>]`（主题顺序 `Dark, Light`）镜像同一场景，并通过 `RelativeSource AncestorType=views:MainWindow` 绑定。

## 4. 运行声明

- ⚠️ **部分验证 —— 未交互式观察动画切换。** 2026-09-07 记录：
    - `dotnet build Examples/Theme/WPF/Demo/Demo.csproj -c Debug` —— 成功，**0 错误**（`VeloxDev.Core` TransitionSystem 代码有 3 条与 DynamicTheme 无关的警告）。
    - `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"` —— **7 通过 / 0 失败**。
    - 上文单文件程序已对照当前 `VeloxDev.WPF` 适配器源码在 `net9.0-windows` 上编译核验（**0 错误**）并冒烟启动：`Loaded` 主题初始化路径（`InitializeTheme`、`SetPlatformInterpolator`）运行无异常，窗口持续存活。实际点击按钮观察 0.46 秒的颜色过渡，留给读者作端到端核验。
