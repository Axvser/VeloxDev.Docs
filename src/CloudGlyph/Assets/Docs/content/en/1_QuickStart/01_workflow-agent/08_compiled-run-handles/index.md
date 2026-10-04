# 08 · Compiled Run Handles

`RunCompiledWorkflow` waits for the end. A run the agent must **hold, let go, follow or stop** cannot, so a second entry starts the same compiled chain in the background and returns a handle at once. The handle family lives on the toolkit, one registry per scope — a handle means nothing outside the scope that started it.

```text
StartCompiledWorkflow(startNodeIndex: 0, seed: null)
→ {"status":"ok","handle":"run-1","resumed":false,"message":"Run started. Poll GetCompiledRunStatus with the handle."}

GetCompiledRunStatus(handle: "run-1")
→ {"status":"ok","handle":"run-1","isRunning":true,"runStatus":"Running","outcome":"Unknown",
   "isPaused":false,"attempts":0,"endedWithError":false,"data":null,"failureCount":0,
   "failures":[],"logCount":0,"logs":[],"logFile":null}

PauseCompiledRun(handle: "run-1")   → {"status":"ok","message":"Run 'run-1' is held at its next node boundary ..."}
ResumeCompiledRun(handle: "run-1")  → {"status":"ok","message":"Run 'run-1' is going again ..."}
StopCompiledRun(handle: "run-1")    → {"status":"ok","message":"Run 'run-1' was asked to stop; it ends at the current node boundary."}
```

All four run tools require `WithAllowNodeExecution(true)`.

## 1. Start and continue

| Tool | Signature | Behaviour |
|---|---|---|
| `StartCompiledWorkflow` | `StartCompiledWorkflow(int startNodeIndex, string? seed = null)` | Compiles the sub-graph from the start node and starts driving it on a background task, returning a handle **at once**. |
| `ContinueCompiledWorkflow` | `ContinueCompiledWorkflow(int startNodeIndex, string? seed = null)` | Loads the last checkpoint from the scope's checkpoint store and carries on: nodes that place records as done are **not** driven again, and what they produced is restored for the nodes behind them. |

`ContinueCompiledWorkflow` **errors when there is no checkpoint to carry on from**:

```text
There is no checkpoint to carry on from: nothing has been written yet.
Run the workflow once (StartCompiledWorkflow) and stop it mid-way, then continue.
```

It deliberately never starts a fresh run behind the agent's back. Source: `CompiledRunControlTests.CarryingOn_WithNothingWrittenYet_IsRefused` (asserts `status:"error"` and a message containing `"no checkpoint"`), `AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt` (a stopped run is resumed to `Completed` with `logCount > 0`).

Handles are formatted `run-{n}` (a per-toolkit counter). An unknown handle returns `Unknown run handle '<h>'. Handles come from StartCompiledWorkflow / ContinueCompiledWorkflow and belong to one scope; list the run you started rather than inventing one.`

## 2. Follow — `GetCompiledRunStatus` (and handle retirement)

`GetCompiledRunStatus(handle)` is the way to learn a run has finished: a still-running run's `outcome` is `Unknown`; a finished one stops being `Unknown`. It reports `isRunning`, `runStatus`, `outcome`, `isPaused`, `attempts`, `endedWithError`, the final `data`, `failures` (as records: `phase`/`level`/`message`/`attempt`/`order`), `failureCount`, `logCount`, the **last 40 lines** of the log (`RunStatusLogTail = 40`, read once through `RuntimeContext.SnapshotLogs()` on the run's own thread), and `logFile` (an absolute path when the host sent the lines to a file).

**It retires the run's handle once it has reported the run as finished.** A finished run is dropped from the registry and its `CancellationTokenSource` disposed in the same call that answered "is it finished", so the answer and the retirement describe one state:

```text
GetCompiledRunStatus("run-1")   → {"status":"ok", "isRunning":false, "outcome":"Completed", ...}   // last good answer
GetCompiledRunStatus("run-1")   → {"status":"error", "message":"Unknown run handle 'run-1'. ..."}  // retired
```

