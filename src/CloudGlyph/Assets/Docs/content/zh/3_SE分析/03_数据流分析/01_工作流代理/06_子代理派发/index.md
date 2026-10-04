# 数据流分析 — 子代理派发（`SpawnSubAgent` → `WaitSubAgents`）

子代理这条流是「一次工具调用启动一次后台运行，第二次工具调用把它收回来」。它值得追踪的地方在于：**全部收窄都同步发生在第一个工具体内** —— 在宿主的 UI 线程上、在孩子存在之前 —— 而孩子自己的运行被交给线程池。本页跟踪一次 spawn，从模型给出的参数一直到落定的名册行，然后是读它的那次等待。

```plantuml
@startuml
participant "LLM" as Model
participant "SpawnSubAgent" as Tool
participant "SubAgentScope._parent\n(WorkflowAgentScope)" as Parent
participant "SkillScope / McpScope" as Sources
participant "新建的子作用域" as Child
participant "线程池" as Pool
participant "SubAgentScope 名册" as Roster

Model -> Tool: SpawnSubAgent(task, allowedTools?, allowedSkills?,\nallowedMcpServers?, maxToolCalls?, …)
activate Tool
Tool -> Tool: task 为空？-> {"status":"refused"}，且不创建任何行
Tool -> Roster: TrySpawn(request, out refusal)
activate Roster

group 深度与生命周期闸门
    Roster -> Roster: _disposed -> 拒绝 "session has been disposed"
    Roster -> Roster: Depth >= MaxDepth -> 拒绝 "the limit is N and this agent is at depth D"
end

group 额度：父的一份份额，绝不是全部
    Roster -> Parent: CreateToolkit().Ledger
    Roster -> Roster: remaining = min((MaxToolCalls ?? SpawnBudget) - ledger.Usage,\n                                 rootCap - rootUsage)
    Roster -> Roster: granted = min(requested ?? remaining, remaining - 1)
    alt granted < 1
        Roster --> Tool: 拒绝（不创建任何行）
    else 请求值高于授予值
        Roster -> Roster: dropped += "maxToolCalls: asked for X, granted Y"
    end
end

group 工具面：两份名单，一个关停循环
    Roster -> Parent: CreateAllTools() 的工具名
    Roster -> Sources: SkillAgentToolkit.ToolNames（挂了 Skills 时）\nSubAgentAgentToolkit.ToolNames（无条件）\nMcpScope.LoadedTools 的工具名（无条件）
    Roster -> Roster: everyName = 去重后的并集
    Roster -> Roster: available = everyName.Where(parent.IsToolEnabled)
    alt 请求点名了工具
        Roster -> Roster: grantedTools = available ∩ 名单，并规范化\n每条拒绝 -> dropped
    else 省略
        Roster -> Roster: grantedTools = available（继承）
    end
    Roster -> Roster: grantedSkills = parent.Skills.GrantableNames ∩ 名单
    Roster -> Roster: grantedServers = parent.Mcp.GrantableNames ∩ 名单
    alt grantedSkills 为空且父有技能源
        Roster -> Roster: 收走技能工具，并在 dropped 里说明原因
    end
end

group 子作用域在「什么都还没跑」时被配置完
    Roster -> Child: parent.Tree.AsAgentScope()
    Roster -> Child: WithMaxToolCalls(granted)、读/写档位夹取、\nWithAllowNodeExecution(两侧都要点头)、\nWithAutoMarkDirty(绝不超出父)
    loop everyName 中每个未被授予的名字（MCP 名字跳过）
        Roster -> Child: WithToolEnabled(name, false)
    end
    Roster -> Child: parent.GrantInteractionTo(child) —— 等级、覆盖表、两个处理器
    Roster -> Child: WithSkills(parentSkills.CreateNarrowed(grantedSkills))
    Roster -> Child: WithMcps(McpScope.CreateGrantedView(parentMcp, grantedServers, grantedTools))
    Roster -> Child: parent.GrantCustomToolsTo(child, grantedTools)
    Roster -> Child: ParentLedger = 父的账本\nWithSynchronizationContext(parent.UIContext)\nWithTranscript(new AgentTranscript())\nWithSubAgents(Depth + 1 处的新子系统) —— 无条件
end

Roster -> Roster: 建行（授予项、dropped 清单）、Children.Add、Republish
Roster -> Pool: Task.Run(RunAsync)
Roster --> Tool: 新的 id
deactivate Roster
Tool --> Model: {"status":"ok","id":…,"maxToolCalls":…,"dropped":[…],"message":…}
deactivate Tool

note over Model, Pool
  派发加轮询，而不是调用即等待：这份回复被渲染时，孩子可能还在网络上。
end note

== 孩子自己那次运行 ==

Pool -> Roster: 先 StartedAt、再 State = Running（先开始后状态）
Pool -> Pool: scopeFactory(childScope) -> AIAgent，然后 RunAsync(task, ct)
alt 完成
    Pool -> Roster: Finish：载荷在前（Result、Usage），State = Completed 最后
else OperationCanceledException
    Pool -> Roster: Finish：State = Cancelled —— token 留 null
else 其他任何异常
    Pool -> Roster: Finish：Error、State = Failed —— token 留 null
end
Roster -> Roster: Republish -> Snapshot、Version++、Changed

== 把它收回来 ==

Model -> Tool: WaitSubAgents(ids?, timeoutMs = 60000)
Tool -> Roster: WaitAsync(ids, timeout)
Roster -> Roster: Select：点名的 id（本作用域从未发出的句柄被跳过），或每个在跑的孩子
alt 有可等的东西
    Roster -> Roster: WhenAll(各次运行) 与 Task.Delay(timeout) 赛跑
    note right
      谁输了靠引用比较判定：
      两个任务都会成功完成。
    end note
else 一个都不匹配
    Roster --> Tool: 空名册，timedOut = false —— 立刻返回
end
Roster -> Roster: RefreshCallCounts -> Republish
Roster --> Tool: 当下的名册
Tool --> Model: {"status":"ok","timedOut":…,"agents":[…,"result"（截断到 4000）,"dropped"…]}
@enduml
```

