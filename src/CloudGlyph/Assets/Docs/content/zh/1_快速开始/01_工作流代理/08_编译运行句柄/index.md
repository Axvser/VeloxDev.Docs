# 08 · 编译运行句柄

`RunCompiledWorkflow` 会等待到结束。而一次 agent 需要**持有、放开、跟进或停止**的运行做不到这点，于是第二个入口在后台启动同一条编译链并立即返回句柄。句柄家族位于工具包上，每个作用域一份注册表 —— 句柄在启动它的作用域之外毫无意义。

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

四个运行工具都需要 `WithAllowNodeExecution(true)`。

## 1. 启动与续跑

| 工具 | 签名 | 行为 |
|---|---|---|
| `StartCompiledWorkflow` | `StartCompiledWorkflow(int startNodeIndex, string? seed = null)` | 编译从起始节点开始的子图，并在后台任务上开始驱动，**立即**返回句柄。 |
| `ContinueCompiledWorkflow` | `ContinueCompiledWorkflow(int startNodeIndex, string? seed = null)` | 从作用域检查点存储中加载最近的检查点并续跑：已记录为完成的节点**不**再驱动，其产物为下游节点恢复。 |

`ContinueCompiledWorkflow` 在**没有可续跑的检查点时会报错**：

```text
There is no checkpoint to carry on from: nothing has been written yet.
Run the workflow once (StartCompiledWorkflow) and stop it mid-way, then continue.
```

它刻意绝不在 agent 背后启动一次全新运行。来源：`CompiledRunControlTests.CarryingOn_WithNothingWrittenYet_IsRefused`（断言 `status:"error"` 且消息含 `"no checkpoint"`）、`AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`（被停止的运行被续跑到 `Completed`，`logCount > 0`）。

句柄格式为 `run-{n}`（每个工具包一个计数器）。未知句柄返回 `Unknown run handle '<h>'. Handles come from StartCompiledWorkflow / ContinueCompiledWorkflow and belong to one scope; list the run you started rather than inventing one.`

## 2. 跟进 —— `GetCompiledRunStatus`（与句柄退休）

`GetCompiledRunStatus(handle)` 是得知运行已结束的方式：仍在运行的运行 `outcome` 为 `Unknown`；已结束的则不再为 `Unknown`。它报告 `isRunning`、`runStatus`、`outcome`、`isPaused`、`attempts`、`endedWithError`、最终 `data`、`failures`（记录形式：`phase`/`level`/`message`/`attempt`/`order`）、`failureCount`、`logCount`、日志的**最后 40 行**（`RunStatusLogTail = 40`，在运行自己的线程上经 `RuntimeContext.SnapshotLogs()` 读取一次），以及 `logFile`（当宿主把日志写入文件时是绝对路径）。

**它在报告某次运行已结束的同时退休该运行的句柄。** 已结束的运行在回答「是否结束」的同一次调用里被从注册表移除、其 `CancellationTokenSource` 被释放，因此回答与退休描述的是同一状态：

```text
GetCompiledRunStatus("run-1")   → {"status":"ok", "isRunning":false, "outcome":"Completed", ...}   // 最后一次有效回答
GetCompiledRunStatus("run-1")   → {"status":"error", "message":"Unknown run handle 'run-1'. ..."}  // 已退休
```

因此轮询循环必须把 **`isRunning:false` 当作终态回答**并停止；随后一次非 `ok` 的回复不是结束。来源：`CompiledRunControlTests.WaitForEndAsync`（其唯一出口是 `isRunning == false`；源码注释写道 *「A finished run is dropped once it has been reported… Asking again afterwards is an unknown handle, which is the honest answer.」*）。

**预期结果：** 轮询直到 `isRunning == false`，然后从同一条回复读取 `outcome`；再问一次返回未知句柄错误。

## 3. 持有与放开 —— `PauseCompiledRun` / `ResumeCompiledRun`

```text
PauseCompiledRun  → 正在驱动的节点跑完，不启动新的，runStatus 变为 "Paused"
ResumeCompiledRun → 运行从停止处继续（未被持有时是空操作）
```

两者都是幂等的，且 `GetCompiledRunStatus` 中的 `isPaused` 反映该门。来源：`CompiledRunControlTests.AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`（持有时 `isPaused:true` **且** `isRunning:true` —— 「持有不等于结束」；放开后运行到 `Completed`）。

### `RunsOnOurGate` 守卫

`PauseCompiledRun` 与 `ResumeCompiledRun` 操作的是 `run.Gate`，因此该门必须**就是引擎实际在等待的那把**。若宿主经 `WithSessionConfiguration` 自带了一个 `ManualExecutionGate`，这两个工具无法驱动它，于是二者都**返回错误**，而不是报告一次根本没发生的暂停：

```text
Run 'run-1' is held by an execution gate this tool cannot drive — the host brought its own.
Pause and resume it through the host's controls; StopCompiledRun still works.
```

检查是 `RunsOnOurGate(run) == ReferenceEquals(run.Context?.ExecutionGate, run.Gate)`。当宿主的门是 `ManualExecutionGate` 时 `NewSession` 会采纳它（`run.Gate = hostGate`），因此用普通宿主门启动的运行能被正确驱动；错误只在宿主的门**不是**运行所驻的那把时触发。**`StopCompiledRun` 没有此守卫** —— 它取消令牌，无论哪把门都有效，正如它的消息所承诺的。

## 4. 停止与续跑 —— `StopCompiledRun`

```text
StopCompiledRun(handle)  → 正在驱动的节点跑完，运行在该边界以 outcome Cancelled 结束，
                           它留下的检查点仍留在作用域的存储中。
```

`StopCompiledRun` 调用 `run.Cts.Cancel()`，因此运行以 `Cancelled` 结束（而非 `Failed`）。它留下的检查点正是 `ContinueCompiledWorkflow` 要读的东西 —— 被停止的运行可在所需之物修好后稍后续跑。这与 `PauseCompiledRun` 不同：后者持有运行**而不结束它**（令牌未被取消，因此 `ContinueCompiledWorkflow` 帮不上忙，应用 `ResumeCompiledRun`）。

**预期结果：** `StopCompiledRun` 后结束状态为 `outcome:"Cancelled"`；随后的 `ContinueCompiledWorkflow` 启动一个新句柄并跑到 `Completed`。

## 5. 失败与日志随结果同行

两个运行入口都把 `failures` 作为记录、`logFile` 作为绝对路径报告。当会话配置了重试策略（`WithSessionConfiguration(ctx => ctx.RetryPolicy = ...)`）时，failures 数组同时携带 `"Warning"` 与 `"Error"` 级别，且日志文件包含重试行（`"[Retry 1]"`）。来源：`CompiledRunControlTests.TheFailureRecords_AndTheLogFile_TravelWithTheResult`。

## 运行声明

- ✅ 实际构建并运行 —— `CompiledRunControlTests` 在 2026-10-01 的确定性套件中通过（`已通过! 失败: 0，通过: 387`）：`AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`、`AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`、`CarryingOn_WithNothingWrittenYet_IsRefused`、`TheFailureRecords_AndTheLogFile_TravelWithTheResult`。
- ⚠️ **`RunsOnOurGate` 守卫**与 **40 行日志尾巴**仅对照源码核验 —— `Agent/**` 中没有测试覆盖它们（测试文件自身的备注已明确说明）。它们引自 `WorkflowAgentToolkit.cs`。
