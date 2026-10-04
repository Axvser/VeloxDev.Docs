# Data Flow — Command Lifecycle

The execution pipeline in `Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`. The invariant the whole design turns on is stated in the source itself (`VeloxCommand.cs` lines 192-194): `_stateLock` is a `SemaphoreSlim(1,1)` and therefore **not reentrant**, so no user code — no event handler, no command body — may run while it is held. Every `RaiseCommandEvent` happens after a `Release()`.

## (a) Immediate run: Created → Started → Completed → Exited

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "VeloxCommand" as Cmd
participant "_stateLock (SemaphoreSlim)" as Lock
participant "Command body\nIncrement(parameter, ct)" as Body
participant "Subscribers" as Sub

UI -> Cmd: Execute(null) / ExecuteAsync(null)
activate Cmd
Cmd -> Cmd: new CommandEventArgs(parameter, Created)
Cmd -> Cmd: attach a CancellationTokenSource when _isCtsNeeded
Cmd -> Sub: raise Created
Cmd -> Lock: WaitAsync()
activate Lock
Cmd -> Cmd: _active.Count < _maxConcurrency  ->  _active.Add(item)
Cmd -> Lock: Release()
deactivate Lock
Cmd -> Cmd: fire ExecuteCoreAsync(item); Notify()
Cmd -> Sub: raise Started
Cmd -> Body: await _command(item.Parameter, item.Cts.Token)
activate Body
Body -> Body: Index++ ; Greeting = "current index: {Index}"
Body --> Cmd: return (or throw)
deactivate Body
alt body returned normally
    Cmd -> Sub: raise Completed
else body threw OperationCanceledException
    Cmd -> Sub: raise Canceled (first emitter wins)
else body threw anything else
    Cmd -> Sub: raise Failed with e.Exception
end
Cmd -> Lock: WaitAsync()  (finally: _active.Remove(item))
activate Lock
Cmd -> Cmd: _active.Remove(item)
Cmd -> Lock: Release()
deactivate Lock
Cmd -> Sub: raise Exited
Cmd -> Cmd: TryStartPendingAsync(); RaiseCanExecuteChanged()
Cmd --> UI
deactivate Cmd
@enduml
```

> Source: `VeloxCommand.cs` — `ExecuteCore` lines 474-531, `ExecuteCoreAsync` lines 533-580, `OnExecutionCompletedAsync` lines 582-598.

## (b) Queueing at capacity: Enqueued … Dequeued

```plantuml
@startuml
!theme plain

participant "UI (Button)" as UI
participant "VeloxCommand" as Cmd
participant "_pendingQueue" as Queue
participant "Command body (first)" as First

UI -> Cmd: first trigger: Execute(null)
activate Cmd
Cmd -> Cmd: raise Created; _active.Add(first) because the slot is free
Cmd -> First: await _command(item.Parameter, ct)
activate First

UI -> Cmd: second trigger: Execute(null)
activate Cmd
Cmd -> Cmd: raise Created
Cmd -> Cmd: _active.Count == _maxConcurrency
Cmd -> Queue: Enqueue(second)
Cmd -> Cmd: raise Enqueued; Notify()
Cmd --> UI
deactivate Cmd

First --> Cmd: return
deactivate First
Cmd -> Cmd: raise Completed
Cmd -> Cmd: finally: _active.Remove(first); raise Exited
Cmd -> Cmd: TryStartPendingAsync()
Cmd -> Queue: Dequeue() -> second ; _active.Add(second)
Cmd -> Cmd: raise Dequeued
Cmd -> Cmd: fire ExecuteCoreAsync(second)
Cmd --> UI
deactivate Cmd
@enduml
```

> Source: `VeloxCommand.cs` — enqueue branch lines 503-505 and 521-524, `TryStartPendingAsync` lines 794-822 (the drain loop is lines 801-809).

## (c) Refusal under lock: Created → Canceled, and nothing else

```plantuml
@startuml
!theme plain

participant "Caller" as Caller
participant "VeloxCommand" as Cmd
participant "Command body" as Body
participant "Awaiting sink (if any)" as Sink

Caller -> Cmd: ExecuteAsync(null) while _isForceLocked
activate Cmd
Cmd -> Cmd: raise Created
Cmd -> Cmd: under the lock: forceLocked == true  ->  neither start nor enqueue
Cmd -> Cmd: item.Cts?.Cancel()
Cmd -> Cmd: raise Canceled
Cmd -> Cmd: item.TakeCts()?.Dispose()
Cmd -> Sink: item.Complete(CommandOutcome.Refused, null)
note right of Body: never entered - no Started, no Exited
Cmd --> Caller
deactivate Cmd
@enduml
```

> Source: `VeloxCommand.cs` lines 513-520. This is the only path that produces `CommandOutcome.Refused`, and the reason `CommandEventType` alone cannot express a refusal (`CommandCompletion.cs` lines 22-28).

## (d) Cancellation and clearing

```plantuml
@startuml
!theme plain

