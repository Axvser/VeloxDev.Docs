# 数据流 — 工作流代理

四个时序图追踪 AI 控制层的主要数据流。使用 PlantUML 语法，可在任意 PlantUML 服务器渲染。

## 1. Agent 工具调用流

用户消息传给 Agent。工具被调用时，`TrackedAIFunction` 调用底层 `AIFunction`，工具通过组件命令变更树，`WorkflowStateTracker` 做快照/差异，让 Agent 观察变化。

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

错误路径（工具抛出）：见时序图 4。

*源码：`WorkflowAgentToolkit.cs` 的 `TrackedAIFunction` 第 175-239 行、`TrackAsync` 第 261-271 行；`WorkflowAgentScope.cs` 的 `RaiseToolCalledAsync` 第 444-450 行。*

## 2. 交互安全 / 确认流

Agent 遇到有歧义或破坏性操作时，`RequestSelection` / `RequestConfirmation` 工具暂停运行并委托给宿主处理器。`AllowAlways` 审批按 `operationKey` 在会话内记住。

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

若结果是 `denied`，Agent 必须停下并报告 —— 不得用替代操作蒙混（第 3 档安全策略）。

*源码：`WorkflowAgentScope.cs` 的 `WithSelectionHandler`/`WithConfirmationHandler`/`ResolveConfirmationAsync` 第 387-442 行；`WorkflowAgentToolkit.cs` 的 `RequestSelection` 第 2106-2147 行、`RequestConfirmation` 第 2150-2161 行。*

## 3. MCP 握手

`LoadAsync` 在需要时安装服务器包（幂等，进程级集合 + `SemaphoreSlim` 守卫）、经 stdio 启动服务器、完成 JSON-RPC MCP 握手，并把服务器工具作为 `AITool[]` 返回。

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

错误路径：单服务器失败把状态置为 `Error`、触发 `ServerError(config, ex)` 并贡献 0 个工具 —— 批次继续处理其余服务器。取消以 `OperationCanceledException` 传播。

*源码：`McpScope.cs` 的 `LoadAsync` 第 163-187 行、`LoadOneAsync` 第 189-226 行、`EnsureNpmPackageAsync` 第 296-328 行、`ConnectServerAsync` 第 378-413 行。*

## 4. 错误路径 —— 工具抛出异常

`TrackedAIFunction.InvokeCoreInnerAsync` 用 try/catch 包住内部调用。抛出的异常变成 JSON `{"status":"error"}` 而非作为 SDK 失败传播给模型，且 `ToolCalled` 回调仍然触发。注入的失败处理协议随后告诉模型读 message、核对状态，改用别的工具重试或询问用户。

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

注意：`ExecuteNode`/`ExecuteCommandOnNode`/`ExecuteCommandById` 返回的 `disabled by host policy` 错误不许绕开 —— 协议指示模型报告并让宿主按需启用。

*源码：`WorkflowAgentToolkit.cs` 的 `InvokeCoreInnerAsync` 第 193-216 行；`WorkflowAgentScope.cs` 的 `BuildFailureHandlingProtocol` 第 509-523 行。*
