# Data Flow — Agent Tool Call

A user message is passed to the agent. On a tool call, `TrackedAIFunction.InvokeCoreAsync` marshals onto the UI context if configured, `InvokeCoreInnerAsync` pre-flights the call limits and runs the underlying `AIFunction`. The tool body mutates the tree through exactly one component command and awaits real completion; afterwards `TrackAsync` raises `ToolCalled` and optionally marks the tree dirty. The framework's undo/redo stack is the single source of truth — the toolkit never submits its own gestures.

```plantuml
@startuml
actor User
participant "IAIAgent" as Agent
participant "TrackedAIFunction" as Tool
participant "AIFunction (tool body)" as Inner
participant "Component command" as Cmd
participant "IWorkflowTreeViewModel" as Tree
participant "WorkflowAgentScope" as Scope

User -> Agent: RunAsync(message, session, runOptions)
activate Agent

Agent -> Tool: InvokeAsync(tool, args)
activate Tool
Tool -> Tool: InvokeCoreAsync: marshal body onto UI context (when configured)
Tool -> Tool: InvokeCoreInnerAsync: reject when Max/Read/Write call limit hit
Tool -> Inner: base.InvokeCoreAsync(args)
activate Inner

Inner -> Cmd: WaitForExitedAsync(cmd, ct) subscribes Exited/Failed
Inner -> Cmd: cmd.Execute(param)  (e.g. SetAnchorCommand / CreateNodeCommand / SendConnectionCommand)
activate Cmd
Cmd -> Cmd: Standard* mutation + Submit only when the command is undoable
Cmd --> Inner: Exited / Failed
deactivate Cmd

Inner --> Tool: compact JSON result (Formatting.None)
deactivate Inner

Tool -> Tool: TrackAsync(name, result)  (counters ++)
Tool -> Scope: RaiseToolCalledAsync(name, result, count)
Scope -> User: ToolCalled event + WithToolCallCallback handler
alt AutoMarkDirty enabled AND tool not a query tool
    Tool -> Tree: Tree.GetHelper().MarkDirty()
end
Tool --> Agent: JSON result (status ok/error/rejected)
deactivate Tool

Agent --> User: response text (uses GetChangesSinceSnapshot diffs to observe change)
deactivate Agent
@enduml
```

Notes:

- Awaiting command completion (`WaitForExitedAsync`, `WaitForCommandAsync`, `WaitForNDispatchesAsync`, `SendReceiveAsync`) means the next tool call never observes a stale-state window.
- Query tools never trigger auto-dirty; a state-observation tool (`TakeSnapshot` / `GetChangesSinceSnapshot`) is a separate, opt-in call.

> Source: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, `TrackedAIFunction` lines 178-242, `TrackAsync` lines 264-281, wait helpers lines 2672-2767; `WorkflowAgentScope.cs`, `RaiseToolCalledAsync` lines 444-450.
