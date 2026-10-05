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

`ContinueCompiledWorkflow` never starts a fresh run behind the agent's back — with nothing written yet it errors:

```text
There is no checkpoint to carry on from: nothing has been written yet.
Run the workflow once (StartCompiledWorkflow) and stop it mid-way, then continue.
```

Source: `CompiledRunControlTests.CarryingOn_WithNothingWrittenYet_IsRefused`, `AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`.

Handles are formatted `run-{n}` (a per-toolkit counter). An unknown handle returns `Unknown run handle '<h>'. Handles come from StartCompiledWorkflow / ContinueCompiledWorkflow and belong to one scope; list the run you started rather than inventing one.`

## 2. Follow — `GetCompiledRunStatus`

The status reply is the whole state of a run in one object:

| Field | Meaning |
|---|---|
| `isRunning` | Whether the run is still going. **A finished run's answer is `false` — that is the terminal reading.** |
| `runStatus` | `Running` / `Paused` / `Stopped` |
| `outcome` | `Unknown` while running, then `Completed` / `Cancelled` / `Failed` |
| `isPaused` | The gate is holding it. `isPaused:true` comes with `isRunning:true` — *held is not finished* |
| `attempts`, `endedWithError` | Redirect attempts, and whether a failure ended the flow |
| `data` | The run's final payload |
| `failures`, `failureCount` | Failure records: `phase` / `level` / `message` / `attempt` / `order` |
| `logCount`, `logs` | `logs` is the **last 40 lines** (`RunStatusLogTail = 40`, read once through `RuntimeContext.SnapshotLogs()` on the run's own thread) |
| `logFile` | An absolute path, present only when the host sent the lines to a file |

**The call retires the handle once it has reported the run as finished** — the run is dropped from the registry and its `CancellationTokenSource` disposed in the same call that answered "is it finished", so the answer and the retirement describe one state:

```text
GetCompiledRunStatus("run-1")   → {"status":"ok", "isRunning":false, "outcome":"Completed", ...}   // last good answer
GetCompiledRunStatus("run-1")   → {"status":"error", "message":"Unknown run handle 'run-1'. ..."}  // retired
```

So a poll loop stops on **`isRunning:false`**; a later non-`ok` reply is not an ending. Source: `CompiledRunControlTests.WaitForEndAsync` — its only exit is `isRunning == false`.

**Expected result:** poll until `isRunning == false`, then read `outcome` from that same reply; asking again returns an unknown-handle error.

## 3. Hold and let go — `PauseCompiledRun` / `ResumeCompiledRun`

| Tool | Effect |
|---|---|
| `PauseCompiledRun` | The node being driven finishes, nothing new starts, `runStatus` becomes `Paused` |
| `ResumeCompiledRun` | The run goes on from where it stopped — a no-op when it was not held |

Both are idempotent. Source: `CompiledRunControlTests.AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`.

### The `RunsOnOurGate` guard

These two operate on `run.Gate`, so that gate must be **the one the engine is actually waiting on**. A host that brought its own `ManualExecutionGate` via `WithSessionConfiguration` has a gate the tools cannot drive, and they return an error rather than reporting a pause that never happened:

```text
Run 'run-1' is held by an execution gate this tool cannot drive — the host brought its own.
Pause and resume it through the host's controls; StopCompiledRun still works.
```

The check is `ReferenceEquals(run.Context?.ExecutionGate, run.Gate)`. `NewSession` adopts a host `ManualExecutionGate` (`run.Gate = hostGate`), so a plain host gate is driven correctly; the error fires only when the host's gate is *not* the one the run is parked on. **`StopCompiledRun` has no such guard** — it cancels the token, which works whatever the gate.

## 4. Stop and carry on — `StopCompiledRun`

```text
StopCompiledRun(handle)  → the node being driven finishes, the run ends at that boundary with outcome Cancelled,
                            and the checkpoint it left stays in the scope's store.
```

| | Ends the run? | Token | How to go on |
|---|---|---|---|
| `PauseCompiledRun` | No — it holds the run | not cancelled | `ResumeCompiledRun` |
| `StopCompiledRun` | Yes, as `Cancelled` (not `Failed`) | cancelled | `ContinueCompiledWorkflow` reads the checkpoint it left |

**Expected result:** after `StopCompiledRun`, the end status is `outcome:"Cancelled"`; a following `ContinueCompiledWorkflow` starts a new handle that runs to `Completed`.

## 5. Failures and the log travel with the result

Both run entries report `failures` as records and `logFile` as an absolute path. With a retry policy on the session (`WithSessionConfiguration(ctx => ctx.RetryPolicy = ...)`) the array carries both `"Warning"` and `"Error"` levels, and the log file contains the retry lines (`"[Retry 1]"`). Source: `CompiledRunControlTests.TheFailureRecords_AndTheLogFile_TravelWithTheResult`.

## Run declaration

- ✅ Actually built and ran — `CompiledRunControlTests` passed in the deterministic suite on 2026-10-01 (`已通过! 失败: 0，通过: 387`): `AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`, `AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`, `CarryingOn_WithNothingWrittenYet_IsRefused`, `TheFailureRecords_AndTheLogFile_TravelWithTheResult`.
- ⚠️ The **`RunsOnOurGate` guard** and the **40-line log tail** are verified against source only — no test in `Agent/**` covers them (noted explicitly in the test file's own remarks). They are quoted from `WorkflowAgentToolkit.cs`.
