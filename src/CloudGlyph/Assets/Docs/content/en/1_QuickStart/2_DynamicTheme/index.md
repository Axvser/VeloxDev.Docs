# DynamicTheme — Quick Start

VeloxDev DynamicTheme provides runtime theme switching with smooth animated transitions between light and dark themes.

## Setup

```csharp
using VeloxDev.DynamicTheme;

// Register platform interpolator (once at startup)
ThemeManager.SetPlatformInterpolator(new VeloxDev.Avalonia.Interpolator());
```

## Define a Theme

```csharp
public class MyDarkTheme : ITheme
{
	public Color Background => Color.FromRgb(30, 30, 30);
	public Color Foreground => Colors.White;
}

public class MyLightTheme : ITheme
{
	public Color Background => Colors.White;
	public Color Foreground => Colors.Black;
}
```

## Register Elements

```csharp
public class MyControl : IThemeObject
{
	public Color Background { get; set; }
}

ThemeManager.Register(myControl);
```

## Switch Themes

```csharp
// Switch to dark theme with animation
ThemeManager.Set<MyDarkTheme>();

// Switch without animation
ThemeManager.SetCurrent<MyDarkTheme>();
```

## Platform-Specific Theme Values

Each platform adapter provides value converters (e.g., `Brush`, `Thickness`) to translate raw theme values into UI-specific types.
