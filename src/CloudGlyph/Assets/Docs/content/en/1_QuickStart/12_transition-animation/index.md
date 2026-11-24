# Transition Animation

Build a WPF window whose `Rectangle` slides and fades with a fluent transition, then reverse itself. The same declarations run unchanged from the UI thread or a background thread; the adapter marshals each frame back to the dispatcher.

## 1. Prerequisites

- **Supported targets of the WPF adapter** (`Src/Adapters/VeloxDev.WPF/VeloxDev.WPF.csproj`): `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows`. The sample uses `net8.0-windows`.
- **`VeloxDev.WPF`** brings `VeloxDev.Core` with it. The demo is built with .NET 9; `net8.0-windows` is the declared minimum of this adapter line.
- .NET SDK 8.0 or later on Windows, plus the Windows Desktop workload. No services are required.

## 2. Install / Add Dependency

```text
dotnet new console -n TransitionQuickStart
cd TransitionQuickStart
dotnet add package VeloxDev.WPF --version 12.3.0
```

Edit the project so WPF is available:

```xml
<PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWPF>true</UseWPF>
</PropertyGroup>
```

**Expected result:** the package restores, the project builds as a WPF executable, and `VeloxDev.TransitionSystem` resolves.

## 3. Basic Setup / Registration

A transition is a chain of property declarations plus one effect. `Transition<T>` is the platform type; `Create()` starts an empty chain.

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var box = new Rectangle
{
    Width = 80,
    Height = 60,
    Fill = Brushes.Cyan,
    RenderTransform = new TranslateTransform()
};

var slide = Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0.25d)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 220d)
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(1.5),
        FPS = 60,
        Ease = Eases.Cubic.InOut,
        IsAutoReverse = true,
        LoopTime = 1
    });
```

**Expected result:** constructing the chain does not animate anything; it only records the end values and the effect. The start value is read from the target when `Execute` runs.

## 4. Core Usage (Step by Step)

### 4.1 Property paths and typed overloads

`Property` takes a lambda, not a string. A nested member is a nested path: `((TranslateTransform)r.RenderTransform).X` writes the child object's property in place. Typed overloads exist for `double`, `int`, `float`, `decimal`, `Brush`, `Transform`, `Color`, `Point`, `Size`, `Rect`, `CornerRadius`, `Thickness`, `Vector`, `Point3D` and the `System.Drawing` equivalents; the WPF adapter supplies the samplers behind them.

For a `Transform` member the overload takes a collection: one element is assigned directly — preserving its runtime type, which keeps the nested `((TranslateTransform)r.RenderTransform).X` path valid — and several are wrapped in a `TransformGroup`.

**Expected result:** `Property(r => r.Opacity, 0.25d)` compiles to the `double` overload; a transform collection of one stays a `TranslateTransform`.

### 4.2 Effects and easing

`TransitionEffect` carries `Duration`, `FPS` (default 60), `Ease`, `IsAutoReverse` and `LoopTime`. `Eases` exposes ten families — `Sine`, `Quad`, `Cubic`, `Quart`, `Quint`, `Expo`, `Circ`, `Back`, `Elastic`, `Bounce` — each with `In`, `Out` and `InOut`, plus `Eases.Default`.

`Back` and `Elastic` deliberately pass the target and come back. That is why the progress a sampler uses can leave `[0, 1]`:

```plot
{
  "title": "Overshooting eases",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.2, 1.8] },
  "data": [
    { "fn": "x", "color": "#888888" },
    { "fn": "1 + 2.70158*(x-1)^3 + 1.70158*(x-1)^2", "color": "#4a9eff" },
    { "fn": "exp(-10*x*0.6931471805599453)*sin((10*x-0.75)*2.0943951023931953)+1", "color": "#f472b6" }
  ]
}
```

**Expected result:** `Back.Out` peaks near 1.10 and `Elastic.Out` near 1.37 before settling at 1.

### 4.3 Execute, mutual and concurrent

`Execute(target)` runs a snapshot and defaults to `CanMutualTask: true`: a new animation on the same target cancels the previous one. Pass `false` to run concurrently.

```csharp
slide.Execute(box);                        // mutually exclusive with the previous run
slide.Execute(box, CanMutualTask: false);  // concurrent
_ = System.Threading.Tasks.Task.Run(() => slide.Execute(box));
```

Starting from a non-UI thread is supported; the adapter switches each frame back to the UI thread using the target's dispatcher. The starting value is whatever the target holds when the run begins, so write the start back first if the run must always begin from a known state.

**Expected result:** a second click replaces the first animation; the non-mutual call lets both runs write the target.

### 4.4 Chaining segments

`Await` pauses before the next segment, `Then` starts one immediately, `AwaitThen` pauses and starts, and `Repeat(n)` reruns the chain from its first segment. Only a count on the last segment repeats the whole chain.

```csharp
var chain = Transition<Rectangle>.Create()
    .Await(TimeSpan.FromSeconds(0.5))
    .Property(r => r.Width, 160d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .Then()
    .Property(r => r.Opacity, 0.5d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1) })
    .Repeat(1);
