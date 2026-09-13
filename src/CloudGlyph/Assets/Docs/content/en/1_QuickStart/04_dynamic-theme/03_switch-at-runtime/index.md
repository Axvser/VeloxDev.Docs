# Dynamic Theme — Switch at Runtime

## Switching at runtime

Everything here happens after `InitializeTheme()` has registered your objects (see [Declare & Register](../02_declare-and-register/index.md)). A switch is global: it walks every registered `IThemeObject` and moves the properties those objects declared.

There are two ways to switch, and they differ in more than looks:

- `ThemeManager.Transition<T>(effect)` runs the switch as an **animation** on the TransitionSystem engine — the object values are produced frame by frame by the engine's sampling loop, and every target of one switch is anchored to a single shared timeline, so the transition system's own `Transition.Pause` / `Seek` / `SetRate` / `Exit` surface drives a theme switch unchanged.
- `ThemeManager.Jump<T>()` writes the target values **synchronously**, on the calling thread, with no timeline and no effect. It needs no platform interpolator at all.

Both paths notify the same hooks in the same order, and both refuse a switch to the theme that is already current.

- [00 Prepare an Animated Switch](00_prepare/index.md) — `SetPlatformInterpolator` (mandatory for animation), `StartModel`, the effect presets
- [01 Animated vs Instant Switching](01_transition-and-jump/index.md) — `Transition` / `Jump`, the generated hooks, `SetCurrent`
- [02 Control a Switch in Flight](02_control-the-switch/index.md) — one timeline per switch, `Pause` / `Resume` / `Seek` / `SetRate` / `Exit`
- [03 Runtime Overrides & Threading](03_overrides-and-threading/index.md) — `SetThemeValue` / `RestoreThemeValue`, the two caches, which thread a switch writes on
