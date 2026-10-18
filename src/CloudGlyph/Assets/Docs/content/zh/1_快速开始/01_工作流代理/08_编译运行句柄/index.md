# 08 · 编译运行句柄

`RunCompiledWorkflow` 等待结束。若 agent 需要**持有、放行、跟进或停止**一次运行，它做不到，因此第二个入口在后台启动同一条编译链并立即返回句柄。句柄家族位于工具包上，每个作用域一个注册表 —— 句柄在启动它的作用域之外没有意义。

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

`StartCompiledWorkflow` / `ContinueCompiledWorkflow` 要求 `WithAllowNodeExecution(true)`，因为它们会启动节点代码。`GetCompiledRunStatus`、`PauseCompiledRun`、`ResumeCompiledRun` 与 `StopCompiledRun` 操作已有句柄，**不**检查该闸门。

## 1. 启动与继续

| 工具 | 签名 | 行为 |
|---|---|---|
| `StartCompiledWorkflow` | `StartCompiledWorkflow(int startNodeIndex, string? seed = null)` | 编译从起始节点出发的子图，并在后台任务上开始驱动，**立即**返回句柄。 |
| `ContinueCompiledWorkflow` | `ContinueCompiledWorkflow(int startNodeIndex, string? seed = null)` | 从作用域检查点存储加载上一个检查点并继续：已记录为完成的节点不会再次驱动，它们产出的值会为下游节点恢复。 |

`ContinueCompiledWorkflow` 绝不在 agent 背后偷偷开始全新运行 —— 什么都还没写时它会报错：

```text
There is no checkpoint to carry on from: nothing has been written yet.
Run the workflow once (StartCompiledWorkflow) and stop it mid-way, then continue.
```

来源：`CompiledRunControlTests.CarryingOn_WithNothingWrittenYet_IsRefused`、`AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`。

句柄格式为 `run-{n}`（每个工具包一个计数器）。未知句柄返回 `Unknown run handle '<h>'. Handles come from StartCompiledWorkflow / ContinueCompiledWorkflow and belong to one scope; list the run you started rather than inventing one.`

## 2. 跟进 —— `GetCompiledRunStatus`

状态回复用一个对象给出运行的全部状态：

| 字段 | 含义 |
|---|---|
| `isRunning` | 运行是否仍在进行。**已结束运行的答案是 `false` —— 那就是终结读数。** |
| `runStatus` | `Running` / `Paused` / `Stopped` |
| `outcome` | 运行中为 `Unknown`，之后为 `Completed` / `Cancelled` / `Failed` |
| `isPaused` | 闸门正持有它。`isPaused:true` 伴随 `isRunning:true` —— *被持有不等于已结束* |
| `attempts`、`endedWithError` | 重定向尝试次数，以及失败是否结束了流程 |
| `data` | 运行的最终载荷 |
| `failures`、`failureCount` | 失败记录：`phase` / `level` / `message` / `attempt` / `order` |
| `logCount`、`logs` | `logs` 是**最后 40 行**（`RunStatusLogTail = 40`，在运行自己的线程上经 `RuntimeContext.SnapshotLogs()` 读取一次） |
| `logFile` | 仅当宿主把日志行写入文件时为绝对路径 |

**一旦报告运行已结束，该调用就退休这个句柄** —— 运行从注册表移除，其 `CancellationTokenSource` 在回答“是否结束”的同一次调用中释放，因此答案与退休描述的是同一状态：

```text
GetCompiledRunStatus("run-1")   → {"status":"ok", "isRunning":false, "outcome":"Completed", ...}   // 最后一次有效答案
GetCompiledRunStatus("run-1")   → {"status":"error", "message":"Unknown run handle 'run-1'. ..."}  // 已退休
```

因此轮询循环应在 **`isRunning:false`** 停止；之后一次非 `ok` 回复不是结局。来源：`CompiledRunControlTests.WaitForEndAsync` —— 它唯一的退出条件是 `isRunning == false`。

**预期结果：** 轮询到 `isRunning == false`，从同一次回复读取 `outcome`；再次询问返回未知句柄错误。

## 3. 持有与放行 —— `PauseCompiledRun` / `ResumeCompiledRun`

| 工具 | 效果 |
|---|---|
| `PauseCompiledRun` | 正在驱动的节点完成后，不再启动新节点，`runStatus` 变为 `Paused` |
| `ResumeCompiledRun` | 运行从停下的地方继续 —— 未被持有时是空操作 |

两者都是幂等的。来源：`CompiledRunControlTests.AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`。

### `RunsOnOurGate` 守卫

这两个工具操作 `run.Gate`，因此该闸门必须**正是引擎实际等待的那个**。通过 `WithSessionConfiguration` 自带 `ManualExecutionGate` 的宿主拥有一个工具无法驱动的闸门，它们会返回错误，而不是报告一次并未发生的暂停：

```text
Run 'run-1' is held by an execution gate this tool cannot drive — the host brought its own.
Pause and resume it through the host's controls; StopCompiledRun still works.
```

检查是 `ReferenceEquals(run.Context?.ExecutionGate, run.Gate)`。`NewSession` 会采纳宿主的 `ManualExecutionGate`（`run.Gate = hostGate`），因此普通宿主闸门能被正确驱动；只有当宿主的闸门*不是*运行停驻的那个时才报错。**`StopCompiledRun` 没有此守卫** —— 它取消 token，无论闸门是什么都有效。

## 4. 停止与继续 —— `StopCompiledRun`

```text
StopCompiledRun(handle)  → 正在驱动的节点完成，运行在该边界以 outcome Cancelled 结束，
                           它留下的检查点保留在作用域存储中。
```

| | 结束运行？ | Token | 如何继续 |
|---|---|---|---|
| `PauseCompiledRun` | 否 —— 持有运行 | 未取消 | `ResumeCompiledRun` |
| `StopCompiledRun` | 是，作为 `Cancelled`（不是 `Failed`） | 已取消 | `ContinueCompiledWorkflow` 读取它留下的检查点 |

**预期结果：** `StopCompiledRun` 后结束状态为 `outcome:"Cancelled"`；随后 `ContinueCompiledWorkflow` 启动新句柄并运行到 `Completed`。

## 5. 失败与日志随结果一起返回

两个运行入口都以记录形式报告 `failures`，并把 `logFile` 报告为绝对路径。会话上启用重试策略后（`WithSessionConfiguration(ctx => ctx.RetryPolicy = ...)`），数组同时携带 `"Warning"` 与 `"Error"` 级别，日志文件包含重试行（`"[Retry 1]"`）。来源：`CompiledRunControlTests.TheFailureRecords_AndTheLogFile_TravelWithTheResult`。

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。曾有一次 2026-10-01 的 `CompiledRunControlTests` 记录（387 项），但它早于权限模式重构，不作为当前证据。
- ⚠️ **`RunsOnOurGate` 守卫**与**40 行日志尾部**仅对照源码核验 —— `Agent/**` 中没有测试覆盖它们（测试文件自身的备注也如此说明）。它们引自 `WorkflowAgentToolkit.cs`。