几点说明：

- **`Task.Run` 之前的一切都与另一次 spawn、以及面板串行**，因为它发生在名册线程上。被交出去的只有孩子自己那次运行 —— 这正是「一次 spawn 可以像其他只读工具调用一样被对待，而孩子在并行干活」的原因。
- **`SpawnSubAgent` 被归为只读**（`SubAgentAgentToolkit.ToolNames` 并入工作流工具包的查询清单），所以一次 spawn 与一次等待都记在**读**计数器上，绝不会标脏工作流图。`SubAgentBudgetTests.ASpawnIsAQuery_AndSoIsNotChargedToTheMutationBudget` 两个方向都断言了，包括「读预算花光时 spawn 被拒」与「变更预算花光时 spawn 不受影响」。
- **spawn 本身也是一次调用，从同一口锅里扣**，这就是授予写成 `remaining - 1` 而不是 `remaining` 的原因：那个 `- 1` 让递减授予的不变式即便那次记账尚未发生也依然成立。
- **孩子从它的第一次调用起就记在树上**，因为 `ParentLedger` 在工具包存在之前就设好了。`SubAgentBudgetTests.AChildsCalls_AreCountedOnTheRootsLedger` 断言根的用量等于那次 spawn 加上孩子的那次调用。
- **被拒绝的 spawn 不留下任何行。** 拒绝是一个 JSON 对象，且期望模型去读 `message`；没有任何半成品被留在那里。
- **孩子自己的名册一开始是空的**，只有它自己去派发时才会被填；这里没有任何一步让兄弟的句柄变得可达。

> 源码：`SubAgentScope.cs`（`TrySpawn` 387-606、`RunAsync` 781-806、`Finish` 815-839、`WaitAsync` 891-906）；`SubAgentAgentToolkit.cs`（五个工具，85-229）；`WorkflowAgentScope.cs`（`GrantInteractionTo` 283-296、`GrantCustomToolsTo` 251-264、`WithSubAgents` 1788-1804）；`ToolCallLedger.cs`。测试：`SubAgentDispatchTests`、`SubAgentBudgetTests`、`SubAgentHierarchyTests`、`SubAgentCapabilityGrantTests`。
