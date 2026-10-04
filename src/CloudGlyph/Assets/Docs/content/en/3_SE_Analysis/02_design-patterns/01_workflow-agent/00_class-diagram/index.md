# Workflow Agent — Design Patterns — Class Diagram

The **scope and its collaborators**. The tool-category hierarchy has its own page: [12 · Tool-Category Hierarchy](../12_tool-category-hierarchy/index.md).

## The scope and its collaborators

```mermaid
classDiagram
    class AgentEx {
        +AsAgentScope(tree) WorkflowAgentScope
    }
    class WorkflowAgentScope {
        <<IAgentToolCallNotifier>>
        +IWorkflowTreeViewModel Tree
        +long Version
        +event Changed
        +AgentPipeline Pipeline
        +WithPromptLanguage(AgentLanguages)
        +WithOutputLanguage(AgentLanguages)
        +WithMaxToolCalls(int)
        +WithMaxReadToolCalls(int)
        +WithMaxWriteToolCalls(int)
        +WithAutoDiscovery(Assembly, AgentLanguages)
        +WithEnums() WithInterfaces() WithComponents() WithData()
        +WithTools(string?, params AITool[])
        +WithQueryTools(string?, params AITool[])
        +WithToolEnabled(string, bool)
        +SetToolEnabled(string, bool) bool
        +WithAllowNodeExecution(bool)
        +WithAllowedGenericCommands(params string[])
        +WithAutoMarkDirty(bool)
        +WithInteractionSafety(int)
        +WithInteractionSafetyPrompt(int, string)
        +WithSelectionHandler(Func~AgentSelectionEventArgs, Task~)
        +WithConfirmationHandler(Func~AgentConfirmationEventArgs, Task~)
        +WithToolApproval(bool)
        +WithSynchronizationContext(SynchronizationContext)
        +WithToolCallCallback(Func~AgentToolCallEventArgs, Task~)
        +WithLogWriter(ILogWriter) WithCheckpointStore(IExecutionCheckpointStore)
        +WithSessionConfiguration(Action~RuntimeContext~)
        +WithTranscript(AgentTranscript)
        +WithSkills(SkillScope) WithMcps(McpScope) WithSubAgents(SubAgentScope)
        +WithTodoTracking() WithAgentModes(AgentModeProviderOptions)
        +WithContextCompaction(int, int)
        +WithContextProvider(Func~WorkflowAgentScope, AIContextProvider~)
        +ProvideProgressiveContextPrompt() string
        +ProvideAllContexts() string
        +CreateToolkit() WorkflowAgentToolkit
        +ProvideTools(WorkflowToolCategory) IList~AITool~
        +CreateContextProviders() IReadOnlyList~AIContextProvider~
    }
    class WorkflowAgentToolkit {
        -WorkflowStateTracker _tracker
        -ToolCallLedger _ledger
        -Dictionary~string, CompiledRun~ _runs
        +CreateTools(WorkflowToolCategory) IList~AITool~
        +CreateAllTools(WorkflowToolCategory) IList~AITool~
        +CreateAccountingStage() IAgentPipelineStage
        +TryGetRun(handle, out run, out error) bool
    }
    class ToolCallLedger {
        +WorkflowAgentScope Owner
        +ToolCallLedger Outer
        +ToolCallLedger Root
        +Spend(bool isQuery)
        +Usage (int,int,int)
        +ResetChain()
    }
    class WorkflowStateTracker {
        -JObject _lastSnapshot
        -long _version
        +TakeSnapshot() string
        +GetChangesSinceLastSnapshot() string
    }
    class WorkflowAgentContextProvider {
        <<AIContextProvider>>
        -Render _published
        +StateKeys IReadOnlyList~string~
        -BuildContext() AIContext
    }
    class TrackedAIFunction {
        <<Decorator>>
        -InvokeCoreAsync(args, ct)
        -InvokeCoreInnerAsync(args, ct)
        -ReportAsync(result, outcome, elapsed, ct)
    }
    class WorkflowToolCategory {
        <<enum>>
        Query Mutation Execution Command Graph
        Layout Analytics State Composite Interaction All
    }
    class AgentPipeline {
        +Stages IReadOnlyList~IAgentPipelineStage~
        +Use(IAgentPipelineStage) AgentPipeline
        +PublishAsync(AgentEvent, ct) ValueTask
        +event StageFailed
    }
    class ToolPipeline {
        +MarshalTo Func~SynchronizationContext~
        +Refuse Func~string,string~
        +Confirm Func~string,CancellationToken,ValueTask~string~~
    }
    class TextPipeline {
        +OnEventAsync(event, next, ct) ValueTask
    }
    class AgentTranscript {
        +Entries ObservableCollection~AgentTranscriptEntry~
        +AppendReasoning(fragment) AgentTranscriptEntry
        +AddToolCall(name, result, outcome) AgentTranscriptEntry
        +ToMarkdown(options) string
    }
    class SkillScope {
        +long Version
        +WithSource(ISkillSource) SkillScope
        +CreateNarrowed(allowed) SkillScope
    }
    class McpScope {
        +long Version
        +McpSelfServiceLevel SelfServiceLevel
        +CreateGrantedView(source, servers, tools) McpScope
    }
    class SubAgentScope {
        +int MaxDepth
        +int SpawnBudget
        +TrySpawn(request, out refusal) string
    }
    class AgentDashboardViewModel {
        +Create(scope) AgentDashboardViewModel
        +SystemTools ObservableCollection~ToolMemberViewModel~
    }
    class AgentMemberViewModel {
        <<abstract>>
        +ApplyToScope(bool)
    }
    class CompilerViewModel {
        +CompileAsync(node, role) IReadOnlyList~CompiledGraph~
    }
    class RuntimeEngine {
        +RunAsync(graph, context, ct, resumeFrom) Task
    }
    class RuntimeContext {
        +RunOutcome Outcome
        +IExecutionGate ExecutionGate
        +bool IsRunning
        +SnapshotLogs() string[]
    }

    AgentEx ..> WorkflowAgentScope : AsAgentScope()
    WorkflowAgentScope *-- WorkflowAgentToolkit : CreateToolkit()
    WorkflowAgentScope --> ToolCallLedger : owns
    WorkflowAgentScope ..> WorkflowAgentContextProvider : CreateContextProviders()
    WorkflowAgentScope --> AgentPipeline
    WorkflowAgentScope --> SkillScope
    WorkflowAgentScope --> McpScope
    WorkflowAgentScope --> SubAgentScope
    WorkflowAgentToolkit *-- WorkflowStateTracker
    WorkflowAgentToolkit --> WorkflowToolCategory : CreateTools
    WorkflowAgentToolkit ..> TrackedAIFunction : wraps each AIFunction
    WorkflowAgentToolkit ..> CompilerViewModel : RunCompiledWorkflow / GetNodeResult
    CompilerViewModel ..> RuntimeEngine
    RuntimeEngine ..> RuntimeContext
    ToolCallLedger --> ToolCallLedger : Outer chain
    AgentPipeline o-- ToolPipeline
    AgentPipeline o-- TextPipeline
    TextPipeline ..> AgentTranscript
    AgentDashboardViewModel --> AgentMemberViewModel
    AgentDashboardViewModel ..> WorkflowAgentScope : reads / writes switches
```

