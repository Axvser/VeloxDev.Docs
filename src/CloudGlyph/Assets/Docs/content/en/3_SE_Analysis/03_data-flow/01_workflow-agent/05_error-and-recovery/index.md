# Data Flow — Error & Recovery

When a tool body throws, `TrackedAIFunction.InvokeCoreInnerAsync` converts the exception into a compact JSON `{"status":"error"}` instead of surfacing an SDK failure, and tracking (counters + `ToolCalled`) still fires. The agent then applies the injected Failure Handling Protocol: read `message`/`reasons`/`hint`/`preferredAlternative`, verify current state, and retry with a different tool — or ask the user. Tools disabled by host policy are reported, never worked around.

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
Tool -> Tool: TrackAsync(name, errorJson) (counters ++)
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

Notes:

- Unmounted-component operations are silent no-ops by framework design; the protocol tells the model to verify mount state (`ListNodes` / `GetNodeDetail`) before retrying.
- Gated tools (`ExecuteNode`, `ExecuteCommandOnNode`, `ExecuteCommandById`, `RunCompiledWorkflow`, `GetNodeResult`) return a structured `disabled by host policy` error when the host has not enabled them; the model is instructed not to bypass it.

> Source: `WorkflowAgentToolkit.cs`, `TrackedAIFunction.InvokeCoreInnerAsync` lines 196-219; `WorkflowAgentScope.cs`, `BuildFailureHandlingProtocol` lines 509-523.
