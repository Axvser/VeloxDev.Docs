# Data Flow — DynamicTheme

## Theme Switch Flow

1. User calls ThemeManager.Set<T>()
2. Resolve new theme type definition
3. Iterate all registered IThemeObject instances
4. For each property: read current value (StartModel: Reflect or Cache)
5. Compute target value from new theme definition
6. Create Transition snapshots via TransitionSystem
7. Execute all snapshots through TransitionScheduler
8. UI animates from old to new values
9. Update ThemeManager.Current
