# Data Flow — Workflow Agent

Four sequence diagrams trace the main data flows of the AI control layer. PlantUML syntax is used so the diagrams can be rendered by any PlantUML server.

## 1. Agent tool call flow

A user message is passed to the agent. On a tool call, `TrackedAIFunction` invokes the underlying `AIFunction`, the tool mutates the tree through a component command, and `WorkflowStateTracker` snapshots/diffs so the agent can observe change.

```plantuml
@startuml
    participant User
participant "IAIAgent" as Agent
participant "TrackedAIFunction" as Tool
participant "WorkflowAgentToolkit" as Toolkit
participant "WorkflowAgentScope" as Scope
participant "IWorkflowTreeViewModel" as Tree
participant "WorkflowStateTracker" as Tracker

    User -> Agent: agent.RunAsync(message, session, runOptions)
    activate Agent
    Agent -> Tool: invoke tool (e.g. CreateNode, ConnectByProperty)
    activate Tool
    Tool -> Toolkit: InvokeCoreInnerAsync(args)
    activate Toolkit

    alt pre-flight limit reached (MaxToolCalls / MaxRead / MaxWrite)
        Toolkit --> Tool: {"status":"error","message":"... limit exceeded"}
    else within limits
        Toolkit -> Tree: componentCommand.Execute(param)
        activate Tree
        Tree -> Tree: StandardCreateNode / StandardConnect (undoable pair)
        Tree --> Toolkit: command Exited
        deactivate Tree
        Toolkit -> Tracker: TakeSnapshot() / GetChangesSinceLastSnapshot()
        Tracker --> Toolkit: JSON snapshot / diff
    end

    Toolkit --> Tool: result JSON (compact)
    deactivate Toolkit
    Tool -> Toolkit: TrackAsync(name, result)
    Toolkit -> Scope: RaiseToolCalledAsync(name, result, count)
    Scope -> User: ToolCalled event + WithToolCallCallback
    deactivate Tool
    Agent --> User: response text (observes changes via diffs)
    deactivate Agent
@enduml
```

Error path (tool throws): see diagram 4.

*Source: `WorkflowAgentToolkit.cs` `TrackedAIFunction` lines 175-239, `TrackAsync` lines 261-271; `WorkflowAgentScope.cs` `RaiseToolCalledAsync` lines 444-450.*

## 2. Interaction safety / confirmation flow

When the agent hits an ambiguous or destructive action, the `RequestSelection` / `RequestConfirmation` tools pause the run and delegate to the host handlers. `AllowAlways` approvals are remembered per `operationKey` for the session.

```plantuml
@startuml
participant "IAIAgent" as Agent
participant "RequestSelection / RequestConfirmation" as Tool
participant "WorkflowAgentScope" as Scope
participant "Host Handler (View)" as Handler
    participant User

    Agent -> Tool: invoke interaction tool
    activate Tool

    alt RequestSelection (safety level 1-3, handler registered)
        Tool -> Scope: SelectionHandler(prompt, options, freeTextPrompt, allowMultiSelect)
        activate Scope
        Scope -> Handler: new AgentSelectionEventArgs(prompt, options)
        Handler -> User: dialog (radio / checkboxes / free text)
        User --> Handler: SelectedOption / SelectedOptions / FreeTextResponse
        Handler --> Scope: args completed
        Scope --> Tool: SelectionResult
        deactivate Scope
        Tool --> Agent: {"status":"ok","chosen":...} or cancelled/error
    else RequestConfirmation (operationKey, description)
        Tool -> Scope: ResolveConfirmationAsync(operationKey, description)
        activate Scope
        alt operationKey already AllowAlways (session)
            Scope --> Tool: allowed (no dialog)
        else first request
            Scope -> Handler: new AgentConfirmationEventArgs(key, description)
            Handler -> User: confirmation dialog
            User --> Handler: AllowOnce / AllowAlways / Deny
            Handler --> Scope: args.Result
            Scope -> Scope: remember key when AllowAlways
        end
        deactivate Scope
        alt result == Deny
            Tool --> Agent: {"status":"denied","message":"Do NOT proceed"}
        else allowed
            Tool --> Agent: {"status":"ok","message":"Proceed"}
        end
    end

    deactivate Tool
@enduml
```

If the result is `denied`, the agent must stop and report — it may not substitute an alternative action (Level 3 safety policy).

