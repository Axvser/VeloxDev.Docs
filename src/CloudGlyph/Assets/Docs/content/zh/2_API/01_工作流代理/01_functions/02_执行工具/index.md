# 函数 · 执行工具

类别 `Execution` —— **12 个工具**，全部受 `WithAllowNodeExecution(true)` 闸控。它们横跨三个执行层级：节点 EXEC、编译链、编译运行家族。闸门关闭时每个都返回 `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).`

## 节点层（4）

| 工具 | 签名 | 用途 |
|---|---|---|
| `ExecuteNode` | `ExecuteNode(int nodeIndex, string? parameter = null)` | 在单节点上运行 `ReceiveCommand` 并**等待**完成。 |
| `ExecuteNodes` | `ExecuteNodes(string nodeIndicesJson, string? parameter = null)` | 对一维索引 JSON 数组运行 `ReceiveCommand`，逐个等待（`completed` + `errors`）。 |
| `BroadcastNode` | `BroadcastNode(int nodeIndex, string? parameter = null)` | 运行 `BroadcastCommand` 向下游转发数据；等待该命令（下游派发为发后即忘）。 |
| `ReverseBroadcastNode` | `ReverseBroadcastNode(int nodeIndex, string? parameter = null)` | 运行 `ReverseBroadcastCommand` 触发上游节点的 `ReceiveCommand`；等待该命令。 |

来源：`WorkflowLifecycleFidelityTests.ExecuteNode_WaitsForCommandCompletion`、`ToolThreadAffinityTests.BuiltInTool_WithAGenuineSuspension_StaysOnTheContext`。

## 链 / 结果层（2）

| 工具 | 签名 | 用途 |
|---|---|---|
| `RunCompiledWorkflow` | `RunCompiledWorkflow(int startNodeIndex, string? seed = null)` | 从起始节点编译（Root 角色）并经引擎驱动整条链；**等待**到结束。 |
| `GetNodeResult` | `GetNodeResult(int nodeIndex, string? seed = null)` | 编译该节点的祖先锥（Terminal 角色）并驱动它；返回 `targetReached` 与该节点的结果。 |

其结果形状与 Terminal 错误契约见 `VeloxDev.AI.Workflow` 的设计页面；下面的运行句柄家族在后台启动同一条链。

## 运行句柄家族（6）

| 工具 | 签名 | 用途 |
|---|---|---|
| `StartCompiledWorkflow` | `StartCompiledWorkflow(int startNodeIndex, string? seed = null)` | 启动一次编译运行并**立即**返回 `handle`；用 `GetCompiledRunStatus` 轮询。 |
| `ContinueCompiledWorkflow` | `ContinueCompiledWorkflow(int startNodeIndex, string? seed = null)` | 启动一次从作用域存储中最近检查点**续跑**的运行。无检查点时返回错误。 |
| `GetCompiledRunStatus` | `GetCompiledRunStatus(string handle)` | 报告运行状态：`isRunning`、`runStatus`、`outcome`、`isPaused`、`attempts`、`endedWithError`、`data`、`failures`、`failureCount`、`logs`（最后 40 行）、`logFile`。**报告某次运行已结束后退休其句柄。** 纯查询。 |
| `PauseCompiledRun` | `PauseCompiledRun(string handle)` | 在该运行的下一个节点边界持有它。当宿主自带执行门（`RunsOnOurGate`）时返回**错误**。 |
| `ResumeCompiledRun` | `ResumeCompiledRun(string handle)` | 让被持有的运行继续（未被持有时为空操作）。同样的 `RunsOnOurGate` 守卫。 |
| `StopCompiledRun` | `StopCompiledRun(string handle)` | 停止运行：它在当前节点边界以 `outcome: Cancelled` 结束，检查点保留。**无门守卫。** |

### 句柄语义

- 句柄为 `run-{n}`（每个工具包一个计数器）；未知句柄返回 `Unknown run handle '<h>'. Handles come from StartCompiledWorkflow / ContinueCompiledWorkflow and belong to one scope; list the run you started rather than inventing one.`
- 尚无任何写入时的 `ContinueCompiledWorkflow`：`There is no checkpoint to carry on from: nothing has been written yet. Run the workflow once (StartCompiledWorkflow) and stop it mid-way, then continue.`
- 门不是该运行的门时的 `PauseCompiledRun` / `ResumeCompiledRun`：`Run '<h>' is held by an execution gate this tool cannot drive — the host brought its own. Pause and resume it through the host's controls; StopCompiledRun still works.`
- `GetCompiledRunStatus` 经 `RuntimeContext.SnapshotLogs()` 读取日志尾部，保留最后 `RunStatusLogTail = 40` 行，并在回答「是否结束」的同一次调用里丢弃句柄（释放其 `CancellationTokenSource`）。

**异常：** 不向模型抛任何异常 —— 失败以 JSON `{"status":"error","message":"…"}` 对象返回。

来源：`CompiledRunControlTests`（`AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`、`AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`、`CarryingOn_WithNothingWrittenYet_IsRefused`、`TheFailureRecords_AndTheLogFile_TravelWithTheResult`）。

## 示例

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

**预期结果：** 最后一次轮询即终态回答（`isRunning:false`）；其后一次是未知句柄错误。
