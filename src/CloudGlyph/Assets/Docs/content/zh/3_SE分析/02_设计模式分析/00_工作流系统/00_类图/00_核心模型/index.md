# Workflow System — 类图：核心 / 执行模型

## A. 核心 / 执行模型（CompilerEx）

`CompilerViewModel.CompileAsync(node, CompileRole)` 是统一编译入口：固定每个节点的身份（Order）并经 `AccessAsync` 做静态边校验；`RuntimeEngine.RunAsync` 随后以运行时会话驱动不可变段。

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
        +Logs ObservableCollection~string~
        +CurrentEntry CompileSegment?
        +BranchKey object?
        +Attempt int
        +Status string
        +CurrentOrder int
        +Target IWorkflowNodeViewModel?
        +TargetReached bool
        +Data object?
        +RedirectRequested bool
        +ActiveRedirectTarget int?
        +RegisterOutput(node, value)
        +ResetOutputs()
        +CollectGroupedInputs(inputs)
    }
    class TaskContext {
        <<struct>>
        +Data object?
        +Sender IWorkflowSlotViewModel?
        +Receiver IWorkflowSlotViewModel?
    }
    class CompileContext {
        +Order int
        +ChainIndex int
        +Offset int
        +InputNodes IReadOnlyList~IWorkflowNodeViewModel?~
    }
    class RuntimeContext {
        +Target IWorkflowNodeViewModel?
        +TargetReached bool
        +Attempt int
    }
    class IGroupData {
        <<interface>>
    }
    class GroupData {
        <<struct>>
        +TryGetValue(node, out object?) bool
    }
    class CompilerViewModel {
        +Graphs ObservableCollection~CompiledGraph~
        +CompileAsync(component, CompileRole role, ct)
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
        +Graph CompiledGraph?
        +IsTerminal bool
    }
    class ParallelSegment {
        +Branches ObservableCollection~CompiledGraph~
    }
    class RuntimeEngine {
        +RunAsync(graph, context, ct)
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
        +ResolveRedirectAsync(context, ct)
    }
    class ICompileTimeRouter {
        <<interface>>
        +GetRouteTable()
        +ResolveRouteKey(payload)
    }
    class RouterCompileMode {
        <<enum>>
        Static
        Dynamic
    }

    IContext <|-- IAccessContext
    IAccessContext <|-- ITaskContext
    IAccessContext <|-- ICompileContext
    ITaskContext <|-- IRuntimeContext
    ITaskContext <|.. TaskContext
    ICompileContext <|.. CompileContext
    IRuntimeContext <|.. RuntimeContext
    IGroupData <|.. GroupData
    RuntimeContext ..> IGroupData : 汇合时作为 Data 注入
    CompilerViewModel ..> CompiledGraph : 产生
    CompileRole <.. CompilerViewModel : 角色分派
    CompiledGraph "1" *-- "many" CompileSegment : Entries
    CompileSegment <|-- ChainSegment
    CompileSegment <|-- BranchSegment
    CompileSegment <|-- ParallelSegment
    BranchSegment "1" *-- "many" BranchOption : Options
    BranchOption --> "0..1" CompiledGraph : Graph
    ParallelSegment "1" *-- "many" CompiledGraph : Branches
    RuntimeEngine ..> CompiledGraph : 驱动
    RuntimeEngine ..> IRedirectable : 链内重定向
    ICompileTimeRouter ..> RouterCompileMode
    CompilerViewModel ..> ICompileTimeRouter : GetRouteTable
```

来源：`CompilerEx/Compile/CompilerViewModel.cs`（第 24-57 行入口、第 59-249 行正向分解）、`CompilerEx/Compile/CompilerViewModel.Reverse.cs`（祖先锥编译）、`CompilerEx/Runtime/RuntimeEngine.cs`、`CompilerEx/Compile/Model/*.cs`、`CompilerEx/Runtime/Model/*.cs`、`Interfaces/WorkflowSystem/IContext.cs`、`IAccessContext.cs`、`ITaskContext.cs`、`WorkflowSystem/TaskContext.cs`。演示实现 `ControllerViewModel`/`EnumSelectorNodeViewModel` 在 `Examples/Workflow/Common/Lib/ViewModels/Workflow/`。
