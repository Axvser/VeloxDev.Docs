# Dynamic Theme — Verify & Complete Code

## 1. Verify with the minimal demo

`Examples/Theme/WPF Trimmed/Demo` and `Examples/Theme/Avalonia Trimmed/Demo` are the minimal shape of the feature: one window, two mapped properties, one toggle button. The WPF window maps `Background` and `Foreground` and its button (`Content="反转主题"`, `Click="ChangeTheme"`) calls `ReverseThemeWithAnimation()`:

```bash
dotnet run --project "Examples/Theme/WPF Trimmed/Demo"
```

Click the button and check the four behaviours the Quick Start builds up, in one window:

- the window's mapped colours interpolate **smoothly** to the other theme over `TransitionEffects.Theme` (0.46 s) — the `Transition<Light/Dark>` path;
- replacing that call with `Jump<Light/Dark>()` (the demo's `ReverseThemeWithOutAnimation`) applies the same colours **instantly**;
- the generated `partial void OnThemeChanged(Type? oldValue, Type? newValue)` fires after each landed switch (the WPF demo shows a message box, the Avalonia one a window notification);
- `SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" })` and `RestoreThemeValue<Light>(...)` (the demo's `ThemeValueEx`) change and put back one value for one theme.

The Avalonia twin builds and runs the same way, with `[ThemeConfig<ObjectConverter, Dark, Light>]` (theme order `Dark, Light`) and bindings through `RelativeSource AncestorType=views:MainWindow`.

**Expected result:** the window recolours on every click — smoothly on `Transition`, instantly on `Jump` — and the callback appears each time.

## 2. Verify with the scale demo

`Examples/Theme/WPF/Demo` and `Examples/Theme/Avalonia/Demo` are the same scenario at a scale where the shared timeline becomes visible: a thousand tiles, the timeline control toolbar, and a live readout (see [Control a Switch in Flight](../03_switch-at-runtime/02_control-the-switch/index.md)). Both also run the scenario headlessly:

```bash
dotnet run --project "Examples/Theme/WPF/Demo" -- bench
```

`BenchRunner` repeats an animated switch and a `Jump` over 1, 50, 200 and 1000 elements, three times each, once with the tiles in the visual tree and once outside it, then writes a TSV table to `%TEMP%\veloxdev-theme-scale.tsv`. `prep_ms` is the synchronous part of the `Transition<T>` call — everything the switch does before its first frame — and it is the part that scales with the element count. `anim_ms` is the rest, and it does not: every element of a switch is anchored to one timeline, so a hundred targets and a thousand reach the end in the same wall time.

Measured on 2026-09-13 (WPF, 300 ms effect, tiles attached; the full run covers all four sizes):

| size | attached | jump_ms | prep_ms | anim_ms | frames | frames_per_target |
|---|---|---|---|---|---|---|
| 1 | True | 0.7 | 0.2 | 329.2 | 14 | 14 |
| 200 | True | 0.6 | 1.7 | 316.8 | 2800 | 14 |
| 1000 | True | 7.2 | 11.7 | 341.5 | 12091 | 12 |

The Avalonia demo's run has the same shape (1000 elements: `jump_ms` 1.9, `prep_ms` 8.2, `anim_ms` 320.4). The `attached = False` rows place the tiles outside the visual tree, so no layout or render work happens; the gap between the two sets of rows is the host's rendering cost, not the theme system's. `frames_per_target` staying near the effect's frame budget at every size is the same shared-timeline fact seen from the other side.

**Expected result:** the command prints the path of the TSV file, the table has one row per (size, attached, repetition), and `prep_ms` grows with `size` while `anim_ms` stays near the effect's duration.

## 3. Verify with the automated tests

The engine contract is pinned by two files under `Src/Core/VeloxDev.Core.Test/DynamicTheme/`:

`ThemeBasicsTests.cs` — the static model:

- `Dark_ImplementsITheme` / `Light_ImplementsITheme` — both built-in themes implement `ITheme`.
- `ThemeManager_DefaultCurrent_IsDark` — `ThemeManager.Current` starts as `typeof(Dark)`.
- `ThemeManager_SetCurrent_Changes` — `ThemeManager.SetCurrent<Light>()` flips `Current`.
- `StartModel_DefaultIsCache` / `StartModel_FlagsEnum` — `StartModel` defaults to `Cache` and is a `[Flags]` enum.
- `ThemeConfigAttribute_2Themes_CanBeInstantiated` — the 2-theme attribute constructs with two context arrays.

`ThemeTransitionTests.cs` — the switch runs on the transition system:

- `Switch_LandsExactlyOnTheTargetValue` — the last frame is pinned to the declared end value.
- `Switch_EveryTargetIsAnchoredToTheSameTimeline` — pausing one target pauses all of them.
- `Switch_SeekIsReachableAndFinishesThePass` — a seek past the end finishes the pass on the endpoint.
- `Switch_HonoursAutoReverseAndLoopTime` — the effect's own flags are honoured.
- `Switch_HoldsAnUnsampledPropertyUntilTheEnd` — a property with no sampler holds its value, then jumps.
- `Switch_WithNoPlatformSeam_AppliesImmediately` — no scheduler means an instant switch, not a stalled one.
- `Jump_WritesTheTargetValue` / `Jump_SkipsAnUnregisteredTarget` — `Jump` writes the target value and ignores unregistered objects.

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"
```

**Expected result:** all 15 DynamicTheme tests pass.

## 4. Complete code

A single-file, self-contained WPF program (no XAML): create an empty project (`dotnet new console -n DynamicThemeQuickStart`), add WPF via the target framework, then replace the project file and `Program.cs`. It declares two themed properties on a `Window` and toggles them through `ThemeManager`:

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

Every identifier is defined above or in the referenced packages: the two `[ThemeConfig]` rows map `Background` (`Light` = white, `Dark` = near-black) and `Foreground` (`Light` = near-black, `Dark` = white); `OnLoaded` registers the window, installs the adapter `Interpolator` and selects the start model; the button toggles between `Dark` and `Light` over `TransitionEffects.Theme` (0.46 s). The minimal demo in the repository has the same shape plus `Jump<T>`, `SetThemeValue` / `RestoreThemeValue` and the two cache getters; the scale demos add the tile collection, the timeline toolbar and the bench mode.

## 5. Run declaration

- ✅ **Built and measured on 2026-09-13.** Recorded outputs:
    - `dotnet build "Examples/Theme/WPF Trimmed/Demo/Demo.csproj" -c Debug` — `已成功生成。 0 个警告 0 个错误`.
    - `dotnet build "Examples/Theme/Avalonia Trimmed/Demo/Demo.csproj" -c Debug` — same, 0 warnings / 0 errors.
    - `dotnet build "Examples/Theme/WPF/Demo/Demo.csproj" -c Debug` and `dotnet build "Examples/Theme/Avalonia/Demo/Demo.csproj" -c Debug` — both 0 warnings / 0 errors.
    - `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"` — `已通过! - 失败: 0，通过: 15，已跳过: 0，总计: 15` on `net10.0`.
    - `dotnet run --project "Examples/Theme/WPF/Demo" -- bench` and the Avalonia equivalent — both completed and printed `%TEMP%\veloxdev-theme-scale.tsv`; the numbers in section 2 are read from those files.
    - The single-file program above was compile-verified against the current `VeloxDev.WPF` adapter source on `net9.0-windows` (**0 errors / 0 warnings**) and smoke-launched: the `Loaded` theme-initialization path (`InitializeTheme`, `SetPlatformInterpolator`) ran without exception and the window stayed up.
- ⚠️ **Not interactively clicked.** The button handlers of the demos were not driven by hand; the animated and instant switches were exercised through the demos' own automated `bench` mode, which calls `ThemeManager.Transition` and `ThemeManager.Jump` directly and waits for `ThemeManager.Current` to advance. Observing a click in the running window is left as the reader's end-to-end check.
