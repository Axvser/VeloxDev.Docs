# Data Flow — Theme Switching

`Transition<T>` and `Jump<T>` no longer share a pipeline. An animated switch prepares a grouped entry set and then hands it to one platform `TransitionSchedulerCore` per target, all anchored to a single `ITimeSourceControl`, so the transition system owns the clock, the frame pacing and the effect's own flags. An instant switch never touches the transition system: `Jump` writes every end value and advances `Current` directly through `ApplyImmediately`, which is why it neither needs `SetPlatformInterpolator` nor is constrained by the platform's `ITransitionEffect<TPriority>`.

Both entry points share the same prologue — guard, cancel, prune, notify `ExecuteThemeChanging` — and both finish by notifying `ExecuteThemeChanged`, but only a switch that actually landed gets there.

## Animated Switch (`Transition<T>`)

```plantuml
@startuml
!theme plain

actor User as User
participant "ThemeManager" as TM
participant "IThemeObject\n(registered view)" as TO
participant "InterpolatorCore\n(platform adapter)" as IK
participant "TransitionSchedulerCore\n(one per target)" as SC
participant "TimeSourceCore\n(one per switch)" as TL
participant "ISampler" as SMP

User -> TM: Transition<Light>(effect)
activate TM

alt guard fails (themeType == Current\nor not assignable to ITheme)
    TM -> TM: Debug.WriteLine(...) and return (no-op)
else passes
    TM -> TM: CancelActiveSwitch()
    note right of TM
      Interlocked.Exchange(ref _activeSwitch, null), then per run:
      Run.Cts.Cancel() and Run.Timeline.Wake(). The wake is required -
      a loop parked on the timeline's pause gate cannot see the token.
    end note
    TM -> TM: activeThemes.RemoveAll(dead)\nactives = alive IThemeObject[]

    loop each active
        TM -> TO: ExecuteThemeChanging(current = Dark, new = Light)
        activate TO
        TO -> TO: base chain + OnThemeChanging (user hook)
        deactivate TO
    end

    note right of TM
      groups = PrepareSamplers(actives, typeof(Light))
      one TargetEntries per target, one TransitionEntry per property.
      No endpoint is normalized here and no sampler is resolved here.
    end note
    loop each active, each themed property
        TM -> TO: GetStaticThemeCache() / GetActiveThemeCache()
        activate TO
        TO --> TM: static defaults + runtime overrides
        deactivate TO
        alt StartModel.Cache
            TM -> TM: start = override[Current] ?? static[Current]
        else StartModel.Reflect
            TM -> TM: start = propertyInfo.GetValue(target)
        end
        TM -> TM: end = override[Light] ?? static[Light]
        TM -> IK: TryGetInterpolator(propertyType, out _)  // hasSampler probe
        activate IK
        IK --> TM: true or false
        deactivate IK
    end

    alt _interpolator is null, or groups is empty
        TM -> TM: ApplyImmediately(groups, typeof(Light))
    else some group has no scheduler
        loop each group
            TM -> IK: CreateScheduler(group.Target, effect)
            activate IK
            IK --> TM: TransitionSchedulerCore? (null = "not mine")
            deactivate IK
        end
        TM -> TM: ApplyImmediately(groups, typeof(Light))
    else every group got a scheduler
        TM -> TL: TimerCore.CreateTimeSource<ITimeSourceControl>()
        loop each (scheduler, group)
            TM -> TO: WriteStartValues(group)
            note right of TM
              The prepared start is written back first, so the default
              StartModel.Cache means "from the current theme's value",
              not "from whatever the target happens to hold".
            end note
            TM -> SC: Track(new TransitionRun(timeline))
            TM -> TM: BuildState(group) - end values only
        end
        TM -> TM: Interlocked.Exchange(ref _activeSwitch, runs)

        loop each run
            TM -> SC: Execute(interpolator, state, effect, run.Cts)
            activate SC
            SC -> IK: Prepare(target, state, effect, inspector)
            activate IK
            IK -> SMP: NormalizeStart / NormalizeEnd
            activate SMP
            SMP --> IK: normalized endpoints
            deactivate SMP
            deactivate IK
            loop until the run ends
                SC -> SMP: InsertFrame(target, property, ref working,\nstart, end, options, t)
                activate SMP
                SMP -> TO: TransitionProperty.SetValue (compiled write)
                deactivate SMP
                SC -> TL: sample the clock / await the pause gate
            end
            deactivate SC
        end

        note right of TM
          await Task.WhenAll(tasks) - the first await in Transition<T>,
          so the call's own duration is the synchronous preparation.
        end note
        loop each run (finally)
            TM -> SC: Untrack(run)
        end
        TM -> TM: Interlocked.CompareExchange(ref _activeSwitch, null, runs)
        TM -> TM: ApplyHeldValues(groups)\nCurrent = typeof(Light)
    end

    note right of TM
      RunSwitch returns false when the pass faulted or any run was
      cancelled. Nothing here runs in that case: no Current, no
      ExecuteThemeChanged.
    end note

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

- `PrepareSamplers` produces `TargetEntries` (private, one per target) holding `TransitionEntry` (private, one per property). An entry carries `Target`, `PropertyInfo`, the compiled `TransitionProperty`, `StartValue`, `EndValue` and `HasSampler`. A target that contributes no usable property gets no group at all — an empty animation and an empty sampler set are both meaningless.
- Only the **end** values are declared to the scheduler (`BuildState`), and only for entries whose `EndValue` is not null; a null end value means "this theme leaves the property alone". The start is read back off the target by `InterpolatorCore.Prepare`, so normalizing an endpoint in `PrepareSamplers` would normalize it twice.
- One timeline for the whole switch. Every target is anchored to it, which is why `Transition.Pause` / `Resume` / `Seek` / `SetRate` / `Exit` on **any single** target act on all of them, and why the switch's wall time does not grow with the element count. The frame pacing and the effect's `FPS`, `IsAutoReverse` and `LoopTime` are the transition system's (`ThemeTransitionTests.Switch_HonoursAutoReverseAndLoopTime`).
- Platform seams are resolved **before** anything is scheduled: if `_interpolator` is null, if no group has a movable property, or if any group's `CreateScheduler` returns null, the whole switch degrades to `ApplyImmediately` rather than animating a subset. `CreateScheduler` is only asked once per target per switch.
- `Track` must precede `Execute`: it is how the scheduler finds the run — and therefore the token — for the frame set it is about to build.
- `RunSwitch` is a private `async Task<bool>`: it returns `false` for a cancelled or superseded switch, and `Transition` is `async void`, so its caller cannot catch an exception — every `await` around the scheduler is wrapped and logged instead.

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
    TM -> TM: CancelActiveSwitch(); prune dead WeakReferences\nactives = alive IThemeObject[]
    loop each active
        TM -> TO: ExecuteThemeChanging(current = Dark, new = Light)
        activate TO
        TO -> TO: base chain + OnThemeChanging (user hook)
        deactivate TO
    end
    note right of TM
      ApplyImmediately(PrepareSamplers(actives, typeof(Light)), typeof(Light))
      - no timeline, no scheduler, no effect, no platform interpolator.
    end note
    loop each group, each entry with a non-null EndValue
        TM -> TO: TransitionProperty.SetValue(target, EndValue)
        activate TO
        TO --> TM: (compiled write, ignores a false return)
        deactivate TO
    end
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

`Jump` performs no normalization and consults no sampler: `TransitionProperty.SetValue` writes the declared value verbatim, and a property with a registered sampler is written the same way as one without. Note the asymmetry that follows — `Jump` cancels an in-flight animated switch first (`CancelActiveSwitch`), but an in-flight `Jump` cannot be cancelled, because it contains no await point at all.

## Guard Conditions & Edge Paths

| Scenario | Behavior |
|---|---|
| `themeType == Current` | Guard returns early with the debug message `[ThemeManager] Invalid theme type, jumping to current theme.` (no-op — it does not re-apply). |
| `themeType` not assignable to `ITheme` | Same guard, same no-op return. |
| No platform interpolator (`_interpolator is null`) | `RunSwitch` degrades to `ApplyImmediately`: every end value is written at once and `Current` advances — no animation, and `ExecuteThemeChanged` still fires. |
| Some target's scheduler is null | The whole switch degrades to `ApplyImmediately`, not just that target. |
| An exception escapes `RunSwitch` | Logged by `Transition`'s catch (the caller of an `async void` cannot catch it) and the switch ends without advancing `Current` and without `ExecuteThemeChanged`. |
| A second switch starts while one runs | `CancelActiveSwitch` cancels each run's token and wakes its timeline; the superseded switch returns `false`, so it advances nothing and announces nothing. |
| Property type has a registered sampler | `InterpolatorCore.Prepare` resolves it and normalizes the endpoints; middle frames come from `ISampler.InsertFrame`. |
| Property type has no sampler | Held at its prepared start for the whole pass; `ApplyHeldValues` writes the end value after `Task.WhenAll`. |
| A property's `EndValue` is null | Skipped by `BuildState` (not sampled) and by `ApplyHeldValues` (not written) — the theme leaves it alone. |
| No value found for the property (start or target) | `PrepareSamplers` logs `... skipping` and omits that property from the switch. |
| Effect with a zero duration / `Jump` | `Jump` writes the end values synchronously; a zero-duration `Transition` completes its one pass on the next frame. |
| Dead registered object | Pruned at the start of the switch (weak references), then ignored. |

> Source: `Src/Core/VeloxDev.Core/DynamicTheme/ThemeManager.cs` — `Transition` (lines 109-146), `Transition<T>` (152-155), `Jump` (161-185), `Jump<T>` (190-193), `RunSwitch` (199-291), `WasCancelled` (297-307), `CancelActiveSwitch` (312-332), `WriteStartValues` (334-347), `BuildState` (353-376), `ApplyHeldValues` (381-399), `ApplyImmediately` (404-425), `PrepareSamplers` (427-577), and the private nested `TargetEntries` (584-588), `TransitionEntry` (590-610), `SwitchTarget` (613-618). Behaviour verified by `Src/Core/VeloxDev.Core.Test/DynamicTheme/ThemeTransitionTests.cs`.
