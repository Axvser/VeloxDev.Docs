# DynamicTheme — API Reference

## Namespace: `VeloxDev.DynamicTheme`

### ThemeManager

| Member | Description |
|---|---|
| `Current` | Gets the active theme type (default: `Dark`) |
| `StartModel` | How to get initial values: `Reflect` or `Cache` |
| `SetPlatformInterpolator<T>(T)` | Register platform interpolator |
| `SetCurrent<T>()` | Switch theme without animation |
| `Set<T>(bool smooth = true)` | Switch theme with animation |
| `Register(IThemeObject)` | Register an element for theming |
| `Unregister(IThemeObject)` | Unregister an element |

### Interfaces

| Interface | Purpose |
|---|---|
| `ITheme` | Theme definition contract |
| `IThemeObject` | Makes an element theme-aware |
| `IThemeValueConverter` | Converts theme values to platform types |

### Key Types

| Type | Description |
|---|---|
| `Dark`, `Light` | Built-in theme definitions |
| `ThemeCache` | Manages cached theme property values |
| `ThemeConfigAttribute` | Marks a class as a theme definition |
