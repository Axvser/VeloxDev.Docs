# Theme Manager

`ThemeManager` keeps the active theme, the weak set of registered theme objects, and the switch in flight. Namespace `VeloxDev.DynamicTheme`.

## VeloxDev.DynamicTheme

### Enum: StartModel

Selects the value a switch starts from.

**Signature:** `[Flags] public enum StartModel : int`

| Member | Value | Meaning |
|---|---|---|
| `Reflect` | 1 | Read the property's current value off the object. |
| `Cache` | 2 | Start from the cached value of the current theme. The default. |

### Class: ThemeManager

**Signature:** `public class ThemeManager`

**Properties**

| Member | Type | Default | Description |
|---|---|---|---|
| `Current` | `static Type { get; internal set; }` | `typeof(Dark)` | The active theme. The transition and jump paths advance it only after a switch lands. |
| `StartModel` | `static StartModel { get; set; }` | `StartModel.Cache` | How a switch obtains start values. |

**Methods**

| Member | Signature | Description |
|---|---|---|
| `SetPlatformInterpolator<T>` | `static void SetPlatformInterpolator<T>(T interpolator) where T : InterpolatorCore` | Supplies the adapter interpolator once. Without it a switch still lands, immediately and without animation. |
| `SetCurrent<T>` | `static void SetCurrent<T>() where T : ITheme` | Sets `Current` without touching any registered object. |
| `Register` | `static void Register(IThemeObject target)` | Adds a target, held weakly. Called by the generated `InitializeTheme`. |
| `Unregister` | `static void Unregister(IThemeObject target)` | Removes a target. |
| `Transition` | `static void Transition(Type themeType, ITransitionEffectCore effect)` | Animates every live target to `themeType`. |
| `Transition<T>` | `static void Transition<T>(ITransitionEffectCore effect) where T : ITheme` | The generic form. |
| `Jump` | `static void Jump(Type themeType)` | Writes every end value at once; no interpolator or effect needed. |
| `Jump<T>` | `static void Jump<T>() where T : ITheme` | The generic form. |

**Behavior notes**

- `Transition` is an `async void` surface: it returns before the animation ends. Callers observe completion through `OnThemeChanged` or the effect's `Completed` / `Finally` events.
- A new transition or jump cancels the previous switch. Targets that are no longer referenced are pruned before each switch; the registry is a `ConditionalWeakTable` / `WeakReference` set, so a closed window is not kept alive.
- Every target in one switch is anchored to a single shared timeline. `Transition.Pause`, `Resume` and `SetRate` on any one target move the whole switch; `Seek` re-anchors only that target's runs, and `Exit` cancels only that target's runs.
- The effect instance is read per frame by every target. Use a dedicated `TransitionEffect` per switch, or one of the shared `TransitionEffects` instances, and do not mutate it while a switch that uses it is running.
- A property whose value has no sampler (or whose path cannot be read) is skipped during the animation and written at the end; the degradation is reported through the effect's `Warn` event.
- `Current` stays unchanged when a switch is superseded or cancelled; the hooks `OnThemeChanged` do not run for a switch that did not land.

### Generated lifecycle hook order

| Step | Hook |
|---|---|
| A switch starts | `OnThemeChanging(oldTheme, newTheme)` |
| Animation (or jump) writes values | — |
| A switch lands | `OnThemeChanged(oldTheme, newTheme)`, then `ThemeManager.Current` has already been advanced |

## Example

```csharp
using System;
using System.Windows.Controls;
using VeloxDev.DynamicTheme;
using VeloxDev.TransitionSystem;

ThemeManager.SetPlatformInterpolator(new Interpolator());
ThemeManager.StartModel = StartModel.Cache;

// Animated switch.
ThemeManager.Transition<Light>(TransitionEffects.Theme);

// Immediate switch.
ThemeManager.Jump<Dark>();

// Whole-switch transport, addressed by any one target.
Transition.Pause(window, IncludeMutual: true, IncludeNoMutual: true);
Transition.SetRate(window, 0.5d, IncludeMutual: true, IncludeNoMutual: true);
Transition.Exit(window, IncludeMutual: true, IncludeNoMutual: true);
```

`Interpolator` and `TransitionEffects` are adapter types; see [Platform converters](../02_platform-converters/index.md) and, for the transition side, [Platform adapter types](../../12_transition-animation/04_platform-adapter-types/index.md).

## Error handling

The switch path catches its own failures. An exception from the scheduler or interpreter is written to `Debug` and the switch does not land (`Current` is not advanced, the changed hooks do not run). An invalid theme type — not assignable to `ITheme`, or equal to `Current` — is ignored and jumps to the current theme.
