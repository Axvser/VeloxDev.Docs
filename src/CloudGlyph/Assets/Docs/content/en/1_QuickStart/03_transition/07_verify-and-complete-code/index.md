# Transition — Verify & Complete Code

## 1. Verify with the demos

Seven GUI demos ship under `Examples/Transition/` (WPF, Avalonia, WinUI, WinForms, MAUI, Blazor/Razor, Jalium), each a small window that runs the same animation scenarios. Launch one (e.g. `dotnet run --project Examples/Transition/WPF/Demo`) and exercise the buttons:

- **Start (main thread)** — three rectangles animate mutually-exclusive from the UI thread.
- **Start (background thread)** — the same `Execute` calls run inside `Task.Run` and the rectangles still animate (UI-thread marshaling).
- **Start (non-mutual)** — the three animations run concurrently with `CanMutualTask: false`.
- **Repeat** — each click starts `Animation0` again on the same rectangle; the previous run is cancelled and the rectangle restarts.
- **Exit / Stop all** — `Transition.Exit(...)` freezes the rectangles in place.
- **Reset** — a `CreateReset*` builder (the initial values declared path by path) played under `.Effect(TransitionEffects.Empty).Execute(...)` restores the rectangle instantly.

**Expected result:** the rectangle slides right and fades while its fill turns orange over 2 s, then auto-reverses twice; the reset and exit buttons behave as described above.

## 2. Verify with the automated tests

The engine contract is pinned by `Src/Core/VeloxDev.Core.Test/TransitionSystem/`:

- `EasesTests` — boundary values (`Ease(0) = 0`, `Ease(1) = 1`) for every standard ease and monotonicity for `Eases.Quad.In`.
- `InterpolatorCoreTests` — register / try-get / overwrite / unregister on the `NativeInterpolators` registry.
- `SamplingLoopTests` — a headless run of a `double` property with `Duration = 0`, auto-reverse and `LoopTime`; asserts `Completed`/`Canceled`/`Finally` firing.
- `NativeSamplersTests`, `TransitionEffectCoreTests`, `StateCoreTests`, `TransitionPropertyTests`, `SamplerSetTests` — sampler endpoints, effect clone/events, state dictionaries and path parsing.
- `TransitionPathConflictTests` / `TransitionPathValidationTests` — the parent/child path conflict and the unsampleable-path rejection.

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~TransitionSystem"
```

**Expected result:** all TransitionSystem tests pass (the sampling-loop tests are deterministic because `Duration = 0` samples once per pass).

## 3. Complete code

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

Every identifier is defined above: the transition declares `Opacity → 0`, `RenderTransform.X → 800` and `Fill → orange`; the effect plays 2 s, auto-reverse, three forth-and-back passes with `Eases.Sine.InOut`. The rectangle starts cyan and, once the window loads, animates across the canvas. When the window closes (`app.Run` returns), `Main` returns and the process exits.

## 4. Run declaration

- ⚠️ **Not interactively run** — no UI execution was performed in this documentation pass. The program above **was compile-verified on 2026-09-07**: built against the real `VeloxDev.WPF` adapter source (Debug project reference) on `net9.0-windows`, `dotnet build` reported 0 warnings / 0 errors, as did the WPF demo (`Examples/Transition/WPF/Demo`) it mirrors. Launching the window and observing the animation is left as the reader's end-to-end check.