*Source: `WorkflowAgentScope.cs` `WithSelectionHandler`/`WithConfirmationHandler`/`ResolveConfirmationAsync` lines 387-442; `WorkflowAgentToolkit.cs` `RequestSelection` lines 2106-2147, `RequestConfirmation` lines 2150-2161.*

## 3. MCP handshake

`LoadAsync` installs the server package when needed (idempotent, guarded by a process-wide set + `SemaphoreSlim`), spawns the server over stdio, performs the JSON-RPC MCP handshake and returns the server's tools as `AITool[]`.

```plantuml
@startuml
    participant Host
participant "McpScope" as Mcp
participant "McpStatusViewModel" as Status
participant "CliWrap (npm/pip)" as Shell
participant "StdioClientTransport" as Proc
participant "MCP Server Process" as Server
participant "ModelContextProtocol Client" as SDK

    Host -> Mcp: LoadAsync(configs, ct)
    activate Mcp
    Mcp -> Status: Reset(); SetLoading(true); Track(config)

    alt Npm / Pip mode
        Mcp -> Shell: EnsureNpmPackageAsync / EnsurePipPackageAsync
        activate Shell
        Shell -> Shell: check s_installed[key] under lock
        alt already installed
            Shell --> Mcp: skip (idempotent)
        else fresh install
            Shell -> Shell: npm install / python -m venv + pip install
            Shell --> Mcp: exit 0
        end
        deactivate Shell
    end

    Mcp -> Proc: ConnectServerAsync -> StdioClientTransport (command + args)
    Proc -> Server: spawn process (node/dotnet/python/exe)
    Server --> Proc: stdio pipe
    Proc -> SDK: McpClient.CreateAsync(transport)
    SDK -> Server: JSON-RPC initialize / tools/list
    Server --> SDK: tool schemas
    SDK --> Proc: ListToolsAsync()
    Proc --> Mcp: AITool[]
    Mcp -> Status: State = Connected; ToolCount = N
    Mcp --> Host: AITool[] (merged into ChatOptions.Tools)
    deactivate Mcp
@enduml
```

Error path: a per-server failure sets `State = Error`, raises `ServerError(config, ex)` and contributes zero tools — the batch continues with the remaining servers. Cancellation propagates as `OperationCanceledException`.

*Source: `McpScope.cs` `LoadAsync` lines 163-187, `LoadOneAsync` lines 189-226, `EnsureNpmPackageAsync` lines 296-328, `ConnectServerAsync` lines 378-413.*

## 4. Error path — a tool throws

`TrackedAIFunction.InvokeCoreInnerAsync` wraps the inner invocation in a try/catch. A thrown exception becomes a JSON `{"status":"error"}` instead of propagating to the model as an SDK failure, and the `ToolCalled` callback still fires. The agent's injected Failure Handling Protocol then tells the model to read the message, verify state, and either retry with a different tool or ask the user.

```plantuml
@startuml
participant "IAIAgent" as Agent
participant "TrackedAIFunction" as Tool
participant "AIFunction (tool body)" as Inner
participant "WorkflowAgentScope" as Scope
    participant User

    Agent -> Tool: invoke tool
    activate Tool
    Tool -> Inner: base.InvokeCoreAsync(args)
    activate Inner
    Inner -> Inner: componentCommand.Execute(param)
    Inner --> Tool: throws Exception
    deactivate Inner
    Tool -> Tool: catch -> WorkflowAgentToolkit.Error(...)
    Tool -> Scope: TrackAsync(name, errorJson)
    Scope -> Scope: RaiseToolCalledAsync -> AgentToolCallEventArgs(toolName, errorJson, count)
    Scope -> User: ToolCalled event (host UI sees the error)
    Tool --> Agent: {"status":"error","message":"Tool 'X' threw an unhandled exception: ..."}
    deactivate Tool
    Agent -> Agent: Failure Handling Protocol (read message, verify state)
    alt recoverable (e.g. stale index)
        Agent -> Tool: retry with corrected args / different tool
    else blocked / host policy disabled
        Agent -> Tool: RequestConfirmation (or stop and report plainly)
        Tool --> Agent: result
    end
    Agent --> User: reports blocker in reply (no silent loop)
@enduml
```

Note: `disabled by host policy` errors from `ExecuteNode`/`ExecuteCommandOnNode`/`ExecuteCommandById` are not worked around — the protocol instructs the model to report and let the host enable them.

*Source: `WorkflowAgentToolkit.cs` `InvokeCoreInnerAsync` lines 193-216; `BuildFailureHandlingProtocol` in `WorkflowAgentScope.cs` lines 509-523.*
