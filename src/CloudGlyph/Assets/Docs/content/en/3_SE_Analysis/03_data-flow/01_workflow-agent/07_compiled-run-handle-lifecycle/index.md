# Data Flow — Compiled Run-Handle Lifecycle

`RunCompiledWorkflow` waits for the end; a run the agent must hold, follow or stop cannot. The run-handle family starts the same compiled chain in the background and returns a handle. This page traces the whole lifecycle: start → poll → hold/release → stop/resume, including the two documented behaviours (handle retirement and the `RunsOnOurGate` guard).

```plantuml
@startuml
!theme plain

actor "Agent (model)" as Agent
participant "WorkflowAgentToolkit\n(run tools)" as Toolkit
participant "CompiledRun registry\n(_runs, per scope)" as Registry
participant "ManualExecutionGate" as Gate
participant "RuntimeEngine" as Engine
participant "RuntimeContext" as Ctx
participant "IExecutionCheckpointStore" as Store

== Start ==
Agent -> Toolkit: StartCompiledWorkflow(startNodeIndex, seed)
activate Toolkit
Toolkit -> Toolkit: new CompiledRun(handle "run-1", new ManualExecutionGate)
Toolkit -> Ctx: NewSession(seed)
note right of Toolkit
  Host config runs first (WithSessionConfiguration).
  If the host brought a ManualExecutionGate, it is ADOPTED
  (run.Gate = hostGate); otherwise context.ExecutionGate ??= run.Gate.
  CheckpointStore ??= scope's effective store.
end note
Toolkit -> Registry: _runs["run-1"] = run
Toolkit -> Engine: DriveAsync(graph)  [Task.Run, background]
Toolkit --> Agent: {"status":"ok","handle":"run-1","resumed":false}
deactivate Toolkit

== Poll (follow) ==
loop until isRunning == false
    Agent -> Toolkit: GetCompiledRunStatus("run-1")
    activate Toolkit
    Toolkit -> Ctx: SnapshotLogs()  — the last 40 lines
    Toolkit -> Toolkit: finished = run.Task.IsCompleted
    alt still running
        Toolkit --> Agent: {"isRunning":true,"outcome":"Unknown","isPaused":..,"logs":[..40]}
    else finished  — retired in this same call
        Toolkit -> Registry: _runs.Remove("run-1")
        Toolkit -> Toolkit: run.Cts.Dispose()
        Toolkit --> Agent: {"isRunning":false,"outcome":"Completed|Cancelled|Failed"}
        note right of Toolkit
          A second poll now returns
          "Unknown run handle 'run-1'".
        end note
    end
    deactivate Toolkit
end

== Hold / release ==
Agent -> Toolkit: PauseCompiledRun("run-1")
activate Toolkit
Toolkit -> Toolkit: RunsOnOurGate(run)?
alt the host brought its own gate (Context.ExecutionGate != run.Gate)
    Toolkit --> Agent: {"status":"error","message":"... held by an execution gate this tool cannot drive ... StopCompiledRun still works."}
else this gate is the run's
    Toolkit -> Gate: Pause()
    Toolkit --> Agent: {"status":"ok","message":"held at its next node boundary"}
end
deactivate Toolkit
note over Gate
  The node being driven finishes, nothing new starts,
  runStatus becomes "Paused" — held is not finished
  (isPaused:true AND isRunning:true).
end note
Agent -> Toolkit: ResumeCompiledRun("run-1")
Toolkit -> Gate: Resume()
Toolkit --> Agent: {"status":"ok"}

== Stop, then carry on ==
Agent -> Toolkit: StopCompiledRun("run-1")
activate Toolkit
note right of Toolkit
  No RunsOnOurGate guard here:
  CancellationToken.Cancel() works whatever the gate.
end note
Toolkit -> Toolkit: run.Cts.Cancel()
Toolkit --> Agent: {"status":"ok","message":"... ends at the current node boundary."}
deactivate Toolkit
Engine -> Ctx: outcome = Cancelled (not Failed)
Engine -> Store: checkpoint retained
Agent -> Toolkit: ContinueCompiledWorkflow(startNodeIndex, seed)
activate Toolkit
Toolkit -> Store: LoadAsync(CancellationToken.None)
alt no checkpoint written yet
    Toolkit --> Agent: {"status":"error","message":"There is no checkpoint to carry on from ..."}
else a place exists
    Toolkit -> Engine: RunAsync(graph, context, place)
    Toolkit --> Agent: {"status":"ok","handle":"run-2","resumed":true}
end
deactivate Toolkit
@enduml
```

Source: `WorkflowAgentToolkit.cs` (`StartCompiledAsync`, `DriveAsync`, `GetCompiledRunStatus`, `PauseCompiledRun`, `ResumeCompiledRun`, `StopCompiledRun`, `NewSession`, `RunsOnOurGate`, `GateNotOurs`, `CompiledRun`); `RunOutcome.cs`; `RuntimeContext.SnapshotLogs`.

## Behaviour pinned by the diagram

- **Retirement is the answer.** `GetCompiledRunStatus` reads `run.Task.IsCompleted` once and, in the same call, drops the handle and disposes its `CancellationTokenSource` when finished. The answer and the retirement describe one state, so a poll loop exits on `isRunning == false` and a later call is an unknown handle. Test: `CompiledRunControlTests.WaitForEndAsync` — its only exit is `isRunning == false`.
- **The gate the tools drive must be the gate the engine waits on.** `NewSession` adopts the host's `ManualExecutionGate`, so `PauseCompiledRun` / `ResumeCompiledRun` operate the real gate; when the host's gate is *not* the run's, both return an error rather than reporting a pause that did not happen. Tests: `AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`; the guard itself is **source-only** (no test in `Agent/**` asserts it).
- **Stop is a cancellation, not a failure.** `StopCompiledRun` cancels the token; the run ends at a node boundary with `outcome: Cancelled`, and the checkpoint it left is exactly what `ContinueCompiledWorkflow` reads — so a stopped run can be resumed later. Test: `AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`.
- **Continue never invents a start.** With nothing written yet it returns `"no checkpoint"` rather than silently starting a fresh run. Test: `CarryingOn_WithNothingWrittenYet_IsRefused`.
- **Failures and the log travel with the result.** With a retry policy on the session, `failures` carries `Warning` and `Error` records and `logFile` is an absolute path containing the retry lines. Test: `TheFailureRecords_AndTheLogFile_TravelWithTheResult`.

**Run declaration:** the four `CompiledRunControlTests` above passed in the deterministic suite on 2026-10-01 (`已通过! 失败: 0，通过: 387`); the `RunsOnOurGate` guard and the 40-line log tail are verified against source only.
