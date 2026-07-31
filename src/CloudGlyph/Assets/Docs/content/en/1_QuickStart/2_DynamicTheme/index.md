# Dynamic Theme — Quick Start

This guide walks you through adding **runtime theme switching with animated transitions** to a VeloxDev-based editor. You will decorate a window with per-theme property values, switch between `Light` and `Dark` at runtime — with or without a smooth animation — and override individual theme values on the fly.

> Demo source: `Examples/Theme/WPF/Demo` and `Examples/Theme/Avalonia/Demo`

## 1. Install / Add Dependency

Add the adapter package matching your GUI framework. The theme converters and interpolators live in the adapter, so you only need one reference:

```bash
# WPF
dotnet add package VeloxDev.WPF

# Avalonia
dotnet add package VeloxDev.Avalonia
```

## 2. Basic Setup / Registration

**Step 1 — Declare per-theme values with `[ThemeConfig]`.** Each attribute maps one property to one value per theme. The generic arguments are `<TConverter, TTheme1, TTheme2, ...>`; the string array after the property name is the value for each theme in order.

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
{
    // class body ...
}
```

The `VeloxDev.Generators.Theme` source generator turns the attributes into an `IThemeObject` implementation (`InitializeTheme`, `SetThemeValue<T>`, callbacks, ...).

**Step 2 — Initialize and register.** Call `InitializeTheme()` **after** `InitializeComponent()`. Then, if you want animated switching, install the adapter's interpolator and pick the start model:

```csharp
private void LoadTheme()
{
    InitializeTheme(); // must run after InitializeComponent()

    // Required only for animated theme switching
    ThemeManager.SetPlatformInterpolator(new Interpolator());

    // Start each animation from the cached theme value (Cache) or
    // from the object's current property value via reflection (Reflect)
    ThemeManager.StartModel = StartModel.Cache;
}
```

## 3. Core Usage (Step by Step)

**Switch theme with animation** — the property values interpolate frame by frame over the effect's duration and easing:

```csharp
private static void ReverseThemeWithAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
        ThemeManager.Transition<Light>(TransitionEffects.Theme);
    else
        ThemeManager.Transition<Dark>(TransitionEffects.Theme);
}
```

**Switch theme instantly** (no animation):

```csharp
private static void ReverseThemeWithOutAnimation()
{
    var condition = ThemeManager.Current == typeof(Dark);
    if (condition)
        ThemeManager.Jump<Light>();
    else
        ThemeManager.Jump<Dark>();
}
```

**React to theme changes** — implement the generated `partial void OnThemeChanged`:

```csharp
partial void OnThemeChanged(Type? oldValue, Type? newValue)
{
    MessageBox.Show($"Theme changed from {oldValue?.Name} to {newValue?.Name}");
}
```

**Override individual theme values at runtime**, then restore them:

```csharp
private void ThemeValueEx()
{
    SetThemeValue<Light>(nameof(Background), new object?[] { "#ffffff" });
    RestoreThemeValue<Light>(nameof(Foreground));

    var staticCache = GetStaticThemeCache();   // per-type default values
    var dynamicCache = GetActiveThemeCache();  // runtime overrides
}
```

## 4. Verification

Run the app and switch themes:

- The window background/foreground changes **smoothly** when using `Transition<T>` (the `TransitionEffects.Theme` effect runs for 0.46 s at 60 FPS).
- `Jump<T>` swaps instantly.
- The `OnThemeChanged` callback fires after each switch and shows a message box.
- Overriding `Background` via `SetThemeValue<Light>` is reflected immediately, and `RestoreThemeValue` reverts to the theme default.

## 5. Complete Code

A minimal WPF example (`MainWindow.xaml.cs`):

```csharp
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Background), ["#ffffff"], ["#1e1e1e"])]
[ThemeConfig<BrushConverter, Light, Dark>(nameof(Foreground), ["#1e1e1e"], ["#ffffff"])]
public partial class MainWindow
{
    public MainWindow()
    {
        InitializeComponent();
        LoadTheme();
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
```

> **Note:** the Avalonia demo uses the same shape, with `ObjectConverter` and theme order `Dark, Light`. XAML binds themed properties via `RelativeSource AncestorType=Window` (WPF) or `RelativeSource AncestorType=views:MainWindow` (Avalonia).
