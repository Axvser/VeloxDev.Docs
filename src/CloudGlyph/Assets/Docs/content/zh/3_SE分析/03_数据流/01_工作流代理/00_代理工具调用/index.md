# 数据流 —— 一次工具调用，端到端

每次工具调用 —— 内置、开发者注册、MCP 来源、技能来源或子代理 spawn —— 都走同一条路径：模型调用 `TrackedAIFunction`，它编组到宿主上下文并把调用交给作用域的**唯一共享 `ToolPipeline`**，后者在工具体运行前施加预算/宿主策略拒绝与权限闸门。函数体派发组件命令，完成事件由 accounting 阶段计数。

```plantuml
@startuml
!theme plain

actor "Host UI" as Host
participant "AIAgent\n(AgentPipelineAgent)" as Agent
participant "WorkflowAgentContextProvider" as Provider
participant "TrackedAIFunction" as Tracked
participant "ToolPipeline\n(SharedTools)" as Gate
participant "Tool body" as Tool
participant "IWorkflowTreeViewModel\n(component commands)" as Tree
participant "AccountingStage" as Acct
participant "ToolCallLedger" as Ledger

Host -> Agent: RunAsync(prompt, session)
activate Agent
Agent -> Provider: ProvideAIContextAsync(invocation)
activate Provider
Provider -> Provider: BuildContext() — cached on ContextKey
note right of Provider
  Unchanged turn: no lock, no allocation,
  the very same AIContext instance returns.
end note
Provider --> Agent: AIContext(instructions, tools)
deactivate Provider

Agent -> Agent: model decides to call a tool
Agent -> Tracked: InvokeCoreAsync(name, args)
activate Tracked
Tracked -> Tracked: marshal onto SynchronizationContext
Tracked -> Gate: OnEventAsync(AgentToolCallStarted)
activate Gate

Gate -> Gate: Refuse(name) — CheckInvocation / IsToolEnabled / PermissionPolicy
alt refused (limit reached, tool switched off, or a Deny decision)
    Gate --> Tracked: refusal message
    Tracked -> Agent: AgentToolCallCompleted(name, msg, Refused)
    note right of Tracked
      The body never ran and the call is NOT counted.
    end note
else allowed
    Gate -> Gate: Confirm(name) — PermissionPolicy.Evaluate; Ask needs a handler
    alt denied, or no handler (an unanswerable prompt denies)
        Gate --> Tracked: "not approved by the user" message
        Tracked -> Agent: AgentToolCallCompleted(name, msg, Refused)
    else approved
        Gate -> Tool: run the tool body
        activate Tool
        Tool -> Tree: dispatch exactly one component command
        activate Tree
        Tree --> Tool: command result
        deactivate Tree
        Tool --> Gate: compact JSON result
        deactivate Tool
        Gate --> Tracked: result
        Tracked -> Agent: AgentToolCallCompleted(name, result, Succeeded)
        deactivate Tracked

        Agent -> Acct: OnEventAsync(Completed: Succeeded)
        activate Acct
        Acct -> Ledger: Spend(isQuery)
        activate Ledger
        Ledger -> Ledger: increment total/read/write
        Ledger -> Ledger: Outer?.Spend(isQuery) — the whole chain
        deactivate Ledger
        Acct -> Host: RaiseToolCalledAsync(name, result, count)
        Acct -> Tree: MarkDirty() — only when AutoMarkDirty && !query
        deactivate Acct
    end
    deactivate Gate
end

Agent --> Host: AgentResponse
deactivate Agent
@enduml
```

源码：`WorkflowAgentToolkit.cs`（`CreateTools`、`CheckInvocation`、`ConfirmMutationAsync`、`AccountAsync`、`CreateAccountingStage`）、`TrackedAIFunction.cs`、`ToolPipeline.cs`、`WorkflowAgentContextProvider.cs`。

## 图钉住的事实

- **模型看不到闸门会拒绝的工具。** `CreateTools` 把关闭的工具从列表中过滤掉，**并且** `CheckInvocation` 在调用时拒绝它们 —— 测试 `SwitchedOffTool_IsRefusedAtCallTime_NotJustHidden` 在开关前捕获 `AIFunction`、开关后调用，钉住的是拒绝而非省略。
- **拒绝发生在函数体之前。** 被拒绝或失败的调用从不运行函数体，因此不计数：`AccountingStage` 只统计 `AgentToolOutcome.Succeeded`。测试 `ARefusedTool_IsReportedToTheModel_AndDoesNotCountAsACall` 断言 `CallCount == 0`。
- **一个策略，每个切片。** 闸门实例与 MCP、技能提供器共享，因此 MCP 来源的工具与内置工具记入同一账本、受同一开关约束。
- **`ResetToolCallLimit` 豁免。** 它通过拒绝钩子（逃生舱挺过它本就为之存在的闸门），在用户同意后清零**整条**账本链，且自身从不计数。
- **消费沿链行走。** 对派生子代理，`Spend` 递归到 `Outer`，因此根账本的总数是整棵树任何位置发生的调用数。
