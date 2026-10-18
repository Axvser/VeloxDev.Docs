# 过渡动画 — 验证与完整代码

验证本特性有三种彼此独立的方式，强度递增：手动运行 demo、运行单元测试、或对真实 demo 运行 `AUTO TEST` 一致性验收套件。

## 1. 用 demo 验证（手动）

`Examples/Transition/` 下有七个 GUI demo（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor/Razor、Jalium），每个都是运行相同动画场景的小窗口。构建并启动一个：

```bash
dotnet build Examples/Transition/WPF/Demo/Demo.csproj -c Debug
cd Examples/Transition/WPF/Demo && dotnet run
```

然后操作它的控件：

- **Start (main thread)** / **Start (background thread)** —— 同样的三次 `Execute`，一次在 UI 线程、一次在 `Task.Run` 内；两者都会动画（UI 线程编组）。
- **Start (non-mutual)** —— 三个动画以 `CanMutualTask: false` 并发运行；`nomutual=` 读数统计它们。
- **Repeat** —— 每次点击都在同一矩形上重新启动 `Animation0`；上一次运行被取消，矩形重启。
- **Stop all** / **Exit** —— `Transition.Exit(...)` 把矩形原地冻结（*不会*跳到终值）。
- **Pause / Resume / ×0.25 / ×4 / ×1 / next pass** —— 时间轴控制行，在活动的 `paused` / `rate` / `pos` / `cycle` 读数上驱动 `Transition.Pause` / `Resume` / `SetRate` / `Seek`。
- **Reset** —— 一个 `CreateReset*` 构建器（逐路径声明初始值），应用后矩形精确回到声明的静止状态。

**预期结果：** 矩形在 2 秒内右移并淡出，同时填充色转为橙色，然后自动反向两次；过冲行明显越过目标再回来（`Back` 与 `Elastic`）；重置、停止与控制按钮按描述工作。

## 2. 用 `AUTO TEST` 一致性套件验证（最强）

`Examples/Transition/AUTO TEST/` 启动每个 demo 的**可执行文件**，经 UI Automation（Blazor 经 Playwright/Edge）操作，并检查屏幕上实际发生了什么 —— 包括用独立于库写就的闭式解核对采样器算术。先按这个形式构建 demo：

```bash
for p in WPF WinForms Avalonia MAUI WinUI Jalium; do dotnet build "Examples/Transition/$p/Demo/Demo.csproj" -c Debug; done
dotnet build "Examples/Transition/Blazor/Demo/Demo/Demo.csproj" -c Debug

cd "Examples/Transition/AUTO TEST"
VELOXDEV_AT=1 VELOXDEV_AT_PACE=0 VELOXDEV_AT_OBSERVE=0 VELOXDEV_BENCH_MS=200 dotnet test VeloxDev.AT.csproj --nologo
```

`VELOXDEV_AT=1` 是必需的 —— 没有它，所有 UI 测试报告为*跳过*并以 0 退出。

**预期结果（记录，2026-10-01）：** 七个 demo 全部 0 错误构建，套件报告 `测试运行成功。测试总数: 33 / 通过数: 32 / 跳过数: 1 / 总时间: 1.9579 分钟` —— 32 通过、0 失败、1 跳过（被 `[Ignore]` 的可达性压力测试）。32 个绿色测试按平台为 `ObservationSurface_IsReachableAndTicking`、`LoadModes_MatchTheLibrarySemantics`、`EverySamplerMatchesItsClosedForm` 与 `TimelineControl_SteersTheRunningAnimation`（Blazor 另有第五个浏览器计算样式检查），外加三个程序集级覆盖守卫。

## 3. 用自动化单元测试验证

引擎契约由 `VeloxDev.Core.Test` 的两个文件夹钉住：

- `Src/Core/VeloxDev.Core.Test/TransitionSystem/` —— 26 个文件：`EasesTests`、`EaseOvershootTests`、`InterpolatorCoreTests`、`NativeSamplersTests`、`NativeSamplersExtendedTests`、`SamplerConformanceTests`、`SamplerSetTests`、`SamplingLoopTests`、`FramePacerTests`、`FramePathAllocationTests`、`ReusableTimerWaitTests`、`TransitionEffectCoreTests`、`TransitionDiagnosticsTests`、`StateCoreTests`、`TransitionPropertyTests`、`TransitionPropertyIndexerTests`、`TransitionPathConflictTests`、`TransitionPathValidationTests`、`TimelineControlTests`、`ChainRepeatTests`、`TransitionSchedulerAwakeTests`、`TransitionSchedulerExitTests`、`TransitionSchedulerPrepareTests`、`TransitionRunThreadAffinityTests`、`NoMutualSchedulerRegistryTests`、`QuaternionOvershootTests`。
- `Src/Core/VeloxDev.Core.Test/Timing/` —— 6 个文件：`CompensatingTimeSamplerTests`、`UncompensatedTimeSamplerTests`、`TimeSourceContractTests`、`HostTimeSourceTests`、`TimerCoreRegistryTests`，以及 `FakeTimeSource` 夹具 —— 它手动驱动时钟，因此步数断言是精确整数而不是比例。

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj \
  --filter "FullyQualifiedName~TransitionSystem|FullyQualifiedName~Timing"
```

**预期结果（记录，2026-10-18）：** `已通过! - 失败: 0，通过: 287，已跳过: 0，总计: 287，持续时间: 23 s`。

## 4. 完整代码

一个单文件、自包含的 WPF 程序（无 XAML），构建 demo 的 `Animation0` 形状并作用在一个矩形上。创建空控制台项目（`dotnet new console -n TransitionQuickStart`），然后替换 `TransitionQuickStart.csproj` 与 `Program.cs`：

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
        <PackageReference Include="VeloxDev.WPF" Version="10.0.0" />
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
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 200d)
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

上面每个标识符都已定义：过渡声明 `Opacity → 0`、`RenderTransform.X → 200` 与 `Fill → orange`；效果播放 2 秒、自动反向、三次来回，使用 `Eases.Sine.InOut`。矩形初始为青色，窗口加载后横穿画布。窗口关闭（`app.Run` 返回）时 `Main` 返回，进程退出。

**预期结果：** 窗口打开，青色矩形用 2 秒滑向右侧到 `X = 200`，填充渐变为橙色，随后自动反向并重复三次。

## 5. 运行声明

- ✅ **`AUTO TEST` 套件于 2026-10-01 实际构建并运行**，先重建全部七个 demo，Windows 11 + .NET 10 SDK。记录结论：`测试运行成功。测试总数: 33，通过数: 32，跳过数: 1，总时间: 1.9579 分钟`（退出码 0；唯一跳过是被 `[Ignore]` 的 `Stress_ReactivatingARowWhileTheDemoIsBusy`）。它端到端练了七个真实 demo，包括采样器闭式解检查与时间轴控制检查。
- ✅ **单元测试于 2026-10-18 实际运行**：`dotnet test … --filter "FullyQualifiedName~TransitionSystem|FullyQualifiedName~Timing"` → `已通过! - 失败: 0，通过: 287，已跳过: 0，总计: 287，持续时间: 23 s`（退出码 0）。
- ✅ **demo 构建曾于 2026-10-01 验证**：WPF、WinForms、Avalonia、MAUI、WinUI、Jalium 与 Blazor demo 的 `dotnet build` 各报 0 错误。
- ⚠️ **§4 窗口在本次文档更新中没有交互启动**；它镜像 `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`（`Animation0`），而该 demo 曾被 `AUTO TEST` 套件在屏幕上驱动。启动它并观察动画留给读者作为端到端检查。
