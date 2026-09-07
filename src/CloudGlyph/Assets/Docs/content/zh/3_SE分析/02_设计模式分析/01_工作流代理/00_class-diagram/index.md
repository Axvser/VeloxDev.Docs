# Workflow Agent — 设计模式 — 类图

下图展示代理控制层真实的参与者集合。左侧是工作流控制核心（`WorkflowAgentScope` → `WorkflowAgentToolkit` → 受追踪工具 + 状态追踪器 + 内省辅助），右侧是 MCP 适配器表面，底部是 run/result 工具复用的 `CompilerEx` 执行模型。

```mermaid
classDiagram
    class AgentEx {
        +AsAgentScope(tree) WorkflowAgentScope
    }
    class WorkflowAgentScope {
        <<IAgentToolCallNotifier>>
        +IWorkflowTreeViewModel Tree
        +int? MaxToolCalls
        +bool AutoMarkDirty
        +event ToolCalled
        +WithPromptLanguage(AgentLanguages)
        +WithOutputLanguage(AgentLanguages)
        +WithMaxToolCalls(int)
        +WithMaxReadToolCalls(int)
        +WithMaxWriteToolCalls(int)
        +WithAutoMarkDirty(bool)
        +WithAllowNodeExecution(bool)
        +WithAllowedGenericCommands(params string[])
        +WithSynchronizationContext(SynchronizationContext)
        +WithToolCallCallback(Func~AgentToolCallEventArgs, Task~)
        +WithSelectionHandler(Func~AgentSelectionEventArgs, Task~)
        +WithConfirmationHandler(Func~AgentConfirmationEventArgs, Task~)
        +WithInteractionSafety(int)
        +WithInteractionSafetyPrompt(int, string)
        +WithTools(string?, params AITool[])
        +WithQueryTools(string?, params AITool[])
        +WithAutoDiscovery(Assembly, AgentLanguages)
        +WithEnums() WithInterfaces() WithComponents() WithData()
        +ProvideAllContexts() string
        +ProvideProgressiveContextPrompt() string
        +ProvideFrameworkContext() string
        +ProvideCustomerContext() string
        +ProvideFrameworkDataContext() string
        +ProvideCustomerDataContext() string
        +CreateToolkit() WorkflowAgentToolkit
        +ProvideTools() IList~AITool~
    }
    class WorkflowAgentToolkit {
        -WorkflowStateTracker _tracker
        -int _toolCallCount _readToolCallCount _writeToolCallCount
        +CreateTools(categories) IList~AITool~
    }
    class WorkflowStateTracker {
        -JObject _lastSnapshot
        -long _version
        +TakeSnapshot() string
        +GetChangesSinceLastSnapshot() string
    }
    class TrackedAIFunction {
        <<Decorator>>
        -InvokeCoreAsync(args, ct)
        -TrackAsync(name, result)
    }
    class CommandInvoker {
        +DiscoverCommands(component) IReadOnlyList~CommandDescriptor~
        +Invoke(component, name, jsonParameter) string
    }
    class ComponentPatcher {
        +ApplyPatch(target, jsonPatch) string
    }
    class TypeIntrospector {
        +ResolveType(fullName) Type
        +GetTypeSchema(type) string
    }
    class AgentContextCollector {
        +GetAgentContext(member, lang) string[]
        +GetEnumContext(type, lang) string
        +GetClassContext(type, lang) string
    }
    class AgentEmbeddedResources {
        +ReadAllReferences(system, lang) string
        +ReadAllSkills(system, lang) string
        +ReadSafety(system, name, lang) string
    }
    class McpScope {
        +McpStatusViewModel Status
        +IReadOnlyList~AITool~ LoadedTools
        +event ServerError
        +LoadAsync(servers, ct) Task~AITool[]~
        +UnloadServer(name) bool
        +GetServerTools(name) IReadOnlyList~AITool~
    }
    class McpAgentToolkit {
        +CreateTools() IList~AITool~
    }
    class McpServerConfiguration {
        +string Name
        +McpServerRunMode RunMode
        +string Package
        +string? Version
        +string[] Arguments
        +string? Endpoint
        +object? Options
    }
    class McpServerRunMode {
        <<enum>>
        Npm Npx Uvx Dotnet Pip Exe Http
    }
    class McpServerStatus {
        <<enum>>
        NotStarted Installing Connecting Connected Error
    }
    class CompilerViewModel {
        +CompileAsync(node, role) IReadOnlyList~CompiledGraph~
    }
    class RuntimeEngine {
        +RunAsync(graph, context, ct) Task
    }
    class RuntimeContext {
        +object? Data
        +IWorkflowNodeViewModel Target
        +bool TargetReached
        +string Status
        +bool EndedWithError
        +IReadOnlyList~string~ Logs
    }
    class CompileRole {
        <<enum>>
        Root Terminal
    }
    class IWorkflowTreeViewModel {
        <<interface>>
        +Nodes
        +Links
        +LinksMap
        +UndoCommand
        +RedoCommand
        +SendConnectionCommand
        +ReceiveConnectionCommand
    }
    class IWorkflowIdentifiable {
        <<interface>>
        +RuntimeId
    }
    class AIFunction {
        <<abstract>>
    }
    class DelegatingAIFunction {
        <<abstract>>
    }
    class AITool {
        <<abstract>>
    }

    AgentEx ..> WorkflowAgentScope : AsAgentScope()
    WorkflowAgentScope ..> WorkflowAgentToolkit : CreateToolkit()
    WorkflowAgentToolkit *-- WorkflowStateTracker : owns
    WorkflowAgentToolkit --> IWorkflowTreeViewModel : operates via commands
    WorkflowAgentToolkit ..> TrackedAIFunction : wraps each AIFunction
    TrackedAIFunction --|> DelegatingAIFunction
    DelegatingAIFunction --|> AIFunction
    AIFunction --|> AITool
    WorkflowAgentToolkit ..> CommandInvoker
    WorkflowAgentToolkit ..> ComponentPatcher
    WorkflowAgentToolkit ..> TypeIntrospector
    WorkflowAgentToolkit ..> AgentContextCollector
    WorkflowAgentScope ..> AgentEmbeddedResources : bilingual prompt docs
    WorkflowAgentToolkit ..> CompilerViewModel : RunCompiledWorkflow / GetNodeResult
    CompilerViewModel ..> RuntimeEngine : graph[0]
    WorkflowAgentToolkit ..> RuntimeContext : Target / TargetReached
    WorkflowAgentToolkit --> CompileRole
    IWorkflowTreeViewModel "1" o-- "many" IWorkflowIdentifiable : stable RuntimeId
    McpAgentToolkit ..> McpScope
    McpScope ..> McpServerConfiguration
    McpScope --> McpServerRunMode
    McpScope --> McpServerStatus
    McpAgentToolkit ..> AITool : server tools
```

