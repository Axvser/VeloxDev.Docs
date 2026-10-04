# 过渡动画 — 验证与完整代码

验证本特性有三条彼此独立的途径，强度递增：手动跑一个演示、跑单元测试，或对真实演示跑 `AUTO TEST` 一致性套件。

## 1. 用演示验证（手动）

`Examples/Transition/` 下有七个 GUI 演示（WPF、Avalonia、WinUI、WinForms、MAUI、Blazor/Razor、Jalium），每个都是一个跑同一批动画场景的小窗口。构建并启动一个：

```bash
dotnet build Examples/Transition/WPF/Demo/Demo.csproj -c Debug
cd Examples/Transition/WPF/Demo && dotnet run
```

然后操作它的控件：

- **主线程启动** / **后台线程启动** —— 同样的三个 `Execute` 调用，一次在 UI 线程、一次在 `Task.Run` 里；两者都能动画（UI 线程编组）。
- **非互斥启动** —— 三条动画以 `CanMutualTask: false` 并发运行；`nomutual=` 读数计数它们。
- **重复** —— 每次点击都在同一矩形上重新启动 `Animation0`；上一趟被取消、矩形重新开始。
- **全部停止** / **退出** —— `Transition.Exit(...)` 把矩形冻在原地（*不*跳到终值）。
- **暂停 / 恢复 / ×0.25 / ×4 / ×1 / 下一趟** —— 时间轴控制那一排，在活的 `paused` / `rate` / `pos` / `cycle` 读数上驱动 `Transition.Pause` / `Resume` / `SetRate` / `Seek`。
- **重置** —— 一个 `CreateReset*` 构建器（逐路径声明初始值），让矩形精确回到它声明的静止态。

**预期结果：** 矩形向右滑动并淡出，同时填充色在 2 秒内变成橙色，然后自动反向两次；过冲那几行肉眼可见地越过目标再回落（`Back` 与 `Elastic`）；重置、停止与控制按钮如上所述。

## 2. 用 `AUTO TEST` 一致性套件验证（最强）

`Examples/Transition/AUTO TEST/` 启动各演示的**可执行文件**，通过 UI Automation 驱动它们（Blazor 经 Playwright/Edge），并检查屏幕上实际发生了什么 —— 包括把采样器算术与一份独立于库写就的闭式解对照。先按如下确切形式构建演示：

```bash
for p in WPF WinForms Avalonia MAUI WinUI Jalium; do dotnet build "Examples/Transition/$p/Demo/Demo.csproj" -c Debug; done
dotnet build "Examples/Transition/Blazor/Demo/Demo/Demo.csproj" -c Debug

cd "Examples/Transition/AUTO TEST"
VELOXDEV_AT=1 VELOXDEV_AT_PACE=0 VELOXDEV_AT_OBSERVE=0 VELOXDEV_BENCH_MS=200 dotnet test VeloxDev.AT.csproj --nologo
```

`VELOXDEV_AT=1` 是必需的 —— 没有它每个 UI 测试都报为*跳过*且退出码 0。

**预期结果（已记录，2026-10-01）：** 七个演示全部构建 0 错误，套件报 `测试运行成功。测试总数: 33 / 通过数: 32 / 跳过数: 1 / 总时间: 1.9579 分钟` —— 通过 32、失败 0、跳过 1（被 `[Ignore]` 的可达性压力测试）。那 32 条绿色测试逐平台为 `ObservationSurface_IsReachableAndTicking`、`LoadModes_MatchTheLibrarySemantics`、`EverySamplerMatchesItsClosedForm` 与 `TimelineControl_SteersTheRunningAnimation`（Blazor 另加一条读浏览器计算样式的检查），外加三条程序集级覆盖率守卫。

## 3. 用自动化单元测试验证

引擎契约由 `VeloxDev.Core.Test` 的两个目录钉死：

- `Src/Core/VeloxDev.Core.Test/TransitionSystem/` —— 26 个文件：`EasesTests`、`EaseOvershootTests`、`InterpolatorCoreTests`、`NativeSamplersTests`、`NativeSamplersExtendedTests`、`SamplerConformanceTests`、`SamplerSetTests`、`SamplingLoopTests`、`FramePacerTests`、`FramePathAllocationTests`、`ReusableTimerWaitTests`、`TransitionEffectCoreTests`、`TransitionDiagnosticsTests`、`StateCoreTests`、`TransitionPropertyTests`、`TransitionPropertyIndexerTests`、`TransitionPathConflictTests`、`TransitionPathValidationTests`、`TimelineControlTests`、`ChainRepeatTests`、`TransitionSchedulerAwakeTests`、`TransitionSchedulerExitTests`、`TransitionSchedulerPrepareTests`、`TransitionRunThreadAffinityTests`、`NoMutualSchedulerRegistryTests`、`QuaternionOvershootTests`。
- `Src/Core/VeloxDev.Core.Test/Timing/` —— 6 个文件：`CompensatingTimeSamplerTests`、`UncompensatedTimeSamplerTests`、`TimeSourceContractTests`、`HostTimeSourceTests`、`TimerCoreRegistryTests`，以及手工驱动时钟的 `FakeTimeSource` 测试台 —— 它让步数断言是精确整数而不是比值。

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj \
  --filter "FullyQualifiedName~TransitionSystem|FullyQualifiedName~Timing"
```

**预期结果（已记录，2026-10-01）：** `测试运行成功。测试总数: 285 / 通过数: 285`，用时 24.5 秒。

## 4. 完整代码

一个单文件、自包含的 WPF 程序（无 XAML），构建演示里 `Animation0` 的形状并把它跑在一个矩形上。创建一个空控制台项目（`dotnet new console -n TransitionQuickStart`），然后替换 `TransitionQuickStart.csproj` 与 `Program.cs`：

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

上面用到的每个标识符都已定义：该过渡声明 `Opacity → 0`、`RenderTransform.X → 200` 与 `Fill → 橙色`；效果播放 2 秒、自动反向、三趟来回、`Eases.Sine.InOut`。矩形以青色起始，窗口加载后便在画布上动画。窗口关闭（`app.Run` 返回）时 `Main` 返回、进程结束。

## 5. 运行声明

- ✅ **`AUTO TEST` 套件已于 2026-10-01 实际构建并运行**，先重建全部七个演示，Windows 11 + .NET 10 SDK。记录结论：
  `测试运行成功。测试总数: 33，通过数: 32，跳过数: 1，总时间: 1.9579 分钟`（退出码 0；唯一跳过的是被 `[Ignore]` 的 `Stress_ReactivatingARowWhileTheDemoIsBusy`）。这端到端演练了全部七个真实演示，含采样器闭式解检查与时间轴控制检查。
- ✅ **单元测试已于 2026-10-01 实际运行**：`dotnet test … --filter "FullyQualifiedName~TransitionSystem|FullyQualifiedName~Timing"` → `测试运行成功。测试总数: 285，通过数: 285`，用时 24.5 秒。
- ✅ **演示构建已核验**：WPF、WinForms、Avalonia、MAUI、WinUI、Jalium 与 Blazor 演示的 `dotnet build` 各自报 0 错误。
- ⚠️ **§4 的窗口在本次文档撰写中未交互式启动**；它镜像 `Examples/Transition/WPF/Demo/MainWindow.xaml.cs`（`Animation0`），而后者已被 `AUTO TEST` 套件在屏幕上驱动。启动它并观察动画留给读者作为端到端检查。
