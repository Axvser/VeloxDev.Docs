# Workflow System — Host Capabilities Around One Drive

The seven optional seams (2026-09-27) wrapped around a single node drive. Every one is read off the concrete `RuntimeContext` through a private `Session()` helper, so it also works inside a fan-out; every one left unset reproduces the pre-2026-09-27 behavior exactly.

```plantuml
@startuml
!theme plain
participant "RuntimeEngine" as Engine
participant "ExecutionGate" as Gate
participant "Observer" as Obs
participant "Node (IRuntimeAware)" as Node
participant "RetryPolicy" as Retry
participant "ErrorSink" as Sink
participant "CheckpointStore" as Ckpt
participant "LogWriter" as Log
participant "Compensation" as Comp

== Before the drive ==
Engine -> Gate: WaitAsync(ct)
activate Gate
alt gate closed
    Engine -> Engine: Status = "Paused" (written only while actually held)
    Gate --> Engine: released (or throws OperationCanceledException ⇒ Stopped / Cancelled)
else gate open
    Gate --> Engine: Task.CompletedTask — no await, no Status flicker
end
deactivate Gate
Engine -> Obs: OnObservedAsync(NodeStarted, node, attempt)
note right of Obs: a throw is logged as [Observer] and changes nothing

== The drive, inside the failure discipline ==
Engine -> Node: AttachRuntimeContext(context)
note right of Node: inside the discipline on purpose — a host throw ends the run\ninstead of silently skipping the node (EngineHostContractFailureTests)
Engine -> Node: ReceiveAsync(context, ct)
activate Node
alt returns normally
    Node --> Engine: result
    Engine -> Obs: OnObservedAsync(NodeSucceeded, elapsed)
    Engine -> Ckpt: SaveAsync(context.Snapshot(), ct)
    note right of Ckpt: a throw ⇒ one [Checkpoint] line, run continues
else throws
    Node --> Engine: exception
    Engine -> Obs: OnObservedAsync(NodeFailed, message, elapsed)
    Engine -> Retry: NextRetryAsync(NodeFailure(node, ex, failures, elapsed), ct)
    activate Retry
    alt policy answers with a delay
        Retry --> Engine: TimeSpan
        Engine -> Log: "[Retry n] node: message"      (no [Error] line — not failed yet)
        Engine -> Obs: OnObservedAsync(NodeRetried, failures)
        Engine -> Engine: Task.Delay(wait, ct); Data = the SAME input; drive again
        note right of Engine: Attempt is NOT incremented — a retry is not a pass over the graph
    else null / no policy / policy throws
        Retry --> Engine: null
        deactivate Retry
        Engine -> Sink: OnErrorAsync(ExecutionError(Phase = Node, ex), ct)
        Engine -> Engine: RegisterOutput(node, null); Data = null; rethrow
    end
end
deactivate Node

== After the drive reported ==
alt reported Warning
    Engine -> Engine: the node's value still flows; no redirect is asked for
else reported Error and node is not IRedirectable
    Engine -> Sink: OnErrorAsync(Phase = Node, "reported an error but does not implement IRedirectable")
    Engine -> Engine: CurrentOrder = -1; EndedWithError = true
else reported Error and node is IRedirectable
    Engine -> Node: ResolveRedirectAsync(context, ct)
    alt that call throws
        Engine -> Sink: OnErrorAsync(Phase = Redirect, ex)
        Engine -> Engine: CurrentOrder = -1; EndedWithError = true
    end
end

== End of the run ==
Engine -> Engine: Outcome = Completed | Cancelled | Failed
Engine -> Comp: CompensateAsync(NodeCompensation, CancellationToken.None)
activate Comp
note right of Comp: ONLY when Outcome is Failed or Cancelled, most recent first,\nand never with the run's token — after a cancellation that one is already cancelled
Comp --> Engine: (a throw is logged as [Compensation]; the rest still run)
deactivate Comp
Engine -> Obs: OnObservedAsync(RunEnded, elapsed)
note right of Obs: the RunEnded observation is sent with CancellationToken.None —\nafter a cancellation the run's token would make the observer reject it
@enduml
```

## The order is the contract

| # | Step | Read from | A throw means |
|---|---|---|---|
| 1 | `ExecutionGate.WaitAsync(ct)` | `RuntimeContext.ExecutionGate` | `OperationCanceledException` ⇒ `Stopped` / `Cancelled` |
| 2 | `Observer` — `NodeStarted` | `.Observer` | logged as `[Observer]`, run unchanged |
| 3 | `IRuntimeAware.AttachRuntimeContext` | the node | **the run ends** (not a silent skip) |
| 4 | `ReceiveAsync` | the node | goes to step 5 |
| 5 | `RetryPolicy.NextRetryAsync` | `.RetryPolicy` | treated as "no more retries" |
| 6 | `ErrorSink.OnErrorAsync` | `.ErrorSink` | swallowed, logged as `[ErrorSink]` |
| 7 | `CheckpointStore.SaveAsync` | `.CheckpointStore` | logged as `[Checkpoint]`, run continues |
| 8 | `Compensation.CompensateAsync` | `.Compensation` | logged as `[Compensation]`, the rest still run |
| — | `LogWriter.Write` | `.LogWriter` | dropped, reported on `RuntimeContext.LogWriteFailed` |

Two rules hold across all of them: **the engine writes no log line for a cancellation**, and **a report never fails the run that made it**.

**Verified behavior** (reproduced against the shipped library — one session per capability):

```text
[5] paused: status=Paused isPaused=True running=True data=<null>
[6] observed: NodeStarted:TickerNode, NodeSucceeded:TickerNode, NodeStarted:BiasNode, NodeSucceeded:BiasNode, NodeStarted:PrinterNode, NodeSucceeded:PrinterNode
[6] sink on a clean run: 0 records
[8] retry: status=Completed data=ok drives=3 attempt=1
[8] retry logs: 01. FlakyNode | 02. [Retry 1] FlakyNode: flaky #1 | 03. [Retry 2] FlakyNode: flaky #2
[9] logfile: fileLines=3 retained=2      (the writer keeps every line; Logs keeps the newest 2)
[10] compensate: status=Stopped outcome=Failed currentOrder=-1 reversed=[BoomNode]
```

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs` (`DriveAsync` 412-506, `NextRetryAsync` 511-531, `ReportErrorAsync` 534-540, `NotifyErrorAsync` 543-557, `CompensateAsync` 561-581, `ObserveAsync` 585-599, `OutcomeOf` 602-610, `Session` 672-678); `CompilerEx/Runtime/Model/RuntimeContext.cs` (`AppendLog` 260-279, `ReportNodeAsync` 329-342). Demo: `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`, `ConfigureRun`. Tests: `CompilerEx/Execution{Gate,Observer,Retry,ErrorSink,Compensation}Tests.cs`, `NodeReportTests.cs`, `CompilerLogWriterTests.cs`.*
