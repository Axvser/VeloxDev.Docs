# 数据流 —— 错误与恢复

当工具体抛异常时，`TrackedAIFunction.InvokeCoreInnerAsync` 把异常转成紧凑 JSON `{"status":"error"}`，而不是让 SDK 失败浮现；跟踪（计数 + `ToolCalled`）仍会触发。agent 随后执行注入的 Failure Handling Protocol：读取 `message`/`reasons`/`hint`/`preferredAlternative`，核实当前状态，换一个工具重试 —— 或者询问用户。被宿主策略禁用的工具会被报告，绝不绕过。

```plantuml
@startuml
actor User
participant "IAIAgent" as Agent
participant "TrackedAIFunction" as Tool
participant "AIFunction (tool body)" as Inner
participant "WorkflowAgentScope" as Scope

Agent -> Tool: invoke tool
activate Tool
Tool -> Inner: base.InvokeCoreAsync(args)
activate Inner
Inner -> Inner: componentCommand.Execute(param)
Inner --> Tool: throws Exception
deactivate Inner

Tool -> Tool: catch -> WorkflowAgentToolkit.Error("Tool 'X' threw an unhandled exception: ...")
Tool -> Tool: ReportAsync(name, errorJson) (counters ++)
Tool -> Scope: RaiseToolCalledAsync(name, errorJson, count)
Scope -> User: ToolCalled event (host UI sees the error)
Tool --> Agent: {"status":"error","message":"Tool 'X' threw ..."}

Agent -> Agent: Failure Handling Protocol: read message; verify state via ListNodes/GetNodeDetail/GetComponentContext
alt recoverable (e.g. stale node index)
    Agent -> Tool: retry with corrected args / different tool
else blocked or host-policy disabled
    Agent -> Tool: RequestConfirmation (or stop and report plainly)
    Tool --> Agent: result
end
Agent --> User: reports the blocker in its reply (no silent loop)
deactivate Tool
@enduml
```

说明：

- 未挂载组件的操作按框架设计是静默空操作；协议让模型在重试前核实挂载状态（`ListNodes` / `GetNodeDetail`）。
- 受闸控的工具（`ExecuteNode`、`ExecuteCommandOnNode`、`ExecuteCommandById`、`RunCompiledWorkflow`、`GetNodeResult`）在宿主未启用时返回结构化的 `disabled by host policy` 错误；模型被告知不要绕过。
- 权限拒绝（`Deny`）同样以结构化错误返回，并点名模式或规则，而不是预算消息。

> 源码：`Agent/TrackedAIFunction.cs`（`InvokeCoreInnerAsync`）；`WorkflowAgentScope.cs`（`DescribePermissionRefusal` 与失败处理协议提示）。