```

**Expected result:** the width segment waits half a second, grows over one second, then opacity fades over the next second, and the pair repeats once.

### 4.5 Timeline transport

The control surface is addressed by **target**, not by snapshot: `Transition.Pause`, `Resume`, `SetRate`, `Seek`, `Exit`, `Position`, `Rate`, `Cycle` and `IsPaused` all take the animated object and two flags selecting mutual, non-mutual, or both runs.

```csharp
Transition.Pause(box, IncludeMutual: true, IncludeNoMutual: true);
Transition.SetRate(box, 0.5d, IncludeMutual: true, IncludeNoMutual: true);
Transition.Seek(box, TimeSpan.FromMilliseconds(750), IncludeMutual: true, IncludeNoMutual: true);
Transition.Exit(box, IncludeMutual: true, IncludeNoMutual: true);   // stops in place
```

**Expected result:** pause freezes every selected run; setting the rate to 0.5 halves the speed without reporting `IsPaused`; `Exit` stops without snapping to the end value.

## 5. Verification

Run the complete program. A cyan rectangle must move 220 pixels to the right while fading to 25%, then reverse and return to its start. With `IsAutoReverse = true` and `LoopTime = 1` the pair runs twice. Closing the window ends the process.

## 6. Complete Code

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        var app = new Application();

        app.Startup += (_, _) =>
        {
            var box = new Rectangle
            {
                Width = 80,
                Height = 60,
                Fill = Brushes.Cyan,
                RenderTransform = new TranslateTransform(),
                HorizontalAlignment = HorizontalAlignment.Left,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(40)
            };

            var window = new Window
            {
                Title = "Transition quick start",
                Width = 420,
                Height = 240,
                Content = box
            };

            var slide = Transition<Rectangle>.Create()
                .Property(r => r.Opacity, 0.25d)
                .Property(r => ((TranslateTransform)r.RenderTransform).X, 220d)
                .Effect(new TransitionEffect
                {
                    Duration = TimeSpan.FromSeconds(1.5),
                    FPS = 60,
                    Ease = Eases.Cubic.InOut,
                    IsAutoReverse = true,
                    LoopTime = 1
                });

            window.Loaded += (_, _) => slide.Execute(box);
            window.Show();
        };

        app.Run();
    }
}
```

The declarations are adapted from `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` (`Animation0`, `Animation2`); the timeline calls match `PauseAll`, `SetRate`, `SeekNextPass` and `ExitAll` in the same file.

## 7. Run Declaration

- ⚠️ Not actually run — statically verified only on 2026-11-25. Verified against `Src/Adapters/VeloxDev.WPF/TransitionSystem/Transition.cs`, `TransitionEffect.cs`, `TransitionEffects.cs`, `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Transition.cs`, `TransitionEx.cs` and `Eases.cs`, plus the WPF demo. No window was launched in this environment.
