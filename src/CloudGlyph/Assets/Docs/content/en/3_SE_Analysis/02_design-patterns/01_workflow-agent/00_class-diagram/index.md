# Workflow Agent — Design Patterns — Class Diagram

The class diagram below shows the real participant set of the agent control layer. The left column is the workflow-control core (`WorkflowAgentScope` → `WorkflowAgentToolkit` → tracked tools + state tracker + introspection helpers), the right column is the MCP adapter surface, and the bottom row is the `CompilerEx` execution model that the run/result tools reuse.

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

Key structural facts:

- **One scope owns one toolkit.** `WorkflowAgentScope` is the fluent builder; `CreateToolkit()` returns a `WorkflowAgentToolkit` bound to the same tree (`WorkflowAgentToolkit.cs`, lines 24-31). The toolkit owns a single `WorkflowStateTracker` (`_tracker`, line 27).
- **Every `AIFunction` is decorated.** `CreateTools` wraps each built-in and developer-registered `AIFunction` in the nested `TrackedAIFunction : DelegatingAIFunction` (`WorkflowAgentToolkit.cs`, lines 178-242). Non-`AIFunction` tools (raw MCP client tools) are added as-is.
- **The undo/redo stack stays in Core.** Mutation tools do not fabricate undo entries — they dispatch `IWorkflow*ViewModel` component commands (`SetAnchorCommand`, `CreateNodeCommand`, `DeleteCommand`, `SendConnectionCommand`, …). `ComponentPatcher` rejects any property that has a backing command.
- **Run/result reuse the compiler.** `RunCompiledWorkflow` and `GetNodeResult` both funnel through `RunCompiledRoleAsync`, which calls `new CompilerViewModel().CompileAsync(node, role)` and then `new RuntimeEngine().RunAsync(graph, context, ct)` (`WorkflowAgentToolkit.cs`, lines 1804-1861). `CompileRole.Root` = whole chain from the start node; `CompileRole.Terminal` = a single node's ancestor cone with `RuntimeContext.Target`/`TargetReached` set.
- **Security is code-enforced.** `WithAllowNodeExecution` and `WithAllowedGenericCommands` are property-backed gates read by the tools; disabled means a structured `error` result, not a prompt hint.

> Source files: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`, `.../Workflow/WorkflowStateTracker.cs`, `.../Workflow/Functions/WorkflowAgentToolkit.cs`, `.../Workflow/Functions/CommandInvoker.cs`, `.../Workflow/Functions/ComponentPatcher.cs`, `.../Workflow/Functions/TypeIntrospector.cs`, `.../Agent/MCP/McpScope.cs`, `.../Agent/MCP/McpAgentToolkit.cs`; compile types under `VeloxDev.Core.WorkflowSystem.CompilerEx` in `Src/Core/VeloxDev.Core`.
