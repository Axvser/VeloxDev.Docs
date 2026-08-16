# Data Flow — Dynamic Theme

## Registration Flow (`InitializeTheme`)

The source-generated `InitializeTheme()` registers the type's theme properties in `ThemeCache`, registers the instance with `ThemeManager`, and applies the current theme's values.

```plantuml
@startuml
!theme plain

actor User as User
participant "MainWindow\n(generated IThemeObject)" as TO
participant "ThemeCache" as TC
participant "ThemeManager" as TM

User -> TO: InitializeTheme()
activate TO

TO -> TC: RegisterType(typeof(MainWindow), properties)
activate TC
TC --> TO: cached (duplicate ignored)
deactivate TC

TO -> TM: Register(this)
activate TM
TM -> TM: _act_cache.Add(this, [])\nactiveThemes.Add(new WeakReference(this))
TM --> TO: registered
deactivate TM

TO -> TO: apply current theme values (Current = Dark)
TO --> User: ready
deactivate TO
@enduml
```

> Source: generated code shape from `VeloxDev.Generators.Theme`; registration backing code in `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (`Register`) and `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs` (`RegisterType`).

## Animated Theme Switch (`Transition<T>`)

`ThemeManager.Transition` validates the target theme, cancels any running transition, prunes dead `WeakReference`s, pre-computes all interpolation frames, then applies them frame by frame on a timer.

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM
participant "ThemeCache" as TC
participant "InterpolatorCore" as IK
participant "IThemeObject" as TO
participant "PropertyInfo" as PI

User -> TM: Transition<Light>(TransitionEffects.Theme)
activate TM

note right of TM
  steps = Duration / (1000 / FPS)
  deltaTime = Duration / steps
end note

TM -> TM: CancleTransition()
TM -> TM: prune dead WeakReferences

TM -> TO: ExecuteThemeChanging(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanging)
deactivate TO

loop each registered object, each themed property
    TM -> IK: TryGetInterpolator(propertyType, out interp)
    activate IK
    IK --> TM: interp or null
    deactivate IK

    alt interpolator found
        TM -> TC: TryGetDefaultValue(type, prop, Dark, out start)\nor active cache value
        activate TC
        TC --> TM: start value (Cache) / live value (Reflect)
        deactivate TC
        TM -> IK: Interpolate(start, end, steps)
        activate IK
        IK --> TM: frames[] (eased by EaseCalculator)
        deactivate IK
    else no interpolator
        note right of TM
          simple two-frame switch: current -> target
        end note
    end
end

loop every frame (delay deltaTime)
    TM -> PI: SetValue(target, frame[i])
    activate PI
    PI --> TM: property updated
    deactivate PI
end

TM -> TM: Current = typeof(Light)
TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanged)
deactivate TO

TM --> User: return
deactivate TM
@enduml
```

> Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Transition` (lines 83–106), `CalculateFrames` (153–407), `ExecuteTransition` (414–452). Interpolation via `InterpolatorCore.TryGetInterpolator` and `IValueInterpolator.Interpolate`.

## Instant Theme Switch (`Jump<T>`)

`Jump` reuses the same frame pipeline with `steps = 1` and `deltaTime = 0`, so every property is set directly to the target value.

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM
participant "IThemeObject" as TO

User -> TM: Jump<Light>()
activate TM

TM -> TO: ExecuteThemeChanging(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanging)
deactivate TO

TM -> TM: CalculateFrames(steps = 1, Eases.Default)
TM -> TM: set each property to target theme value (no interpolation)
TM -> TM: Current = typeof(Light)

TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanged)
deactivate TO

TM --> User: return
deactivate TM
@enduml
```

> Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Jump(Type)` (lines 121–143).

## Error / Edge Paths

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM

== Invalid theme type (not an ITheme) ==
User -> TM: Transition(typeof(object), effect)
activate TM
TM -> TM: typeof(ITheme).IsAssignableFrom(typeof(object)) == false
TM -> TM: Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")
TM --> User: return (no-op)
deactivate TM

== themeType == Current ==
User -> TM: Transition<Dark>(effect)
activate TM
TM -> TM: themeType == Current  → aborted early
TM -> TM: Debug.WriteLine("[ThemeManager] Invalid theme type, jumping to current theme.")
TM --> User: return (no-op)
deactivate TM

== Zero-duration effect ==
User -> TM: Transition<Light>(TransitionEffects.Empty)
activate TM
note right of TM
  steps = 0 → clamped to 1
end note
TM -> TM: apply final values, Current = typeof(Light)
TM --> User: return
deactivate TM
@enduml
```

## Normal vs. Edge Path Summary

| Scenario | Behavior |
|---|---|
| Normal animated switch | Interpolate each registered object's themed properties over `Duration`, then set `Current` and fire `OnThemeChanged`. |
| `themeType == Current` | Aborted early — debug message "Invalid theme type, jumping to current theme." |
| `themeType` not assignable to `ITheme` | Aborted early with the same debug message. |
| Property without an interpolator | Falls back to a simple two-frame switch (`current` for every frame but the last, `target` for the last); `Jump`/`SetThemeValue` still set the final value. |
| Target theme has no configured value for a property | `CalculateFrames` logs "No target value found" and skips that property for the transition. |
| `steps <= 0` (zero-duration effect) | Clamped to `steps = 1`, so the theme still applies. |

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (lines 83–106 `Transition`, 121–143 `Jump`, 153–407 `CalculateFrames`, 414–452 `ExecuteTransition`), `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`.
