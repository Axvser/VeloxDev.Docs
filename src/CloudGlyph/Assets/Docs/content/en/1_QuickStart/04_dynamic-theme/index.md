# Dynamic Theme — Quick Start

## Dynamic Theme

Dynamic Theme brings **runtime theme switching with animated transitions** to a VeloxDev-based editor. You declare per-theme values on your controls or view models with `[ThemeConfig]`, then switch between `Light` and `Dark` at runtime — smoothly (`Transition<T>`) or instantly (`Jump<T>`). The property values are interpolated frame by frame by the TransitionSystem engine, while the platform adapter supplies the value converters and the `Interpolator`.

> Evidence: demo projects `Examples/Theme/WPF/Demo` and `Examples/Theme/Avalonia/Demo`, plus the test suite `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`.

### Quick Start

#### 1. Prerequisites

- **Supported targets** (from `VeloxDev.Core.csproj`, `VeloxDev.WPF.csproj`, `VeloxDev.Avalonia.csproj`): core `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0`; WPF adapter `netframework4.6.1` / `net5.0-windows` / `netcoreapp3.0`; Avalonia adapter `netstandard2.0` / `net6.0`.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+); C# 12 collection expressions appear in attribute arguments in the demos (needs `LangVersion` 12 / SDK 8.0+) — a *tested* example note, not a library requirement.
- **Package manager:** NuGet / `dotnet` CLI.
- **Required services:** a UI adapter for your GUI framework — `VeloxDev.WPF` or `VeloxDev.Avalonia` — plus its `Interpolator` (from `VeloxDev.TransitionSystem`) for animated switches.


#### 2. Install / Add Dependency

Add the core package and the adapter matching your GUI framework. The value converters and the platform `Interpolator` live in the adapter, so referencing the adapter alone is sufficient in practice (the WPF demo does exactly that via a project reference to `VeloxDev.WPF`).

```bash
dotnet add package VeloxDev.Core      # core engine: ThemeManager, ThemeCache, [ThemeConfig]
dotnet add package VeloxDev.WPF       # WPF   adapter (or VeloxDev.Avalonia for Avalonia)
```

**Expected result:** the packages appear in your `.csproj` `<ItemGroup>`, and `dotnet restore` exits with code 0.

#### 3. Basic Setup / Registration

Decorate your control or view-model class with `[ThemeConfig<...>]`, then call the source-generated `InitializeTheme()` **after** `InitializeComponent()`. If you want animated switches, install the adapter's `Interpolator` and choose the animation start model.

```csharp
public partial class MainWindow
{
    private void LoadTheme()
    {
        InitializeTheme(); // must run after InitializeComponent()

        // Required only for animated theme switching
        ThemeManager.SetPlatformInterpolator(new Interpolator());

        // Start each animation from the cached theme value (Cache) or
        // from the object's current property value via reflection (Reflect)
        ThemeManager.StartModel = StartModel.Cache;
    }
}
```

The `VeloxDev.Generators.Theme` source generator turns every `[ThemeConfig]` on the class into an `IThemeObject` implementation: it registers the class with `ThemeCache`, calls `ThemeManager.Register(this)`, and applies the current theme's values.

**Expected result:** the instance is registered with `ThemeManager`; `ThemeManager.Current == typeof(Dark)` by default (verified by `ThemeBasicsTests.ThemeManager_DefaultCurrent_IsDark`).

#### 4. Core Usage (Step by Step)

**Step 1 — declare per-theme values.** Each `[ThemeConfig]` maps one property to one value per theme. Generic arguments are `<TConverter, TTheme1, TTheme2, ...>`; the arrays after the property name are the values for each theme in order.

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
{
    // members shown in Step 2, Step 3 and Complete Code below
}
```

**Expected result:** the generator emits an `IThemeObject` implementation (`InitializeTheme`, `SetThemeValue<T>`, callbacks) on the class; the class can be registered with `ThemeManager`.

**Step 2 — switch with animation.** The property values interpolate frame by frame over the effect's duration and easing.

```csharp
private static void ReverseThemeWithAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    else
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
}
```

**Expected result:** the window background/foreground animates smoothly over `TransitionEffects.Theme` (`Duration = 0.46 s`, 60 FPS) and `OnThemeChanged` fires afterwards.

**Step 3 — switch instantly.** No interpolation; every property is set directly to the target theme value.

```csharp
private static void ReverseThemeWithOutAnimation()
{
    if (ThemeManager.Current == typeof(Dark))
        ThemeManager.Jump<Light>();
    else
        ThemeManager.Jump<Dark>();
}
```

**Expected result:** the theme changes immediately with no animation; `OnThemeChanged` fires with `(oldValue, newValue)`.

#### 5. Verification

Run the Theme demo (`Examples/Theme/WPF/Demo` or `Examples/Theme/Avalonia/Demo`) and click the theme-toggle button:

- With `Transition<T>` the window background/foreground changes **smoothly** (the `TransitionEffects.Theme` effect runs for 0.46 s at 60 FPS).
- With `Jump<T>` the switch is **instant**.
- The generated `partial void OnThemeChanged(Type? oldValue, Type? newValue)` fires after each switch (a message box in the WPF demo).
- Runtime overrides via `SetThemeValue<Light>(nameof(Background), ...)` are reflected immediately; `RestoreThemeValue<Light>` reverts to the theme default.

#### 6. Complete Code

A minimal, complete WPF example — the code-behind `MainWindow.xaml.cs` (namespace `Demo`). The companion `MainWindow.xaml` declares a `Window` with a `Button Click="ChangeTheme"` bound to the `Background`/`Foreground` via `RelativeSource AncestorType=Window`:

```csharp
using System.Windows;
using VeloxDev.DynamicTheme;
using VeloxDev.TransitionSystem;

namespace Demo
{
    [ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
    [ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            LoadTheme();
        }

        private void ChangeTheme(object sender, RoutedEventArgs e)
        {
            ReverseThemeWithAnimation();
        }

        private void LoadTheme()
        {
            InitializeTheme();
            ThemeManager.SetPlatformInterpolator(new Interpolator());
            ThemeManager.StartModel = StartModel.Cache;
        }

        partial void OnThemeChanged(Type? oldValue, Type? newValue)
        {
            MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
        }

        private void ReverseThemeWithAnimation()
        {
            if (ThemeManager.Current == typeof(Dark))
                ThemeManager.Transition<Light>(TransitionEffects.Theme);
            else
                ThemeManager.Transition<Dark>(TransitionEffects.Theme);
        }

        private void ReverseThemeWithOutAnimation()
        {
            if (ThemeManager.Current == typeof(Dark))
                ThemeManager.Jump<Light>();
            else
                ThemeManager.Jump<Dark>();
        }
    }
}
```

> **Note:** the Avalonia demo has the same shape, but uses `ObjectConverter` and theme order `Dark, Light`, and binds via `RelativeSource AncestorType=views:MainWindow`. The complete code above is modeled on `Examples/Theme/WPF/Demo/MainWindow.xaml.cs`.

#### 7. Run Declaration

- ⚠️ Not actually run — statically verified only. The demo sources and tests were read in full (`Examples/Theme/WPF/Demo`, `Examples/Theme/Avalonia/Demo`, `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeBasicsTests.cs`), but the author did not compile and execute the sample in this session.
