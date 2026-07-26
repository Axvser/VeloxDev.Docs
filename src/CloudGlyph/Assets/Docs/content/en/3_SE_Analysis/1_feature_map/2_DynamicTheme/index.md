# Feature Map — DynamicTheme

## Features

1. **Theme Definition** — Classes implementing ITheme define color palettes and constants
2. **Element Registration** — IThemeObject elements register with ThemeManager
3. **Animated Switching** — Theme changes use TransitionSystem for smooth animation
4. **Value Conversion** — IThemeValueConverter adapts to platform-specific types
5. **Caching** — Values cached for performance (StartModel.Cache vs Reflect)