participant "Caller" as Caller
participant "VeloxCommand" as Cmd
participant "_active / _pendingQueue" as Sets
participant "Command body (running)" as Body

Caller -> Cmd: InterruptAsync()
activate Cmd
Cmd -> Cmd: LockCoreAsync() - remembers whether it was already locked
Cmd -> Sets: snapshot _active ; _active.Clear()
Cmd -> Body: it.Cts?.Cancel()
activate Body
Body --> Cmd: throws OperationCanceledException
deactivate Body
Cmd -> Cmd: raise Canceled (direct, for each active item)
Cmd -> Body: the body's own OCE reaches ExecuteCoreAsync
Cmd -> Cmd: RaiseCanceled -> TryMarkCancelReported blocks the second report
Cmd -> Cmd: raise Exited from ExecuteCoreAsync's finally
Cmd -> Cmd: if it was not locked before, UnlockAsync()
Cmd --> Caller
deactivate Cmd

== Clear is the same plus the queue ==

Caller -> Cmd: ClearAsync()
activate Cmd
Cmd -> Cmd: LockCoreAsync()
Cmd -> Sets: snapshot _active ; drain _pendingQueue into pendingToCancel
Cmd -> Cmd: raise Dequeued for every pending item, in queue order
Cmd -> Cmd: per pending item: Cancel(); raise Canceled; TakeCts()?.Dispose(); Complete(Canceled, null)
Cmd -> Cmd: per active item: Cancel(); raise Canceled
Cmd -> Cmd: UnlockAsync() if it was not locked before
Cmd --> Caller
deactivate Cmd
@enduml
```

> Source: `VeloxCommand.cs` — `InterruptAsync` lines 642-683, `ClearAsync` lines 686-747, `RaiseCanceled` lines 398-404, `TryMarkCancelReported` line 896.

```csharp
// Source: Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs, lines 396-404
// One execution reports at most one Canceled. Interrupt/Clear report promptly;
// the body's own OperationCanceledException arrives later and is blocked by TryMarkCancelReported.
private void RaiseCanceled(CommandEventArgs item)
{
    if (item.TryMarkCancelReported())
    {
        RaiseCommandEventAs(Canceled, item, CommandEventType.Canceled);
    }
}
```

## (e) The `canValidate` gate: property hook → Notify → CanExecuteChanged

```plantuml
@startuml
!theme plain

participant "Generated setter\nIndex" as Setter
participant "partial OnIndexChanged" as Hook
participant "MinusCommand\n(IVeloxCommand)" as Cmd
participant "WPF / Avalonia binding engine" as Bind

Setter -> Hook: OnIndexChanged(old, new)
Hook -> Cmd: MinusCommand.Notify()
Cmd -> Cmd: RaiseCanExecuteChanged()
alt EventContext is null or already current
    Cmd -> Bind: CanExecuteChanged raised inline
else EventContext is set to another context
    Cmd -> Cmd: context.Post(...)  (asynchronous, in lifecycle order)
end
Bind -> Cmd: CanExecute(null)
activate Cmd
Cmd -> Cmd: (_canExecute?.Invoke(parameter) ?? true) && !_isForceLocked
note right of Cmd: delegates to CanExecuteMinusCommand -> _index > 0
Cmd --> Bind: true / false
deactivate Cmd
Bind -> Bind: enable / disable the bound Button
@enduml
```

> Source: `VeloxCommand.cs` — `Notify` line 414, `RaiseCanExecuteChanged` lines 328-339, `CanExecute` lines 407-408; the hook is `Examples/MVVM/WPF/Demo/MainWindowViewModel.cs` lines 34-38.

## Error-path summary

| Path | Behaviour |
|---|---|
| Body throws a non-cancellation exception | `outcome = Failed`, `failure = ex`, `Failed` raised with `CommandEventArgs.Exception`; `Exited` still fires from the `finally`. |
| Body throws `OperationCanceledException` | `outcome = Canceled`, `Canceled` raised — unless `Interrupt` / `Clear` already reported one for that execution. |
| Force-locked trigger | Neither started nor enqueued; `Canceled` raised and the sink completed with `Refused`. |
| `Clear` while calls are queued | `Dequeued` then `Canceled` per pending item; such an item never reaches `Started` / `Exited`. |
| A cancellation callback throws | Swallowed (`AggregateException`), because letting it escape would skip `UnlockAsync` and leave the command permanently locked (`VeloxCommand.cs` lines 669-673, 735-739). |
| `ObjectDisposedException` on `Cancel` | Swallowed: the body may already have finished and released its own source (lines 665-668). |
| A subscriber throws | Caught and reported through the static `HandlerException`; the lifecycle is unaffected. |
| `OnExecutionCompletedAsync` throws | The nested `finally` still runs `item.Complete(...)` and `TakeCts()?.Dispose()` (lines 569-578). |
