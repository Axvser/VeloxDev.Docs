# Data Flow — Theme Switching

Both `Transition<T>` (animated) and `Jump<T>` (instant) follow the same pipeline: guard the target theme, notify `ExecuteThemeChanging`, prepare one sampler entry per property, run `ExecuteTransition`, update `Current`, then notify `ExecuteThemeChanged`. The only difference is the animation duration — `Jump` passes `durationMs = 0`.

## Animated Switch (`Transition<T>`)

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM
participant "IThemeObject\n(registered view)" as TO
participant "InterpolatorCore\n(static registry)" as IK
participant "ISampler" as SMP

User -> TM: Transition<Light>(TransitionEffects.Theme)
activate TM

note right of TM
  effect.Duration = 460 ms (TransitionEffects.Theme)
  effect.Ease drives easing of normalized time
end note

alt guard fails (themeType == Current\nor not assignable to ITheme)
    TM -> TM: Debug.WriteLine(...) and return (no-op)
else passes
    TM -> TM: CancleTransition()  // cancel a running pass
    TM -> TM: prune dead WeakReferences\nactives = alive IThemeObject[]

    loop each active
        TM -> TO: ExecuteThemeChanging(current = Dark, new = Light)
        activate TO
        TO -> TO: base chain + OnThemeChanging (user hook)
        deactivate TO
    end

    note right of TM
      PrepareSamplers(actives, typeof(Light))
    end note
    loop each active, each themed property
        TM -> TO: GetStaticThemeCache() / GetActiveThemeCache()
        activate TO
        TO --> TM: static values + runtime overrides
        deactivate TO
        alt StartModel.Cache
            TM -> TM: start = override[Current] ?? static[Current]
        else StartModel.Reflect
            TM -> TM: start = propertyInfo.GetValue(target)
        end
        TM -> TM: target = override[Light] ?? static[Light]
        TM -> IK: TryGetInterpolator(propertyType, out sampler)
        activate IK
        IK --> TM: ISampler or null
        deactivate IK
        TM -> TM: TransitionEntry(target, prop, sampler,\nnormStart, normEnd) via NormalizeStart/End
    end

    note right of TM
      ExecuteTransition(entries, effect.Ease, durationMs, themeType)
    end note
    TM -> TM: await _asyncLock_transition (serialize passes)\ncancel previous pass, new CancellationTokenSource

    loop until rawT >= 1
        TM -> TM: rawT = elapsed / durationMs (clamp [0,1])\napplyT = rawT >= 1 ? 1 : clamp(ease(rawT), 0, 1)
        loop each TransitionEntry
            alt sampler == null
                TM -> TM: hold current value;\nat end SetValue(target, targetValue)
            else
                TM -> SMP: InsertFrame(target, prop, ref working,\nstart, end, null, applyT)
                activate SMP
                SMP -> SMP: TransitionProperty.SetValue (compiled write)
                deactivate SMP
            end
        end
        TM -> TM: await Task.Delay(1)   // coarse ~1 ms yield
    end

    TM -> TM: Current = typeof(Light)   (only if not cancelled)
    loop each active
        TM -> TO: ExecuteThemeChanged(current = Dark, new = Light)
        activate TO
        TO -> TO: base chain + OnThemeChanged (user hook)
        deactivate TO
    end
    TM --> User: done
end
deactivate TM
@enduml
```

Notes:

- The entry list is prepared up front and holds one `TransitionEntry` per property: target, the compiled `TransitionProperty`, the resolved `ISampler` (or null), and the normalized start/end values.
- No frame list is built — sampling is Stopwatch-driven; each loop iteration yields via `Task.Delay(1)`, and the pass ends when `elapsed >= durationMs`. `FPS` on the effect is not consulted by this loop.
- If a second `Transition`/`Jump` starts while one is running, the earlier pass is cancelled through a `CancellationTokenSource` (`CancleTransition`), and only the winning pass updates `Current`. `ExecuteTransition` awaits a static `SemaphoreSlim` first, so passes never overlap.

## Instant Switch (`Jump<T>`)

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM
participant "IThemeObject\n(registered view)" as TO

User -> TM: Jump<Light>()
activate TM

alt guard fails
    TM -> TM: Debug.WriteLine(...) and return (no-op)
else passes
    TM -> TM: CancleTransition(); prune dead WeakReferences\nactives = alive IThemeObject[]
    loop each active
        TM -> TO: ExecuteThemeChanging(current = Dark, new = Light)
        activate TO
        TO -> TO: base chain + OnThemeChanging (user hook)
        deactivate TO
    end
    TM -> TM: entries = PrepareSamplers(actives, typeof(Light))
    note right of TM
      ExecuteTransition(entries, Eases.Default, 0d, themeType)
      durationMs = 0 => rawT = 1 on the first sample,
      so every property is written directly to its target.
    end note
    TM -> TM: Current = typeof(Light)
    loop each active
        TM -> TO: ExecuteThemeChanged(current = Dark, new = Light)
        activate TO
        TO -> TO: base chain + OnThemeChanged (user hook)
        deactivate TO
    end
    TM --> User: done
end
deactivate TM
@enduml
```

`Eases.Default` is the linear ease (`Ease(t) => t`), but it is never observed because the zero duration forces `applyT = 1` on the first sample.

## Guard Conditions & Edge Paths

| Scenario | Behavior |
|---|---|
| `themeType == Current` | Guard returns early with the debug message `[ThemeManager] Invalid theme type, jumping to current theme.` (no-op — it does not re-apply). |
| `themeType` not assignable to `ITheme` | Same guard, same no-op return. |
| Property type has a registered sampler | Endpoints are produced by `NormalizeStart`/`NormalizeEnd`; middle frames written by `ISampler.InsertFrame`. |
| Property type has no sampler | Simple switch: current value is held for the whole pass, target value is written on the final sample. |
| No value found for the property (start or target) | `PrepareSamplers` logs `... skipping` and omits that property from the pass. |
| New switch while one is running | Previous pass cancelled (`CancleTransition`); sampling serialized by the static `SemaphoreSlim`. |
| Zero-duration effect / `Jump` | `rawT = 1` on the first sample → every property set directly to its target value. |
| Dead registered object | Pruned at the start of the pass (weak references), then ignored. |

> Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Transition` lines 83-112, `Jump` lines 118-146, `PrepareSamplers` lines 148-303, `ExecuteTransition` lines 332-400.
