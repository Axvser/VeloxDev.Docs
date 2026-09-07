# Workflow System — Design Patterns — Class Diagram

Two Mermaid class diagrams capture the current architecture. Diagram A is the core/execution model — the CompilerEx compile→run machinery and the context hierarchy that flows through every node. Diagram B is the component model — the VM interfaces, their helpers, and the topology they expose. For the adapter/attached-behaviors side (per-platform surfaces that host this VM tree: drag, connect, view-pool virtualization, minimap) see [Platform Adapters — class diagram](../../08_platform-adapters/index.md).

## A. Core / Execution Model (CompilerEx)

Every type below exists in `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/**` (Compile + Runtime folders). The model is two-phase: `CompilerViewModel.CompileAsync` fixes each node's identity (Order) and statically validates edges via `AccessAsync`; `RuntimeEngine.RunAsync` then drives the immutable segments against a runtime session.

```mermaid
classDiagram
    class IContext {
        <<interface>>
        +Data object?
    }
    class IAccessContext {
        <<interface>>
        +IsCompilePhase bool
        +Sender IWorkflowSlotViewModel?
        +Receiver IWorkflowSlotViewModel?
    }
    class ITaskContext {
        <<interface>>
    }
    class ICompileContext {
        <<interface>>
        +Order int
        +ChainIndex int
        +Offset int
        +InputNodes IReadOnlyList~IWorkflowNodeViewModel?~
    }
    class IRuntimeContext {
        <<interface>>
        +Uid Guid
        +Sequence int
        +Logs ObservableCollection~string~
        +CurrentEntry CompileSegment?
        +Attempt int
        +Status string
        +CurrentOrder int
        +Target IWorkflowNodeViewModel?
        +TargetReached bool
        +Data object?
        +RedirectRequested bool
        +EndedWithError bool
        +PendingRedirectTarget int?
        +ActiveRedirectTarget int?
        +Log(string)
        +Error(string)
        +Warn(string)
        +Set(string, object?)
        +TryGet(string, out object?) bool
        +RegisterOutput(node, value)
        +ResetOutputs()
        +CollectGroupedInputs(inputs) IReadOnlyDictionary
    }
    class IGroupData {
        <<interface>>
    }
    class GroupData {
        <<readonly struct>>
        +Count int
        +TryGetValue(node, out value) bool
    }
    class CompileContext {
        +IsCompilePhase bool
        +Data object?
        +Order int
        +ChainIndex int
        +Offset int
        +Sender IWorkflowSlotViewModel?
        +Receiver IWorkflowSlotViewModel?
        +InputNodes IReadOnlyList~IWorkflowNodeViewModel?~
    }
    class RuntimeContext {
        +Target IWorkflowNodeViewModel?
        +TargetReached bool
        +Data object?
        +Attempt int
    }
    class CompilerViewModel {
        +Graphs ObservableCollection~CompiledGraph~
        +CompileAsync(component, CompileRole role, ct) Task~IReadOnlyList~CompiledGraph~~
    }
    class CompileRole {
        <<enum>>
        Root
        Terminal
    }
    class CompiledGraph {
        +Entries ObservableCollection~CompileSegment~
    }
    class CompileSegment {
        <<abstract>>
        +Id Guid
        +Depth int
    }
    class ChainSegment {
        +Nodes ObservableCollection~IWorkflowNodeViewModel~
    }
    class BranchSegment {
        +Router IWorkflowNodeViewModel?
        +Options ObservableCollection~BranchOption~
        +IsDynamic bool
        +CompileKey object?
    }
    class BranchOption {
        +Key object?
        +Label string?
        +Graph CompiledGraph?
        +IsTerminal bool
    }
    class ParallelSegment {
        +Branches ObservableCollection~CompiledGraph~
    }
    class RuntimeEngine {
        +RunAsync(graph, context, ct) Task
    }
    class ICompileTimeAware {
        <<interface>>
        +CompileContext ICompileContext?
        +AttachCompileTimeContext(context)
    }
    class IRuntimeAware {
        <<interface>>
        +AttachRuntimeContext(context)
    }
    class IRedirectable {
        <<interface>>
        +ResolveRedirectAsync(context, ct) Task~int?~
    }
    class ICompileTimeRouter {
        <<interface>>
        +GetRouteTable() Task~IReadOnlyDictionary~
        +ResolveRouteKey(payload) Task~object?~
    }
    class RouterCompileMode {
        <<enum>>
        Static
        Dynamic
    }
    class EnumSelectorNodeViewModel {
        +SelectedValue object?
    }
    class ControllerViewModel {
        +Compiler CompilerViewModel
        +RuntimeContext IRuntimeContext?
    }

    IContext <|-- IAccessContext
    IAccessContext <|-- ITaskContext
    IAccessContext <|-- ICompileContext
    ITaskContext <|-- IRuntimeContext
    ICompileContext <|.. CompileContext
    IRuntimeContext <|.. RuntimeContext
    IGroupData <|.. GroupData
    CompilerViewModel ..> CompiledGraph : produces
    CompileRole <.. CompilerViewModel : role switch
    CompiledGraph "1" *-- "many" CompileSegment : Entries
    CompileSegment <|-- ChainSegment
    CompileSegment <|-- BranchSegment
    CompileSegment <|-- ParallelSegment
    BranchSegment "1" *-- "many" BranchOption : Options
    BranchOption --> "0..1" CompiledGraph : Graph
    ParallelSegment "1" *-- "many" CompiledGraph : Branches
    RuntimeEngine ..> CompiledGraph : drives
    RuntimeEngine ..> IRuntimeContext : session
    RuntimeEngine ..> GroupData : boxes grouped inputs into Data
    RuntimeEngine ..> IRedirectable : in-chain redirect
    ICompileTimeRouter ..> RouterCompileMode
    EnumSelectorNodeViewModel ..|> ICompileTimeRouter : demo router
    EnumSelectorNodeViewModel ..|> ICompileTimeAware
    ControllerViewModel ..|> ICompileTimeAware : demo root
    ControllerViewModel ..|> IRuntimeAware
    CompilerViewModel ..> ICompileTimeRouter : GetRouteTable
```