Key structural facts:

- **One scope owns one toolkit.** `CreateToolkit()` returns a `WorkflowAgentToolkit` bound to the same tree and caches it per scope. The toolkit owns one `WorkflowStateTracker` and one `ToolCallLedger`.
- **The ledger is a chain.** A root scope's ledger has no `Outer`; a spawned child's `ParentLedger` is set before its toolkit exists, so `Spend` walks the chain and the root's total is the whole tree's.
- **Every `AIFunction` is decorated.** `CreateTools` wraps each built-in and developer-registered `AIFunction` in `TrackedAIFunction : DelegatingAIFunction` (namespace `VeloxDev.AI`, `internal sealed`). Non-`AIFunction` tools are added as-is.
- **The provider is the sole tool source.** `CreateContextProviders()` composes compaction → workflow → skill → MCP → sub-agent → todo → modes → host factories, in that fixed order.
- **Run/result reuse the compiler.** `RunCompiledWorkflow` / `GetNodeResult` / the run-handle family funnel through `RunCompiledRoleAsync` and `StartCompiledAsync`, both of which call `new CompilerViewModel().CompileAsync(node, role)` then `new RuntimeEngine().RunAsync(graph, context, ct)`.
- **Subsystems are narrowed views.** A spawn builds a *new* `WorkflowAgentScope` over the same tree and hands it filtered views of the parent's skills (`CreateNarrowed`) and MCP servers (`CreateGrantedView`), never shares of the parent's own objects.

> Source files: `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/{WorkflowAgentScope,WorkflowStateTracker,WorkflowAgentContextProvider}.cs`, `.../Workflow/Functions/{WorkflowAgentToolkit,ToolCallLedger,WorkflowToolCategory}.cs`, `.../TrackedAIFunction.cs`, `.../Pipelines/*`, `.../Skills/*`, `.../MCP/*`, `.../SubAgents/*`, `.../Dashboard/*`; compile types under `VeloxDev.Core.WorkflowSystem.CompilerEx` in `Src/Core/VeloxDev.Core`.
