# Transition — Verify & Complete Code

There are three independent ways to verify this feature, in increasing strength: run a demo by hand, run the unit tests, or run the `AUTO TEST` conformance harness against the real demos.

## 1. Verify with the demos (manual)

Seven GUI demos ship under `Examples/Transition/` (WPF, Avalonia, WinUI, WinForms, MAUI, Blazor/Razor, Jalium), each a small window that runs the same animation scenarios. Build and launch one:

```bash
dotnet build Examples/Transition/WPF/Demo/Demo.csproj -c Debug
cd Examples/Transition/WPF/Demo && dotnet run
```

Then exercise its controls:

- **Start (main thread)** / **Start (background thread)** — the same three `Execute` calls, once from the UI thread and once inside `Task.Run`; both animate (UI-thread marshaling).
- **Start (non-mutual)** — the three animations run concurrently with `CanMutualTask: false`; the `nomutual=` readout counts them.
- **Repeat** — each click starts `Animation0` again on the same rectangle; the previous run is cancelled and the rectangle restarts.
- **Stop all** / **Exit** — `Transition.Exit(...)` freezes the rectangles in place (it does *not* jump to the end value).
- **Pause / Resume / ×0.25 / ×4 / ×1 / next pass** — the timeline-control row, driving `Transition.Pause` / `Resume` / `SetRate` / `Seek` over a live `paused` / `rate` / `pos` / `cycle` readout.
- **Reset** — a `CreateReset*` builder (the initial values declared path by path) applied so the rectangle returns exactly to its declared rest state.

**Expected result:** the rectangle slides right and fades while its fill turns orange over 2 s, then auto-reverses twice; the overshoot rows visibly pass their target and come back (`Back` and `Elastic`); the reset, stop and control buttons behave as described.

## 2. Verify with the `AUTO TEST` conformance harness (strongest)

`Examples/Transition/AUTO TEST/` starts each demo's **executable**, drives it over UI Automation (Blazor over Playwright/Edge), and checks what actually happened on screen — including sampler arithmetic against a closed form written independently of the library. Build the demos first, in exactly this form:

```bash
for p in WPF WinForms Avalonia MAUI WinUI Jalium; do dotnet build "Examples/Transition/$p/Demo/Demo.csproj" -c Debug; done
dotnet build "Examples/Transition/Blazor/Demo/Demo/Demo.csproj" -c Debug

cd "Examples/Transition/AUTO TEST"
VELOXDEV_AT=1 VELOXDEV_AT_PACE=0 VELOXDEV_AT_OBSERVE=0 VELOXDEV_BENCH_MS=200 dotnet test VeloxDev.AT.csproj --nologo
```

`VELOXDEV_AT=1` is mandatory — without it every UI test reports as *skipped* and the run exits 0.

**Expected result (recorded, 2026-10-01):** all seven demos build with 0 errors, and the suite reports `测试运行成功。测试总数: 33 / 通过数: 32 / 跳过数: 1 / 总时间: 1.9579 分钟` — 32 passed, 0 failed, 1 skipped (the `[Ignore]`d reachability stress test). The 32 green tests are, per platform, `ObservationSurface_IsReachableAndTicking`, `LoadModes_MatchTheLibrarySemantics`, `EverySamplerMatchesItsClosedForm` and `TimelineControl_SteersTheRunningAnimation` (plus a fifth, browser-computed-style check on Blazor), together with three assembly-level coverage guards.

## 3. Verify with the automated unit tests

The engine contract is pinned by two folders of `VeloxDev.Core.Test`:

- `Src/Core/VeloxDev.Core.Test/TransitionSystem/` — 26 files: `EasesTests`, `EaseOvershootTests`, `InterpolatorCoreTests`, `NativeSamplersTests`, `NativeSamplersExtendedTests`, `SamplerConformanceTests`, `SamplerSetTests`, `SamplingLoopTests`, `FramePacerTests`, `FramePathAllocationTests`, `ReusableTimerWaitTests`, `TransitionEffectCoreTests`, `TransitionDiagnosticsTests`, `StateCoreTests`, `TransitionPropertyTests`, `TransitionPropertyIndexerTests`, `TransitionPathConflictTests`, `TransitionPathValidationTests`, `TimelineControlTests`, `ChainRepeatTests`, `TransitionSchedulerAwakeTests`, `TransitionSchedulerExitTests`, `TransitionSchedulerPrepareTests`, `TransitionRunThreadAffinityTests`, `NoMutualSchedulerRegistryTests`, `QuaternionOvershootTests`.
- `Src/Core/VeloxDev.Core.Test/Timing/` — 6 files: `CompensatingTimeSamplerTests`, `UncompensatedTimeSamplerTests`, `TimeSourceContractTests`, `HostTimeSourceTests`, `TimerCoreRegistryTests`, plus the `FakeTimeSource` rig that drives the clock by hand so the step-count assertions are exact integers rather than ratios.

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj \
  --filter "FullyQualifiedName~TransitionSystem|FullyQualifiedName~Timing"
```

**Expected result (recorded, 2026-10-01):** `测试运行成功。测试总数: 285 / 通过数: 285` in 24.5 s.

## 4. Complete code

A single-file, self-contained WPF program (no XAML) that builds the `Animation0` shape from the demo and runs it against one rectangle. Create an empty console project (`dotnet new console -n TransitionQuickStart`), then replace `TransitionQuickStart.csproj` and `Program.cs`:

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

Every identifier is defined above: the transition declares `Opacity → 0`, `RenderTransform.X → 200` and `Fill → orange`; the effect plays 2 s, auto-reverse, three forth-and-back passes with `Eases.Sine.InOut`. The rectangle starts cyan and, once the window loads, animates across the canvas. When the window closes (`app.Run` returns), `Main` returns and the process exits.

## 5. Run declaration

- ✅ **The `AUTO TEST` suite was actually built and run on 2026-10-01**, all seven demos rebuilt first, on Windows 11 with .NET 10 SDK. Recorded verdict:
  `测试运行成功。测试总数: 33，通过数: 32，跳过数: 1，总时间: 1.9579 分钟` (exit code 0; the one skip is the `[Ignore]`d `Stress_ReactivatingARowWhileTheDemoIsBusy`). This exercises all seven real demos end to end, including the sampler closed-form check and the timeline-control check.
- ✅ **The unit tests were actually run on 2026-10-01**: `dotnet test … --filter "FullyQualifiedName~TransitionSystem|FullyQualifiedName~Timing"` → `测试运行成功。测试总数: 285，通过数: 285` in 24.5 s.
- ✅ **The demo builds were verified**: `dotnet build` on WPF, WinForms, Avalonia, MAUI, WinUI, Jalium and Blazor demos reported 0 errors each.
- ⚠️ **The §4 window was not launched interactively** in this documentation pass; it mirrors `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` (`Animation0`), which the `AUTO TEST` suite drove on screen. Launching it and watching the animation is left as the reader's end-to-end check.