Sources: `CompilerEx/Compile/CompilerViewModel.cs` (lines 26-57 entry, 59-232 forward decomposition), `CompilerEx/Compile/CompilerViewModel.Reverse.cs` (ancestor-cone compilation), `CompilerEx/Runtime/RuntimeEngine.cs` (lines 19-68 `RunAsync`, 205-214 fan-out restore), `CompilerEx/Compile/Model/*.cs` + `Runtime/Model/*.cs`, `Interfaces/WorkflowSystem/IContext.cs`, `IAccessContext.cs`, `ITaskContext.cs`.

## B. Component Model (VM interfaces + helpers)

The editor tree is built from four VM interfaces; each is paired with a *Helper* that owns behavior (Template Method / Command patterns). Nodes expose the topology the compiler consumes: `Slots` → `Targets`/`Sources` edges.

```mermaid
classDiagram
    class IWorkflowViewModel {
        <<interface>>
        +InitializeWorkflow()
        +CloseCommand
    }
    class IWorkflowTreeViewModel {
        <<interface>>
        +Nodes ObservableCollection~IWorkflowNodeViewModel~
        +Links ObservableCollection~IWorkflowLinkViewModel~
        +LinksMap Dictionary
        +VirtualLink IWorkflowLinkViewModel
        +CreateNodeCommand
        +UndoCommand
        +RedoCommand
    }
    class IWorkflowNodeViewModel {
        <<interface>>
        +Parent IWorkflowTreeViewModel?
        +Anchor Anchor
        +Size Size
        +Slots ObservableCollection~IWorkflowSlotViewModel~
        +ReceiveCommand IVeloxCommand
        +GetHelper() IWorkflowNodeViewModelHelper
    }
    class IWorkflowSlotViewModel {
        <<interface>>
        +Targets ObservableCollection~IWorkflowSlotViewModel~
        +Sources ObservableCollection~IWorkflowSlotViewModel~
        +Parent IWorkflowNodeViewModel?
        +Channel SlotChannel
    }
    class IWorkflowLinkViewModel {
        <<interface>>
        +Sender IWorkflowSlotViewModel?
        +Receiver IWorkflowSlotViewModel?
        +IsVisible bool
    }
    class IWorkflowNodeViewModelHelper {
        <<interface>>
        +ReceiveAsync(ITaskContext, ct) Task~object?~
        +BroadcastAsync(object?, ct) Task
        +AccessAsync(IAccessContext, ct) Task~bool~
        +Delete()
        +Install(node)
        +Uninstall(node)
    }
    class IWorkflowTreeViewModelHelper {
        <<interface>>
        +Install(tree)
        +Uninstall(tree)
        +CreateLink(sender, receiver) IWorkflowLinkViewModel
        +ValidateConnection(sender, receiver) bool
        +Submit(IWorkflowActionPair)
        +Undo()
        +Redo()
    }
    class TreeHelper~T~ {
        +Install(IWorkflowTreeViewModel)
        +Uninstall(IWorkflowTreeViewModel)
        +CloseAsync() Task
        +CreateLink(sender, receiver) IWorkflowLinkViewModel
        +NodeAdded event
    }
    class NodeHelper~T~ {
        +Install(node)
        +ReceiveAsync(ITaskContext, ct) Task~object?~
        +AccessAsync(IAccessContext, ct) Task~bool~
        +BroadcastAsync(object?, ct) Task
    }
    class WorkflowActionPair {
        +Redo Action
        +Undo Action
    }

    IWorkflowViewModel <|-- IWorkflowTreeViewModel
    IWorkflowViewModel <|-- IWorkflowNodeViewModel
    IWorkflowViewModel <|-- IWorkflowSlotViewModel
    IWorkflowViewModel <|-- IWorkflowLinkViewModel
    IWorkflowTreeViewModel "1" *-- "many" IWorkflowNodeViewModel : Nodes
    IWorkflowNodeViewModel "1" *-- "many" IWorkflowSlotViewModel : Slots
    IWorkflowSlotViewModel --> "many" IWorkflowSlotViewModel : Targets / Sources
    IWorkflowNodeViewModelHelper <.. IWorkflowNodeViewModel : GetHelper()
    IWorkflowNodeViewModelHelper <|.. NodeHelper~T~
    IWorkflowTreeViewModelHelper <|.. TreeHelper~T~
    IWorkflowNodeViewModel --> IWorkflowNodeViewModelHelper : delegates ReceiveAsync
    TreeHelper~T~ ..> WorkflowActionPair : Submit/Undo/Redo
```

Sources: `Interfaces/WorkflowSystem/IWorkflow*.cs`, `Templates/Helpers/TreeHelper.cs` (lines 109-265), `Templates/Helpers/NodeHelper.cs` (lines 28-112), `Templates/WorkflowBuilder.cs`.
