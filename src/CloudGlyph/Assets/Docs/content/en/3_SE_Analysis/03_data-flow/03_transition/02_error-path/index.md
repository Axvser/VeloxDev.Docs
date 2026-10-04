# Data Flow — Transition: Error Path

The engine's failure mode is **silence**: a sampler runs inside a dispatcher callback on the UI thread where nothing catches, and `Execute` is `async void`, so there is no caller to receive a throw. The design answer is a single internal mediator (`TransitionDiagnostics`) and one rule the loop keeps unconditionally: *an exception never leaves the loop; it becomes a report, and then the run unwinds down its normal cancellation path.*

## (a) A throwing sampler, mid-frame

```plantuml
@startuml
!theme plain

participant "Interpreter" as TI
participant "SamplerSet" as SET
participant "ISampler" as SM
participant "Diagnostics" as DG
participant "Effect" as EF
participant "Host\n(dispatcher queue)" as Q

TI -> SET: Apply(target, easedT, priority)
activate SET
SET -> Q: Post(target, thread, cachedApply, priority)   (queued)
Q --> SET: accepted: true
deactivate SET

Q -> SET: pumped later, on the target's thread
activate SET
SET -> SET: ApplyCore re-checks: not cancelled, host alive
loop each prepared entry
    SET -> SM: InsertFrame(...)
    SM -> SM: throws (e.g. the framework rejects the value)
end
SET -> DG: Error("Sampling", exception)
activate DG
DG -> DG: first time this stage -> report; subsequent -> false
DG -> EF: InvokeError(target, args)
EF --> DG: (a handler may set args.Handled)
DG --> SET: reported
deactivate DG
SET -> SET: CancelQuietly()   (cts.Cancel(), swallowing ObjectDisposedException)
SET --> Q: return
deactivate SET

note over Q, SET
  Error is reported ONCE per run per stage. A sampler that cannot
  produce a drawable value must not keep throwing at the frame rate.
end note

Q -> TI: the loop's next await sees a cancelled token
TI -> TI: throw OperationCanceledException
TI -> EF: InvokeCancled(sender, args)
TI -> EF: InvokeFinally(sender, args)
note right of TI
  Finally runs in a nested try/finally, so a throwing handler
  cannot take the loop's own resources with it: the pacer and the
  reused timer are released and a host timer is not leaked.
end note
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/SamplerSet.cs` (`ApplyCore`, `CancelQuietly`), `TransitionDiagnostics.cs`, `TransitionInterpreter.cs` (`ExecuteSamplingLoopAsync`, `Report`, `ReleaseLoopResources`).

Two details are worth spelling out:

- **The exception does not propagate, and the token is cancelled *quietly*.** `CancelQuietly` swallows `ObjectDisposedException` because the animation or the adapter may already have disposed the token source — there is nothing left to cancel, and that is not a new failure.
- **`Error` is reported once per stage.** `TransitionDiagnostics` keeps a per-instance `HashSet<string> _reported`; a stage already reported returns `false`. That is what stops a per-frame condition from producing a per-frame log, and it is why the message names the *stage* rather than the frame.

## (b) A throwing callback, and the aborted stages at entry

```plantuml
@startuml
!theme plain

participant "CoreExecute\n(async void)" as CE
participant "Scheduler" as Sch
participant "Host" as H
participant "Diagnostics" as DG
participant "Effect" as EF

== Entry: the stages that can abort a run before it starts ==
CE -> Sch: ExecuteCore(...)
activate Sch
Sch -> H: PostAsync(target, () => InvokeAwake(...))
activate H
H --> Sch: throws, or returns false (nothing was queued)
deactivate H
alt the Awake callback threw
    Sch -> DG: Error("Awake", exception)
    note right of Sch
      A host callback that throws ends the animation here
      and leaves the host process untouched.
    end note
else the dispatch was refused
    Sch -> DG: Warn("Dropped", "the host's dispatch queue refused the animation's Awake")
    note right of Sch
      Nothing would be dispatched, frames included, so giving up
      is better than starting a run that cannot draw.
    end note
end
Sch --> CE: return null  (the gate is still released by the finally)
deactivate Sch

== Run: a callback that throws inside the loop ==
Sch -> Sch: newInterpreter.Execute(...)
Sch -> DG: Error("Update" or "LateUpdate" or "Marshaling", exception)
activate DG
DG -> EF: InvokeError(target, args)
deactivate DG
Sch -> EF: InvokeCancled(sender, args)
Sch -> EF: InvokeFinally(sender, args)
note over Sch, EF
  Every callback goes through Report / ReportMarshaling, which
  convert a throw into a report plus the run's NORMAL cancellation
  path. That is what keeps Canceled and Finally firing, and what
  keeps the loop's own resources released.
end note

== Last resort: anything that still escapes ==
CE -> DG: Error("Run", exception)
note right of CE
  CoreExecute is async void, so an escaped exception has no caller
  and would be an unhandled exception in the host process. The catch
  reports it through the root segment's effect and returns.
end note
@enduml
```

> Source: `Src/Core/VeloxDev.Core/TransitionSystem/TransitionScheduler.cs` (`ExecuteCore`), `Transition.cs` (`CoreExecute`), `TransitionInterpreter.cs` (`Report`, `ReportMarshaling`, `ExecuteSamplingLoopAsync`'s catch clauses).

## (c) The diagnosis an operator actually sees

Every report carries `TransitionEventArgs.Stage`, so a log line names the failing stage without re-running anything:

| `Stage` | Raised as | Meaning |
|---|---|---|
| `Awake` | `Error` | the `Awaked` handler threw; the run aborts before preparation |
| `Prepare` | `Error` | normalization threw; the run aborts |
| `Update` / `LateUpdate` | `Error` | an effect callback threw; the pass ends |
| `Marshaling` | `Error` | the host's write path threw (`Apply`) |
| `Sampling` | `Error` | an `ISampler.InsertFrame` threw; the run is cancelled quietly |
| `Run` | `Error` | something escaped the loop's own catch — the `async void` last resort |
| `Dropped` | `Warn` | the host refused a frame, or refused the `Awake` dispatch |
| `Unreadable` | `Warn` | a declared path does not match the target's runtime type; skipped |
| `Unsampled` | `Warn` | no sampler resolves for a declared path; skipped |

The `Warn` / `Error` handlers are `WeakDelegate`-backed like the lifecycle events, and setting `Handled = true` inside one asks the run to terminate — the one place a diagnostic is allowed to *change* behavior. Without a handler the report still reaches `Debug.WriteLine`, so a run that silently degrades in a debugger is still visible.
