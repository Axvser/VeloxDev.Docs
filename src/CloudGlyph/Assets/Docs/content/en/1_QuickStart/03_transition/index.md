# Transition — Quick Start

## Transition

### Quick Start

This guide gets you animating UI properties with the **Transition** feature — VeloxDev's cross-platform, code-driven interpolation engine. The core idea is **"everything is a state"**: you record a target's property values into a *state snapshot* (`StateSnapshot`), describe where the object should end up, and execute it — the engine interpolates every recorded property from its current value to the target over a timed, eased, frame-based timeline.

> Demo source: `Examples/Transition/{WPF, Avalonia, WinUI, WinForms, MAUI, Blazor}/Demo`.

#### 1. Prerequisites

- **Supported targets** (from `VeloxDev.Core.csproj`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` — usable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+); the demos target `net9.0` / `net10.0` — *tested* configurations.
- **Package manager:** NuGet (dotnet CLI or Visual Studio).
- **Required services:** a UI framework adapter (WPF / Avalonia / WinUI / MAUI / WinForms / Razor) for UI-thread animation and platform interpolators. **None required** for pure math interpolation on a POCO — `Eases`, `InterpolatorCore` / `IValueInterpolator` run in a plain console app.


#### 2. Install / Add Dependency

Add the core package and the adapter package for your GUI framework — the adapter brings the Transition engine plus platform interpolators and the UI-thread marshaller:

```bash
dotnet add package VeloxDev.Core     # pure math + engine core
dotnet add package VeloxDev.WPF      # or: Avalonia / WinUI / MAUI / WinForms / Razor
```

**Expected result:** both `dotnet add` commands print `Successfully added package ...` and the package is referenced in the `.csproj`; after a restore, `using VeloxDev.TransitionSystem;` resolves.

#### 3. Basic Setup / Registration

Create a `StateSnapshot` from a target with `Transition<T>.Create()` and record target property values. Property lambdas may be **nested paths** (e.g. `r => ((TranslateTransform)r.RenderTransform).X`):

```csharp
using VeloxDev.TransitionSystem;

private static readonly Transition<Rectangle>.StateSnapshot Animation0 =
    Transition<Rectangle>.Create()
        .Property(r => r.Opacity, 0)
        .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
        .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
        .Effect(new TransitionEffect()
        {
            Duration = TimeSpan.FromSeconds(2),
            IsAutoReverse = true,
            LoopTime = 2,
        });
```

You can also capture a live snapshot of the object's **current** values with the adapter extension `target.Snapshot(...)` / `target.SnapshotAll()` / `target.SnapshotExcept(...)`, or run a snapshot without a pre-declared builder via `Transition<T>.Execute(target, snapshot, CanMutualTask)`.

**Expected result:** the fluent chain compiles and builds a `StateSnapshot` holding 3 recorded properties (`Opacity`, `RenderTransform.X`, `Fill`) plus one `TransitionEffect` (2 s, auto-reverse twice). Nothing animates yet — the snapshot is a pure descriptor.

**Platform wiring (only some platforms need it):**

- **WPF / Avalonia / MAUI**: no wiring required — animations may even be started from a background thread; the adapter's `UIThreadInspector` marshals updates to the UI thread.
- **WinUI**: optional — `UIThreadInspector.CaptureUIThread()` may be called once on the UI thread. Any `DependencyObject` target is auto-marshalled through its own `DispatcherQueue`, so this is only needed for non-UI targets started from a background thread.
- **WinForms / Razor**: optional — `UIThreadInspector.CaptureUIThread()` may be called on the UI thread (WinForms: in `OnLoad`; Razor: in `OnInitialized`). Both adapters also lazily capture on first UI-thread access and marshal through `Control`/`SynchronizationContext`.

#### 4. Core Usage (Step by Step)

**Step 1 — record target values.** Use `.Property(x => x.Width, 200)` for each animatable property. Each call parses the expression into a `TransitionProperty` and stores the target value in the snapshot's state.

```csharp
Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 800);
```

**Expected result:** the snapshot's state now maps the two properties to their target values (`Opacity → 0`, `RenderTransform.X → 800`). You can read them back via `snapshot.GetState().Values`.

**Step 2 — set timing with an effect.** Either mutate an effect object or use the fluent setter:

```csharp
.Effect(e => e.Duration = TimeSpan.FromSeconds(2))          // fluent setter
.Effect(TransitionEffects.Hover)                            // preset: 0.32 s
.Effect(new TransitionEffect() { FPS = 144, Ease = Eases.Circ.InOut, IsAutoReverse = true, LoopTime = 2 });
```

**Expected result:** the effect descriptor carries `Duration`, `FPS` (default 60), `Ease` (default `Eases.Default`), `IsAutoReverse`, and `LoopTime`. `LoopTime = int.MaxValue` means "loop forever".

**Step 3 — sequence segments.** `.Await(timeSpan)` waits before this segment, `.Then()` starts the next segment, `.AwaitThen(timeSpan)` does both. Each segment has its own `State` + `Effect`.

```csharp
.Then()
.Property(r => r.Fill, new SolidColorBrush(Colors.Yellow))
.Effect(new TransitionEffect() { Duration = TimeSpan.FromSeconds(2), Ease = Eases.Sine.In });
```

**Expected result:** the snapshots are linked into a segment chain; the interpreter plays them in order, honoring each segment's delay, easing, and loop settings.

**Step 4 — execute.** Run the snapshot against a target. The default is **mutual-exclusive** (`CanMutualTask: true`): one object runs only one animation at a time, and a new animation cancels the running one. Pass `CanMutualTask: false` to allow parallel animations.

```csharp
Animation0.Execute(Rec0);                   // default: mutual-exclusive
Animation0.Execute(Rec0, CanMutualTask: false);
Transition<Rectangle>.Execute(Rec0, snapshot);   // static alternative
Transition.Exit(Rec0);                      // stop: IncludeMutual / IncludeNoMutual
```

**Expected result:** the property animates from its current value to the target over the effect's duration and easing. A second mutual animation cancels the first; `Transition.Exit(Rec0)` stops animations in place.

#### 5. Verification

Run the app (e.g. `dotnet run` in the WPF demo):

- The rectangle animates opacity, position, and fill over 2 s, then auto-reverses twice (`IsAutoReverse + LoopTime: 2`).
- A multi-segment animation moves + scales, waits, then animates the fill with a different easing.
- The Reset button restores the rectangle to a captured snapshot instantly (`snapshot.Effect(TransitionEffects.Empty).Execute(Rec0)`).
- Interrupt buttons call `Transition.Exit(...)` and the rectangle freezes in place.
- All six platform demos (WPF, Avalonia, WinUI, WinForms, MAUI, Blazor) run the same animation definitions — the Blazor demo animates a plain `BoxModel` view-model and re-renders via `INotifyPropertyChanged`.

#### 6. Complete Code

A minimal, self-contained WPF program (single `Program.cs`, no XAML) that animates a rectangle. Create the project with `dotnet new` + `dotnet add package VeloxDev.WPF`, then replace `Program.cs`:

```csharp
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

