# 数据流 —— 编译运行句柄生命周期

`RunCompiledWorkflow` 等待到结束；而一次需要持有、跟进或停止的运行做不到。运行句柄家族在后台启动同一条编译链并返回句柄。本页追踪整个生命周期：启动 → 轮询 → 持有/放开 → 停止/续跑，含两项已记录的行为（句柄退休与 `RunsOnOurGate` 守卫）。

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

== 启动 ==
Agent -> Toolkit: StartCompiledWorkflow(startNodeIndex, seed)
activate Toolkit
Toolkit -> Toolkit: new CompiledRun(handle "run-1", new ManualExecutionGate)
Toolkit -> Ctx: NewSession(seed)
note right of Toolkit
  宿主配置先跑（WithSessionConfiguration）。
  宿主自带 ManualExecutionGate 时被「采纳」
  （run.Gate = hostGate）；否则 context.ExecutionGate ??= run.Gate。
  CheckpointStore ??= 作用域的有效存储。
end note
Toolkit -> Registry: _runs["run-1"] = run
Toolkit -> Engine: DriveAsync(graph)  [Task.Run，后台]
Toolkit --> Agent: {"status":"ok","handle":"run-1","resumed":false}
deactivate Toolkit

== 轮询（跟进） ==
loop 直到 isRunning == false
    Agent -> Toolkit: GetCompiledRunStatus("run-1")
    activate Toolkit
    Toolkit -> Ctx: SnapshotLogs() — 最后 40 行
    Toolkit -> Toolkit: finished = run.Task.IsCompleted
    alt 仍在运行
        Toolkit --> Agent: {"isRunning":true,"outcome":"Unknown","isPaused":..,"logs":[..40]}
    else 已结束 —— 在同一次调用中退休
        Toolkit -> Registry: _runs.Remove("run-1")
        Toolkit -> Toolkit: run.Cts.Dispose()
        Toolkit --> Agent: {"isRunning":false,"outcome":"Completed|Cancelled|Failed"}
        note right of Toolkit
          再问一次现在返回
          "Unknown run handle 'run-1'"。
        end note
    end
    deactivate Toolkit
end

== 持有 / 放开 ==
Agent -> Toolkit: PauseCompiledRun("run-1")
activate Toolkit
Toolkit -> Toolkit: RunsOnOurGate(run)?
alt 宿主自带门（Context.ExecutionGate != run.Gate）
    Toolkit --> Agent: {"status":"error","message":"... held by an execution gate this tool cannot drive ... StopCompiledRun still works."}
else 这把门就是该运行的门
    Toolkit -> Gate: Pause()
    Toolkit --> Agent: {"status":"ok","message":"held at its next node boundary"}
end
deactivate Toolkit
note over Gate
  正在驱动的节点跑完，不启动新的，
  runStatus 变为 "Paused" —— 持有不等于结束
  （isPaused:true 且 isRunning:true）。
end note
Agent -> Toolkit: ResumeCompiledRun("run-1")
Toolkit -> Gate: Resume()
Toolkit --> Agent: {"status":"ok"}

== 停止，然后续跑 ==
Agent -> Toolkit: StopCompiledRun("run-1")
activate Toolkit
note right of Toolkit
  此处无 RunsOnOurGate 守卫：
  CancellationToken.Cancel() 无论哪把门都有效。
end note
Toolkit -> Toolkit: run.Cts.Cancel()
Toolkit --> Agent: {"status":"ok","message":"... ends at the current node boundary."}
deactivate Toolkit
Engine -> Ctx: outcome = Cancelled（非 Failed）
Engine -> Store: 检查点保留
Agent -> Toolkit: ContinueCompiledWorkflow(startNodeIndex, seed)
activate Toolkit
Toolkit -> Store: LoadAsync(CancellationToken.None)
alt 尚无任何检查点
    Toolkit --> Agent: {"status":"error","message":"There is no checkpoint to carry on from ..."}
else 存在可续跑之处
    Toolkit -> Engine: RunAsync(graph, context, place)
    Toolkit --> Agent: {"status":"ok","handle":"run-2","resumed":true}
end
deactivate Toolkit
@enduml
```

来源：`WorkflowAgentToolkit.cs`（`StartCompiledAsync`、`DriveAsync`、`GetCompiledRunStatus`、`PauseCompiledRun`、`ResumeCompiledRun`、`StopCompiledRun`、`NewSession`、`RunsOnOurGate`、`GateNotOurs`、`CompiledRun`）；`RunOutcome.cs`；`RuntimeContext.SnapshotLogs`。

## 图中所钉定的行为

- **退休就是回答。** `GetCompiledRunStatus` 只读一次 `run.Task.IsCompleted`，并在同一次调用里于结束时刻丢弃句柄、释放其 `CancellationTokenSource`。回答与退休描述同一状态，因此轮询循环在 `isRunning == false` 时退出，之后的调用是未知句柄。测试：`CompiledRunControlTests.WaitForEndAsync` —— 其唯一出口是 `isRunning == false`。
- **工具驱动的门必须是引擎所等的门。** `NewSession` 采纳宿主的 `ManualExecutionGate`，因此 `PauseCompiledRun` / `ResumeCompiledRun` 操作真实的那把门；当宿主的门*不是*该运行的门时，二者返回错误，而非报告一次没发生的暂停。测试：`AStartedRun_CanBeHeld_LetGo_AndFollowedToItsEnd`；守卫本身**仅源码**（`Agent/**` 中无测试断言它）。
- **停止是取消，不是失败。** `StopCompiledRun` 取消令牌；运行在节点边界以 `outcome: Cancelled` 结束，它留下的检查点正是 `ContinueCompiledWorkflow` 要读的东西 —— 所以被停止的运行可稍后续跑。测试：`AStoppedRun_EndsAsCancelled_AndTheAgentCanCarryOnFromIt`。
- **续跑绝不凭空启动。** 尚无任何写入时它返回 `"no checkpoint"`，而非悄悄启动一次全新运行。测试：`CarryingOn_WithNothingWrittenYet_IsRefused`。
- **失败与日志随结果同行。** 会话配置了重试策略时，`failures` 携带 `Warning` 与 `Error` 记录，`logFile` 是含重试行的绝对路径。测试：`TheFailureRecords_AndTheLogFile_TravelWithTheResult`。

**运行声明：** 上述四个 `CompiledRunControlTests` 在 2026-10-01 的确定性套件中通过（`已通过! 失败: 0，通过: 387`）；`RunsOnOurGate` 守卫与 40 行日志尾巴仅对照源码核验。
