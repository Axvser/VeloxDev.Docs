# Runtime Themes

Give one WPF window two theme value sets, switch between them with an animated transition, and observe the change through generated callbacks. Theme values are converted once by the platform converter; switching only samples the already-built values.

## 1. Prerequisites

- **Supported targets of the WPF adapter**: `netframework4.6.1;net5.0-windows;netcoreapp3.0;net8.0-windows`; the sample uses `net8.0-windows`. The animated path additionally needs the transition surface of the same adapter.
- **`VeloxDev.WPF`** (brings `VeloxDev.Core`) and **`VeloxDev.Core.Generator`**. The generator is an analyzer (a NuGet reference to Core carries it; a `ProjectReference` does not) and is not a runtime dependency. The sample installs it explicitly for its build-time Roslyn check.
- .NET SDK 8.0+ on Windows with the Windows Desktop workload. No services are required.

## 2. Install / Add Dependency

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

**Expected result:** both packages restore. After the first build the generated `InitializeTheme`, `SetThemeValue`, `RestoreThemeValue` and the two partial callbacks are available; set `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` to write the `*_ThemeConfig.g.cs` file under `obj/`.

## 3. Basic Setup / Registration

`[ThemeConfig]` is applied to the class that owns the themed properties. Each attribute names one property, one converter and two to seven theme types, with one value array per theme. `Light` and `Dark` ship in `VeloxDev.DynamicTheme` and implement `ITheme`, so they can be used as-is; a custom theme is an empty `public sealed class Ocean : ITheme { }`.

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
        InitializeTheme();   // required, and after any InitializeComponent() call
    }

    partial void OnThemeChanged(Type? oldValue, Type? newValue)
        => Console.WriteLine($"theme: {oldValue?.Name} -> {newValue?.Name}");
}
```

`BrushConverter` is the WPF adapter's `IThemeValueConverter`; it turns `"#ffffff"` into a `SolidColorBrush`. The generated `InitializeTheme()` registers this instance and applies the current theme's values.

**Expected result:** constructing `ThemedWindow` makes its `Background` and `Foreground` match `ThemeManager.Current`, which defaults to `Dark`.

## 4. Core Usage (Step by Step)

### 4.1 Select the platform interpolator

`ThemeManager` is in Core, so it cannot name the WPF sampler set. Supply the adapter's `Interpolator` once. Without it a switch still lands, but it jumps instead of animating.

```csharp
using VeloxDev.TransitionSystem;

ThemeManager.SetPlatformInterpolator(new Interpolator());
ThemeManager.StartModel = StartModel.Cache;   // start from the cached theme value, not the live property
```

**Expected result:** the call returns; a later `Transition<T>` produces frames. `StartModel.Cache` is also the default.

### 4.2 Animated versus jump switching

`Transition<T>(effect)` samples every registered target through the effect. `Jump<T>()` writes every end value immediately and does not need an interpolator.

```csharp
if (ThemeManager.Current == typeof(Dark))
{
    ThemeManager.Transition<Light>(TransitionEffects.Theme);   // 0.46 s animated switch
}
else
{
    ThemeManager.Jump<Dark>();                                 // immediate
}
```

`TransitionEffects.Theme` is a shared WPF effect (`Duration = 0.46 s`). It is read per frame, so do not mutate it while a switch is running. `TransitionEffects.Hover` (0.32 s) is the pointer-hover default; `Empty` has zero duration.

**Expected result:** the animated call fades `Background` and `Foreground` to the target values and only then raises `OnThemeChanged`; the jump call writes them in one step and raises the callback immediately.

### 4.3 One shared timeline per switch

Every target of one switch is anchored to a single timeline. `Transition.Pause`, `Resume` and `SetRate` on any one target therefore move the whole switch; `Seek` re-anchors only that target's runs, and `Exit` cancels only that target's runs.

```csharp
Transition.Pause(window, IncludeMutual: true, IncludeNoMutual: true);
Transition.Resume(window, IncludeMutual: true, IncludeNoMutual: true);
```

**Expected result:** pausing during a theme fade freezes every themed object at the same progress; resuming continues all of them.

### 4.4 Per-instance overrides

The generated `SetThemeValue<T>` writes an override for one instance and one theme; `RestoreThemeValue<T>` removes it and re-applies the declared value. `GetStaticThemeCache()` and `GetActiveThemeCache()` expose the declared and overridden maps.

```csharp
window.SetThemeValue<Light>(nameof(Background), Brushes.White);
window.RestoreThemeValue<Light>(nameof(Background));
```

**Expected result:** while `Light` is current, the override wins; restoring it returns the property to `#ffffff`.

### 4.5 Hooks and lifetime

`OnThemeChanging` runs before the switch starts and `OnThemeChanged` after it lands. Registration is weak: `ThemeManager` holds `WeakReference<IThemeObject>`, so an object that is no longer referenced is removed on the next switch. Call `InitializeTheme()` again only for a new instance.

**Expected result:** a closed window is not kept alive by the theme manager and is skipped by the next switch.

## 5. Verification

Run the complete program. The window opens dark; every two seconds it fades to the other theme. The console prints one `theme: Dark -> Light` or `theme: Light -> Dark` line per landed switch. Clicking is not required; the timer exercises both `Transition<T>` and the shared timeline.

## 6. Complete Code

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

The declaration pattern and the `Transition`/`Jump` pair are taken from `Examples/Theme/WPF Trimmed/Demo/MainWindow.xaml.cs`; the larger tile demo at `Examples/Theme/WPF/Demo/MainWindow.xaml.cs` adds the shared-timeline transport.

## 7. Run Declaration

- ⚠️ Not actually run — statically verified only on 2026-11-25. Verified against `Src/Core/VeloxDev.Core/DynamicTheme/ThemeConfigAttribute.cs`, `ThemeManager.cs`, `Src/Generators/VeloxDev.Core.Generator/Theme.cs`, `Src/Adapters/VeloxDev.WPF/TransitionSystem/TransitionEffects.cs` and `Src/Adapters/VeloxDev.WPF/DynamicTheme/ThemeValueConverters.cs`, plus both WPF theme demos. No window was launched in this environment.
