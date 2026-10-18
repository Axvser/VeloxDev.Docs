# 数据流 —— 子代理派发（`SpawnSubAgent` → `WaitSubAgents`）

子代理流是一个启动后台运行的工具调用，加第二个收集它的调用。值得追踪的是：所有收窄都**同步发生在第一个工具体内** —— 在宿主 UI 线程上、子代理存在之前 —— 而子代理自己的运行进入线程池。本页从模型的参数列表追到一行已结算的名册，再追读取它的 wait。

```plantuml
@startuml
participant "LLM" as Model
participant "SpawnSubAgent" as Tool
participant "SubAgentScope._parent\n(WorkflowAgentScope)" as Parent
participant "SkillScope / McpScope" as Sources
participant "new child scope" as Child
participant "thread pool" as Pool
participant "SubAgentScope roster" as Roster

Model -> Tool: SpawnSubAgent(task, allowedTools?, allowedSkills?,\nallowedMcpServers?, maxToolCalls?, …)
activate Tool
Tool -> Tool: blank task? -> {"status":"refused"} and no row is created
Tool -> Roster: TrySpawn(request, out refusal)
activate Roster

group depth & lifecycle gates
    Roster -> Roster: _disposed -> refuse "session has been disposed"
    Roster -> Roster: Depth >= MaxDepth -> refuse "the limit is N and this agent is at depth D"
end

group the allowance: a share of the parent's, never the whole of it
    Roster -> Parent: CreateToolkit().Ledger
    Roster -> Roster: remaining = min((MaxToolCalls ?? SpawnBudget) - ledger.Usage,\n                                 rootCap - rootUsage)
    Roster -> Roster: granted = min(requested ?? remaining, remaining - 1)
    alt granted < 1
        Roster --> Tool: refuse (no row created)
    else a request above the grant
        Roster -> Roster: dropped += "maxToolCalls: asked for X, granted Y"
    end
end

group the tool surface: two lists, one switch-off loop
    Roster -> Parent: CreateAllTools() names
    Roster -> Sources: SkillAgentToolkit.ToolNames (if Skills attached)\nSubAgentAgentToolkit.ToolNames (always)\nMcpScope.LoadedTools names (always)
    Roster -> Roster: everyName = distinct union
    Roster -> Roster: available = everyName.Where(parent.IsToolEnabled)
    alt request named its tools
        Roster -> Roster: grantedTools = available ∩ named, canonicalised\nrefusals -> dropped
    else omitted
        Roster -> Roster: grantedTools = available (inherit)
    end
    Roster -> Roster: grantedSkills = parent.Skills.GrantableNames ∩ named
    Roster -> Roster: grantedServers = parent.Mcp.GrantableNames ∩ named
    alt grantedSkills is empty and the parent has a skill source
        Roster -> Roster: strip the skill tools and say why in dropped
    end
end

group the child scope is configured while nothing runs yet
    Roster -> Child: parent.Tree.AsAgentScope()
    Roster -> Child: WithMaxToolCalls(granted), read/write caps clamped,\nWithAllowNodeExecution(opt-in on both sides),\nWithAutoMarkDirty(never beyond the parent)
    loop every name in everyName not granted (MCP names skipped)
        Roster -> Child: WithToolEnabled(name, false)
    end
    Roster -> Child: parent.GrantInteractionTo(child) — permission policy (mode, rules, judge), mode text, both handlers
    Roster -> Child: WithSkills(parentSkills.CreateNarrowed(grantedSkills))
    Roster -> Child: WithMcps(McpScope.CreateGrantedView(parentMcp, grantedServers, grantedTools))
    Roster -> Child: parent.GrantCustomToolsTo(child, grantedTools)
    Roster -> Child: ParentLedger = the parent's ledger\nWithSynchronizationContext(parent.UIContext)\nWithTranscript(new AgentTranscript())\nWithSubAgents(new subsystem at Depth + 1)  — unconditional
end

Roster -> Roster: create the row (grants, dropped list), Children.Add, Republish
Roster -> Pool: Task.Run(RunAsync)
Roster --> Tool: the new id
deactivate Roster
Tool --> Model: {"status":"ok","id":…,"maxToolCalls":…,"dropped":[…],"message":…}
deactivate Tool

note over Model, Pool
  Dispatch and poll, not call and wait: the child may still be on the wire when this reply is rendered.
end note

== the child's own run ==

Pool -> Roster: StartAt then State = Running  (start before state)
Pool -> Pool: scopeFactory(childScope) -> AIAgent, then RunAsync(task, ct)
alt completed
    Pool -> Roster: Finish: payload FIRST (Result, Usage), State = Completed last
else OperationCanceledException
    Pool -> Roster: Finish: State = Cancelled — tokens stay null
else any other exception
    Pool -> Roster: Finish: Error, State = Failed — tokens stay null
end
Roster -> Roster: Republish -> Snapshot, Version++, Changed

== collecting it ==

Model -> Tool: WaitSubAgents(ids?, timeoutMs = 60000)
Tool -> Roster: WaitAsync(ids, timeout)
Roster -> Roster: Select: named ids (a handle this scope never issued is skipped), or every running child
alt there is something to wait for
    Roster -> Roster: WhenAll(runs) versus Task.Delay(timeout)
    note right
      Which one lost is decided by REFERENCE
      comparison: both tasks complete successfully.
    end note
else nothing matches
    Roster --> Tool: empty rows, timedOut = false — returns at once
end
Roster -> Roster: RefreshCallCounts -> Republish
Roster --> Tool: rows as they stand
Tool --> Model: {"status":"ok","timedOut":…,"agents":[…,"result" (cut at 4000), "dropped"…]}
@enduml
```

说明：

- **`Task.Run` 之前的一切与其他 spawn、与面板串行**，因为它发生在名册线程上。只有子代理自己的运行被交出去 —— 这让 spawn 可像任何只读工具调用一样处理，而子代理并行工作。
- **`SpawnSubAgent` 被归类为只读**（`SubAgentAgentToolkit.ToolNames` 并入 workflow 工具包的查询列表），因此 spawn 与 wait 记入读计数，绝不标脏。`SubAgentBudgetTests.ASpawnIsAQuery_AndSoIsNotChargedToTheMutationBudget` 断言两个方向，包括读预算耗尽时 spawn 被拒、写预算耗尽时不受影响。
- **spawn 本身是对共享锅的一次调用**，因此授予是 `remaining - 1` 而非 `remaining`：即使那次记账尚未发生，`- 1` 也让递减授予不变量成立。
- **子代理从第一次调用起就记在树上**，因为 `ParentLedger` 在工具包存在前设置。`SubAgentBudgetTests.AChildsCalls_AreCountedOnTheRootsLedger` 断言根用量等于 spawn 加子代理调用。
- **被拒的 spawn 不留下行。** 拒绝是 JSON 对象，模型应读 `message`；没有任何东西被半创建。
- **子代理自己的名册起初为空**，只有它自己派发时才填充；这里没有任何东西让兄弟句柄可达。

> 源码：`SubAgentScope.cs`（`TrySpawn`、`RunAsync`、`Finish`、`WaitAsync`）；`SubAgentAgentToolkit.cs`（五个工具）；`WorkflowAgentScope.cs`（`GrantInteractionTo`、`GrantCustomToolsTo`、`WithSubAgents`）；`ToolCallLedger.cs`。测试：`SubAgentDispatchTests`、`SubAgentBudgetTests`、`SubAgentHierarchyTests`、`SubAgentCapabilityGrantTests`。
