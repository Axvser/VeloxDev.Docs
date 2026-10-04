# Functions · Execution Tools

Category `Execution` — **12 tools**, all gated by `WithAllowNodeExecution(true)`. They span the three execution levels: node EXEC, the compiled chain, and the compiled-run family. Every one returns `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).` when the gate is off.

## Node level (4)

| Tool | Signature | Purpose |
|---|---|---|
| `ExecuteNode` | `ExecuteNode(int nodeIndex, string? parameter = null)` | Runs `ReceiveCommand` on one node and **waits** until it completes. |
| `ExecuteNodes` | `ExecuteNodes(string nodeIndicesJson, string? parameter = null)` | Runs `ReceiveCommand` on a JSON array of indices and waits for each (`completed` + `errors`). |
| `BroadcastNode` | `BroadcastNode(int nodeIndex, string? parameter = null)` | Runs `BroadcastCommand` to forward data downstream; waits for the command (downstream dispatch is fire-and-forget). |
| `ReverseBroadcastNode` | `ReverseBroadcastNode(int nodeIndex, string? parameter = null)` | Runs `ReverseBroadcastCommand` to trigger `ReceiveCommand` on upstream nodes; waits for the command. |

Source: `WorkflowLifecycleFidelityTests.ExecuteNode_WaitsForCommandCompletion`, `ToolThreadAffinityTests.BuiltInTool_WithAGenuineSuspension_StaysOnTheContext`.

## Chain / result level (2)

| Tool | Signature | Purpose |
|---|---|---|
| `RunCompiledWorkflow` | `RunCompiledWorkflow(int startNodeIndex, string? seed = null)` | Compiles from a start node (Root role) and drives the whole chain via the engine; **waits** for the end. |
| `GetNodeResult` | `GetNodeResult(int nodeIndex, string? seed = null)` | Compiles the node's ancestor cone (Terminal role) and drives it; returns `targetReached` and the node's result. |

Their result shape and the Terminal error contract are on the `VeloxDev.AI.Workflow` design pages; the run-handle family below starts the same chain in the background.

## Run-handle family (6)

| Tool | Signature | Purpose |
|---|---|---|
| `StartCompiledWorkflow` | `StartCompiledWorkflow(int startNodeIndex, string? seed = null)` | Starts a compiled run and returns **at once** with a `handle`; poll with `GetCompiledRunStatus`. |
| `ContinueCompiledWorkflow` | `ContinueCompiledWorkflow(int startNodeIndex, string? seed = null)` | Starts a run that **carries on** from the last checkpoint in the scope's store. Errors when there is no checkpoint. |
| `GetCompiledRunStatus` | `GetCompiledRunStatus(string handle)` | Reports on a run: `isRunning`, `runStatus`, `outcome`, `isPaused`, `attempts`, `endedWithError`, `data`, `failures`, `failureCount`, `logs` (last 40), `logFile`. **Retires the handle** once it has reported the run as finished. Pure query. |
| `PauseCompiledRun` | `PauseCompiledRun(string handle)` | Holds the run at its next node boundary. Returns an **error** when the host brought its own execution gate (`RunsOnOurGate`). |
| `ResumeCompiledRun` | `ResumeCompiledRun(string handle)` | Lets a held run go again (a no-op when it was not held). Same `RunsOnOurGate` guard. |
| `StopCompiledRun` | `StopCompiledRun(string handle)` | Stops the run: it ends at the current node boundary with `outcome: Cancelled`, checkpoint retained. **No gate guard.** |

### Handle semantics

- Handles are `run-{n}` from a per-toolkit counter; an unknown handle returns `Unknown run handle '<h>'. Handles come from StartCompiledWorkflow / ContinueCompiledWorkflow and belong to one scope; list the run you started rather than inventing one.`
- `ContinueCompiledWorkflow` with nothing written yet: `There is no checkpoint to carry on from: nothing has been written yet. Run the workflow once (StartCompiledWorkflow) and stop it mid-way, then continue.`
- `PauseCompiledRun` / `ResumeCompiledRun` when the gate is not the run's: `Run '<h>' is held by an execution gate this tool cannot drive — the host brought its own. Pause and resume it through the host's controls; StopCompiledRun still works.`
- `GetCompiledRunStatus` reads its log tail through `RuntimeContext.SnapshotLogs()`, keeps the last `RunStatusLogTail = 40` lines, and drops the handle (and disposes its `CancellationTokenSource`) in the same call that answers "is it finished".

**Exceptions:** none are thrown to the model — failures come back as a JSON `{"status":"error","message":"…"}` object.

Source: `CompiledRunControlTests` (`AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`, `AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`, `CarryingOn_WithNothingWrittenYet_IsRefused`, `TheFailureRecords_AndTheLogFile_TravelWithTheResult`).

## Example

```text
// Source: Test — CompiledRunControlTests
StartCompiledWorkflow(startNodeIndex: 0)        → {"status":"ok","handle":"run-1",...}
GetCompiledRunStatus("run-1")                    → {"status":"ok","isRunning":true,"outcome":"Unknown",...}
PauseCompiledRun("run-1")                        → {"status":"ok"}
GetCompiledRunStatus("run-1")                    → {"status":"ok","isRunning":true,"isPaused":true}
ResumeCompiledRun("run-1")                       → {"status":"ok"}
GetCompiledRunStatus("run-1")                    → {"status":"ok","isRunning":false,"outcome":"Completed",...}
GetCompiledRunStatus("run-1")                    → {"status":"error","message":"Unknown run handle 'run-1'. ..."}
```

**Expected result:** the last poll is the terminal answer (`isRunning:false`); the one after it is an unknown-handle error.
