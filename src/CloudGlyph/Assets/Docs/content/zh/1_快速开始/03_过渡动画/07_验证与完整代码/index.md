# Transition — 验证与完整代码

## 1. 用示例验证

`Examples/Transition/` 下提供了七个 GUI 示例（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor/Razor、Jalium），每个都是一运行相同动画场景的小窗口。启动一个（例如 `dotnet run --project Examples/Transition/WPF/Demo`）并点击按钮：

- **启动（主线程）** —— 三个矩形在 UI 线程上以互斥方式动画。
- **启动（后台线程）** —— 同样的 `Execute` 调用在 `Task.Run` 内执行，矩形仍然动画（UI 线程编组）。
- **启动（非互斥）** —— 三个动画以 `CanMutualTask: false` 并发运行。
- **重复** —— 每次点击都在同一矩形上再次启动 `Animation0`；上一轮被取消，矩形重新开始。
- **退出 / 全部停止** —— `Transition.Exit(...)` 让矩形就地冻结。
- **重置** —— `CreateReset().Effect(TransitionEffects.Empty).Execute(rect)` 用一个零时长效果把各初始值逐条写回。

**预期结果：** 矩形在 2 秒内右移并淡出、填充转橙，然后自动往返两次；重置与退出按钮的行为如上所述。

## 2. 用自动化测试验证

引擎契约由 `Src/Core/VeloxDev.Core.Test/TransitionSystem/` 锁定：

- `EasesTests` —— 每种标准缓动的边界值（`Ease(0) = 0`、`Ease(1) = 1`），及 `Eases.Quad.In` 的单调性。
- `InterpolatorCoreTests` —— 在 `NativeInterpolators` 注册表上执行注册 / 读取 / 覆盖 / 注销，以及查找的解析顺序：先基类（由近及远）再接口、基类胜过接口、两个接口都匹配时胜者确定。
- `SamplingLoopTests` —— `Duration = 0`、自动往返与 `LoopTime` 下对 `double` 属性的无界面运行；断言 `Completed`/`Canceled`/`Finally` 触发。
- `NativeSamplersTests`、`TransitionEffectCoreTests`、`StateCoreTests`、`TransitionPropertyTests`、`SamplerSetTests` —— 采样器端点、效果克隆/事件、状态字典与路径解析。

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~TransitionSystem"
```

**预期结果：** 所有 TransitionSystem 测试通过（采样循环测试是确定性的，因为 `Duration = 0` 每程只采样一次）。

## 3. 完整代码

一个单文件、自包含的 WPF 程序（无 XAML），构建示例中 `Animation0` 的形状并对一个矩形运行。先创建空控制台项目（`dotnet new console -n TransitionQuickStart`），然后替换 `TransitionQuickStart.csproj` 与 `Program.cs`：

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
        <PackageReference Include="VeloxDev.WPF" Version="9.0.0" />
    </ItemGroup>

</Project>
```

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

namespace TransitionQuickStart;

public static class Program
{
    private static readonly Transition<Rectangle> Animation0 =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
            .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
            .Effect(new TransitionEffect
            {
                Duration = TimeSpan.FromSeconds(2),
                IsAutoReverse = true,
                LoopTime = 2,
                Ease = Eases.Sine.InOut,
            });

    [STAThread]
    public static void Main()
    {
        var app = new Application();
        var window = new Window { Title = "Transition Quick Start", Width = 920, Height = 300 };
        var canvas = new Canvas { Background = Brushes.White };

        var rect = new Rectangle
        {
            Width = 120,
            Height = 60,
            Fill = Brushes.Cyan,
            RenderTransform = new TranslateTransform(),
        };
        canvas.Children.Add(rect);

        window.Content = canvas;
        window.Loaded += (_, _) => Animation0.Execute(rect);
        app.Run(window);
    }
}
```

上文每个标识符都已定义：animation 声明 `Opacity → 0`、`RenderTransform.X → 800` 与 `Fill → 橙色`；效果为 2 秒、自动往返、`Eases.Sine.InOut` 三个来回。矩形初始为青色，窗口加载后横穿画布。窗口关闭（`app.Run` 返回）后，`Main` 返回、进程退出。

## 4. 运行声明

- ⚠️ **未交互式运行** — 本次文档编写未执行 UI。上面的程序已在 **2026-09-07 编译核验**：对照真实 `VeloxDev.WPF` 适配器源码（Debug 项目引用）以 `net9.0-windows` 构建，`dotnet build` 报告 0 警告 / 0 错误；其所参照的 WPF 示例（`Examples/Transition/WPF/Demo`）同样构建通过。打开窗口并观察动画，留给读者作端到端核验。
