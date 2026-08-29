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

`ThemeManager.Transition` validates the target theme, cancels any running transition, prunes dead `WeakReference`s, prepares per-property samplers, then samples them in a Stopwatch-driven loop over the effect's duration.

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
  durationMs = effect.Duration.TotalMilliseconds
  sampling loop: rawT = stopwatch.Elapsed / durationMs
end note

TM -> TM: CancleTransition()
TM -> TM: prune dead WeakReferences

TM -> TO: ExecuteThemeChanging(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanging)
deactivate TO

loop each registered object, each themed property
    TM -> IK: TryGetInterpolator(propertyType, out sampleable)
    activate IK
    IK --> TM: ISampleable? or null
    deactivate IK

    alt sampleable found (registered native / self-ISampleable)
        TM -> TC: TryGetDefaultValue(type, prop, Dark, out start)\nor active cache value
        activate TC
        TC --> TM: start value (Cache) / live value (Reflect)
        deactivate TC
        TM -> TM: sampler = sampleable.Normalize(current, targetValue, options)
    else no sampleable
        note right of TM
          simple switch: hold current value, jump to target at the end
        end note
    end
    TM -> TM: TransitionEntry(target, property, sampler, current, targetValue)
end

TM -> TM: stopwatch = Stopwatch.StartNew()

loop until rawT >= 1 (Stopwatch-driven, 1ms coarse yield)
    TM -> TM: rawT = elapsed / durationMs  (clamped to [0,1])
    TM -> TM: easedT = clamp(Ease(rawT), 0, 1)
    loop each TransitionEntry
        alt rawT >= 1 (end)
            TM -> PI: SetValue(target, targetValue)
        else sampler == null
            note right of TM
              hold current value (no write)
            end note
        else
            TM -> TM: sampler.Update(target, property, current, targetValue, null, easedT)
        end
        activate PI
        PI --> TM: property updated (written inside Update)
        deactivate PI
    end
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

> Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Transition`, `PrepareSamplers`, `ExecuteTransition`. Sampler resolution via `InterpolatorCore.TryGetInterpolator`; `Normalize` in `PrepareSamplers`; per-sample writes via `ISampler.Update`.

## Instant Theme Switch (`Jump<T>`)

`Jump` runs the same sampler pipeline with a zero duration (`durationMs = 0`), so the first sample has `rawT = 1` and every property is set directly to the target value.

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

TM -> TM: PrepareSamplers(actives, themeType)
TM -> TM: ExecuteTransition(entries, Eases.Default, 0d, themeType)\n(rawT = 1 immediately → each property set directly to target value)
TM -> TM: Current = typeof(Light)

TM -> TO: ExecuteThemeChanged(old=Dark, new=Light)
activate TO
TO --> TM: (fires OnThemeChanged)
deactivate TO

TM --> User: return
deactivate TM
@enduml
```

> Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Jump(Type)`.

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
  durationMs = 0 → rawT = 1 on the first sample
end note
TM -> TM: apply final values (end-value writes), Current = typeof(Light)
TM --> User: return
deactivate TM
@enduml
```

## Normal vs. Edge Path Summary

| Scenario | Behavior |
|---|---|
| Normal animated switch | Prepare per-property samplers (`Normalize`), then drive each registered object's themed properties over `Duration` (Stopwatch-driven, eased + clamped) via `ISampler.Update`, then set `Current` and fire `OnThemeChanged`. |
| `themeType == Current` | Aborted early — debug message "Invalid theme type, jumping to current theme." |
| `themeType` not assignable to `ITheme` | Aborted early with the same debug message. |
| Property without a sampleable | Falls back to a simple switch (the current value is held for the whole pass, the target value is written on the final sample); `Jump`/`SetThemeValue` still set the final value. |
| Target theme has no configured value for a property | `PrepareSamplers` logs "No target value found" and skips that property for the transition. |
| Zero-duration effect (`durationMs = 0`) | `rawT = 1` on the first sample, so every property is written directly to its target value; the theme still applies. |

> Source references: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` (`Transition`, `Jump`, `PrepareSamplers`, `ExecuteTransition`), `Src/Core/VeloxDev.Core/DynamicTheme/ThemeCache.cs`.