关键结构事实：

- **一个作用域拥有一个工具包。** `WorkflowAgentScope` 是流畅构建者；`CreateToolkit()` 返回绑定到同一棵树的 `WorkflowAgentToolkit`（`WorkflowAgentToolkit.cs`，第 24-31 行）。工具包拥有唯一的 `WorkflowStateTracker`（`_tracker`，第 27 行）。
- **每个 `AIFunction` 都被装饰。** `CreateTools` 把每个内置及开发者注册的 `AIFunction` 包装进嵌套的 `TrackedAIFunction : DelegatingAIFunction`（`WorkflowAgentToolkit.cs`，第 178-242 行）。非 `AIFunction` 工具（原始 MCP 客户端工具）按原样加入。
- **撤销/重做栈保留在 Core。** 变更工具不伪造撤销条目——它们派发 `IWorkflow*ViewModel` 组件命令（`SetAnchorCommand`、`CreateNodeCommand`、`DeleteCommand`、`SendConnectionCommand`、……）。`ComponentPatcher` 拒绝任何有对应命令的属性。
- **run/result 复用编译器。** `RunCompiledWorkflow` 与 `GetNodeResult` 都汇入 `RunCompiledRoleAsync`：调用 `new CompilerViewModel().CompileAsync(node, role)`，再用 `new RuntimeEngine().RunAsync(graph, context, ct)`（`WorkflowAgentToolkit.cs`，第 1804-1861 行）。`CompileRole.Root` = 从起始节点开始的整条链；`CompileRole.Terminal` = 单个节点的祖先锥，设置 `RuntimeContext.Target`/`TargetReached`。
- **安全由代码强制。** `WithAllowNodeExecution` 与 `WithAllowedGenericCommands` 是工具读取的属性门；禁用时返回结构化 `error` 结果，而非提示词暗示。

> 源文件：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`、`.../Workflow/WorkflowStateTracker.cs`、`.../Workflow/Functions/WorkflowAgentToolkit.cs`、`.../Workflow/Functions/CommandInvoker.cs`、`.../Workflow/Functions/ComponentPatcher.cs`、`.../Workflow/Functions/TypeIntrospector.cs`、`.../Agent/MCP/McpScope.cs`、`.../Agent/MCP/McpAgentToolkit.cs`；`VeloxDev.Core.WorkflowSystem.CompilerEx` 中的编译类型位于 `Src/Core/VeloxDev.Core`。
