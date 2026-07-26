# Design Patterns — DynamicTheme

## Observer Pattern
ThemeManager notifies all registered IThemeObject instances when theme changes.

## Strategy Pattern
StartModel (Reflect/Cache) determines how initial values are resolved before animation.

## Adapter Pattern
IThemeValueConverter adapts raw values (Color, double) to platform types (Brush, Thickness).

## Singleton Pattern
ThemeManager is a static singleton managing global theme state.