namespace TransitionDemo;

public static class Program
{
    private static readonly Transition<Rectangle>.StateSnapshot Animation0 =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
            .Property(r => r.Fill, new SolidColorBrush(Colors.Orange))
            .Effect(new TransitionEffect()
            {
                Duration = TimeSpan.FromSeconds(2),
                IsAutoReverse = true,
                LoopTime = 2,
                Ease = Eases.Sine.InOut,
            });

    [STAThread]
    public static int Main()
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
        window.Loaded += (s, e) => Animation0.Execute(rect);
        app.Run(window);
        return 0;
    }
}
```

The matching `.csproj` (from `dotnet new`):

```xml
<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <OutputType>WinExe</OutputType>
        <TargetFramework>net9.0-windows</TargetFramework>
        <Nullable>enable</Nullable>
        <ImplicitUsings>enable</ImplicitUsings>
        <UseWPF>true</UseWPF>
    </PropertyGroup>
    <ItemGroup>
        <PackageReference Include="VeloxDev.WPF" />
    </ItemGroup>
</Project>
```

> **Note:** the Razor adapter adds a `string?` `Property` overload for animating CSS color strings (`"#ff7043"`, `rgb(...)`, named colors). WinForms animates `IInterpolable` + `Padding` + common numerics; MAUI animates MAUI types (`Brush`, `Shadow`, `PointF`, `RectF`, ...).

#### 7. Run Declaration

- ⚠️ **Not actually run** — statically verified only. The code above was written against the verified source of `Examples/Transition/WPF/Demo/MainWindow.xaml.cs` and the adapter API in `Src/Adapters/VeloxDev.WPF/PlatformAdapters/Transition.cs`; it was **not** compiled or executed in this documentation pass.
