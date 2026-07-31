# Data Flow — Transition System

## Executing a State Snapshot (`snapshot.Execute(target)`)

The complete call chain from `Execute` to the frame pump. This flow works identically across all six platform adapters.

```plantuml
@startuml
!theme plain

actor User as User
participant "StateSnapshot" as SS
participant "TransitionCore" as TC
participant "TransitionScheduler" as Sch
participant "Interpolator" as IC
participant "UIThreadInspector" as UI
participant "FrameSequence" as FS
participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "Target (UI element)" as T

User -> SS: Execute(Rec0, CanMutualTask)
activate SS

SS -> TC: (static) Execute(target, snapshot, CanMutualTask)
activate TC

TC -> Sch: FindOrCreate(target, CanMutualTask)
activate Sch
alt CanMutualTask == true
    Sch -> Sch: return shared scheduler (ConditionalWeakTable)
else false
    Sch -> Sch: return one-off non-mutual scheduler
end
Sch --> TC: scheduler
deactivate Sch

TC -> Sch: Execute(interpolator, state, effect, cts)
activate Sch

Sch -> IC: Interpolate(target, state, effect, isUIAccess, inspector)
activate IC

loop every recorded property
    IC -> IC: TryGetInterpolator(propertyType) -> IValueInterpolator
    IC -> IC: IInterpolable? fallback on start/end value
    IC -> IC: build List<object?> frames (steps = Duration/(1000/FPS))
end

IC --> Sch: FrameSequence (per-property frame lists)
deactivate IC

Sch -> TI: Execute(target, frameSequence, effect, isUIAccess, cts)
activate TI

TI -> EF: InvokeStart(sender, args)
EF --> TI: Start event fired

loop index in 0 .. frames.Count-1
    TI -> TI: easedIndex = GetEaseIndex(effect.Ease, index, count)
    TI -> FS: Update(target, easedIndex, isUIAccess, priority)
    activate FS
    loop each property
        FS -> UI: IsUIThread()?
        alt on UI thread
            FS -> T: property.SetValue(target, frame[prop][easedIndex])
        else not on UI thread
            UI -> UI: ProtectedInvoke(false, action) (marshals to UI thread)
            UI -> T: property.SetValue(target, frame[prop][easedIndex])
        end
    end
    deactivate FS
    TI -> EF: InvokeUpdate(sender, args)
    TI -> TI: await Delay(duration/count)
end

alt IsAutoReverse
    TI -> TI: walk frames backwards (reverse index)
end

alt LoopTime > 1 or int.MaxValue
    TI -> TI: repeat loop (LoopTime times, or forever)
end

TI -> EF: InvokeCompleted(sender, args)
deactivate TI
Sch --> TC: completed
deactivate Sch
TC --> SS
deactivate TC
SS --> User: return
deactivate SS
@enduml
```

## Cancellation & Error Path

```plantuml
@startuml
!theme plain

participant "TransitionInterpreter" as TI
participant "Effect" as EF
participant "TransitionEventArgs" as Args

TI -> TI: frame loop
TI -> TI: Args.Handled == true?
alt Handled == true
    TI -> EF: InvokeCancled(sender, args)
    TI -> EF: InvokeFinally(sender, args)
    TI -> TI: stop immediately
else cancelled via CTS (Transition.Exit)
    TI -> EF: InvokeCancled(sender, args)
    TI -> EF: InvokeFinally(sender, args)
    TI -> TI: stop immediately
else app shutdown (IsAppAlive() == false)
    TI -> TI: stop without further invocations
end
@enduml
```

## Normal / Error Path Summary

| Scenario | Behavior |
|---|---|
| Normal execution | Frames applied on the UI thread via `UIThreadInspector`; `Update`/`LateUpdate` events fire per frame; `Completed` + `Finally` at the end. |
| New mutual animation on same target | Previous scheduler is `Exit()`-ed (current animation cancelled) before the new one runs. |
| `TransitionEventArgs.Handled = true` | Short-circuits the timeline; `Canceled` + `Finally` events fire. |
| `Transition.Exit(target)` | Cancels the target's mutual (and optionally non-mutual) schedulers. |
| Background-thread start | `UIThreadInspector.ProtectedInvoke(false, action)` marshals frame writes to the UI thread. |
| Property without interpolator | The property is skipped; other properties still animate. |

> Source references: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionInterpreter.cs` (frame pump), `TransitionScheduler.cs` (`FindOrCreate`, `Execute`), `Interpolator.cs` (resolution), `InterpolatorOutputCore.cs` (`Update`), `Src/Adapters/*/PlatformAdapters/UIThreadInspector.cs`.
