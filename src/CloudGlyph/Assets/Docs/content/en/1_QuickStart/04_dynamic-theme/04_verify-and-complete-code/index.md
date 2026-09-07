# Dynamic Theme — Verify & Complete Code

## 1. Verify with the demos

Two GUI demos ship under `Examples/Theme/` (WPF and Avalonia), each a small window that toggles its mapped colors between themes. Launch one (e.g. `dotnet run --project Examples/Theme/WPF/Demo`) and click the theme-toggle button:

- The window's mapped properties (the WPF demo maps `Background`/`Foreground`) interpolate **smoothly** to the other theme over `TransitionEffects.Theme` (0.46 s) when `Transition<T>(...)` runs.
- `Jump<T>()` applies the same values **instantly** with no interpolation.
- The generated `partial void OnThemeChanged(Type? oldValue, Type? newValue)` fires after each switch (a message box in the WPF demo).
- Runtime overrides via `SetThemeValue<T>(nameof(...), new object?[] { ... })` are reflected immediately for the active theme; `RestoreThemeValue<T>` reverts to the static value.

**Expected result:** the window recolors on every click — smoothly on `Transition`, instantly on `Jump` — and the callback message appears each time.

## 2. Verify with the automated tests

The engine contract is pinned by `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`:

- `Dark_ImplementsITheme` / `Light_ImplementsITheme` — both built-in themes implement `ITheme`.
- `ThemeManager_DefaultCurrent_IsDark` — `ThemeManager.Current` starts as `typeof(Dark)`.
- `ThemeManager_SetCurrent_Changes` — `ThemeManager.SetCurrent<Light>()` flips `Current`.
- `StartModel_DefaultIsCache` / `StartModel_FlagsEnum` — `StartModel` defaults to `Cache` and is a `[Flags]` enum.
- `ThemeConfigAttribute_2Themes_CanBeInstantiated` — the 2-theme attribute constructs with two context arrays.

```bash
dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"
```

**Expected result:** all 7 DynamicTheme tests pass.

## 3. Complete code

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

Every identifier is defined above or in the referenced packages: the two `[ThemeConfig]` rows map `Background` (`Light` = white, `Dark` = near-black) and `Foreground` (`Light` = near-black, `Dark` = white); `OnLoaded` registers the window and installs the adapter `Interpolator`; the button toggles between `Dark` and `Light` over `TransitionEffects.Theme` (0.46 s). The demo in the repository (`Examples/Theme/WPF/Demo/MainWindow.xaml.cs`) has the same shape and additionally demonstrates `Jump<T>`, `SetThemeValue`/`RestoreThemeValue` and `GetStaticThemeCache`/`GetActiveThemeCache`. The Avalonia demo (`Examples/Theme/Avalonia/Demo`) mirrors the scenario with `[ThemeConfig<ObjectConverter, Dark, Light>]` (theme order `Dark, Light`) and binds through `RelativeSource AncestorType=views:MainWindow`.

## 4. Run declaration

- ⚠️ **Partially verified — the animated toggle was not interactively observed.** Recorded on 2026-09-07:
    - `dotnet build Examples/Theme/WPF/Demo/Demo.csproj -c Debug` — succeeded, **0 errors** (3 warnings in `VeloxDev.Core`'s TransitionSystem code, unrelated to DynamicTheme).
    - `dotnet test Src/Core/VeloxDev.Core.Test/VeloxDev.Core.Test.csproj --filter "FullyQualifiedName~DynamicTheme"` — **7 passed / 0 failed**.
    - The single-file program above was compile-verified against the current `VeloxDev.WPF` adapter source on `net9.0-windows` (**0 errors**) and smoke-launched: the `Loaded` theme-initialization path (`InitializeTheme`, `SetPlatformInterpolator`) ran without exception and the window stayed up. Actually clicking the button and observing the 0.46 s color transition is left as the reader's end-to-end check.