So a poll loop must treat **`isRunning:false` as the terminal answer** and stop; a subsequent non-`ok` reply is not an ending. Source: `CompiledRunControlTests.WaitForEndAsync` (its only exit is `isRunning == false`; the source comment reads *"A finished run is dropped once it has been reported… Asking again afterwards is an unknown handle, which is the honest answer."*).

**Expected result:** poll until `isRunning == false`, then read `outcome` from that same reply; asking again returns an unknown-handle error.

## 3. Hold and let go — `PauseCompiledRun` / `ResumeCompiledRun`

```text
PauseCompiledRun  → the node being driven finishes, nothing new starts, runStatus becomes "Paused"
ResumeCompiledRun → the run goes on from where it stopped (a no-op when it was not held)
```

Both are idempotent, and `isPaused` in `GetCompiledRunStatus` reflects the gate. Source: `CompiledRunControlTests.AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd` (holding shows `isPaused:true` **and** `isRunning:true` — "held is not finished"; resuming then ends `Completed`).

### The `RunsOnOurGate` guard

`PauseCompiledRun` and `ResumeCompiledRun` operate on `run.Gate`, so that gate must be **the one the engine is actually waiting on**. A host that brought its own `ManualExecutionGate` via `WithSessionConfiguration` has a gate these tools cannot drive, and both tools then **return an error** instead of reporting a pause that never happened:

```text
Run 'run-1' is held by an execution gate this tool cannot drive — the host brought its own.
Pause and resume it through the host's controls; StopCompiledRun still works.
```

The check is `RunsOnOurGate(run) == ReferenceEquals(run.Context?.ExecutionGate, run.Gate)`. `NewSession` adopts the host's gate when it is a `ManualExecutionGate` (`run.Gate = hostGate`), so a run started with a plain host gate is driven correctly; the error fires only when the host's gate is *not* the one the run is parked on. **`StopCompiledRun` has no such guard** — it cancels the token, which works whatever the gate, exactly as its message promises.

## 4. Stop and carry on — `StopCompiledRun`

```text
StopCompiledRun(handle)  → the node being driven finishes, the run ends at that boundary with outcome Cancelled,
                            and the checkpoint it left stays in the scope's store.
```

`StopCompiledRun` calls `run.Cts.Cancel()`, so the run ends as `Cancelled` (not `Failed`). The checkpoint it left behind is exactly what `ContinueCompiledWorkflow` reads — a stopped run can be resumed later once whatever it needed has been fixed. This is different from `PauseCompiledRun`, which holds the run **without ending it** (the token is not cancelled, so `ContinueCompiledWorkflow` would not help; use `ResumeCompiledRun`).

**Expected result:** after `StopCompiledRun`, the end status is `outcome:"Cancelled"`; a following `ContinueCompiledWorkflow` starts a new handle that runs to `Completed`.

## 5. Failures and the log travel with the result

Both run entries report `failures` as records and `logFile` as an absolute path. With a retry policy configured on the session (`WithSessionConfiguration(ctx => ctx.RetryPolicy = ...)`) the failures array carries both `"Warning"` and `"Error"` levels, and the log file contains the retry lines (`"[Retry 1]"`). Source: `CompiledRunControlTests.TheFailureRecords_AndTheLogFile_TravelWithTheResult`.

## Run declaration

- ✅ Actually built and ran — `CompiledRunControlTests` passed in the deterministic suite on 2026-10-01 (`已通过! 失败: 0，通过: 387`): `AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`, `AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`, `CarryingOn_WithNothingWrittenYet_IsRefused`, `TheFailureRecords_AndTheLogFile_TravelWithTheResult`.
- ⚠️ The **`RunsOnOurGate` guard** and the **40-line log tail** are verified against source only — no test in `Agent/**` covers them (noted explicitly in the test file's own remarks). They are quoted from `WorkflowAgentToolkit.cs`.
