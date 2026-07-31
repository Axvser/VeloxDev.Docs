# Data Flow — Dynamic Theme

## Animated Theme Switch (`Transition<T>`)

This is the core API call chain. `ThemeManager.Transition` pre-computes all interpolation frames, then applies them frame by frame on a timer.

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

TM -> IK: TryGetInterpolator(propertyType, out interp)
activate IK
IK --> TM: interp or null
deactivate IK

alt interpolator found
    TM -> TC: TryGetDefaultValue(type, prop, Dark, out start)
    activate TC
    TC --> TM: start value (Cache) or current property value (Reflect)
    deactivate TC
    TM -> IK: Interpolate(start, end, steps, options)
    activate IK
    IK --> TM: List<object?> frames (eased by EaseCalculator)
    deactivate IK
else no interpolator
    note right of TM
      property is skipped for animation
    end note
end

loop every frame (deltaTime delay)
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

## Instant Switch (`Jump<T>`)

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

TM -> TM: set each property to new theme value (no interpolation)
TM -> TM: Current = typeof(Light)

TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanged)
deactivate TO

TM --> User: return
deactivate TM
@enduml
```

## Runtime Value Override (`SetThemeValue<T>`)

```plantuml
@startuml
!theme plain

actor User as User
participant "IThemeObject (generated)" as TO
participant "ThemeCache" as TC

User -> TO: SetThemeValue<Light>(nameof(Background), new value)
activate TO

TO -> TC: GetOrCreateActiveEntry(this)
activate TC
TC --> TO: InstanceCache (overrides)
deactivate TC

TO -> TC: RegisterConverter / lookup converter for property
TO -> TO: convert raw value to platform type

TO -> TO: UpdatePropertyToCurrentTheme(Background)
TO --> User: property updated immediately
deactivate TO
@enduml
```

## Normal vs. Error Paths

| Scenario | Behavior |
|---|---|
| Normal animated switch | Interpolate each registered object's properties over `Duration`, then set `Current` and fire `OnThemeChanged`. |
| `themeType == Current` | Aborted early — debug message "Invalid theme type, jumping to current theme." |
| `themeType` not assignable to `ITheme` | Aborted early with the same debug message. |
| Property without an interpolator | Property skipped during animation; still set to the final value by `Jump`/`SetThemeValue`. |
| `steps <= 0` (zero-duration effect) | Clamped to `steps = 1`, so the theme still applies. |

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (lines 83–106 `Transition`, 153–407 `CalculateFrames`, 414–452 `ExecuteTransition`), `Src/Generators/VeloxDev.Core.Generator/Theme.cs`.
