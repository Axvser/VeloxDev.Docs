# 工作流系统 — 类图：核心 / 执行模型

## A. 核心 / 执行模型（CompilerEx）

下列类型都存在于 `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/**`（Compile + Runtime 目录）。模型分两阶段：`CompilerViewModel.CompileAsync` 固定每个节点的身份（Order），并通过 `AccessAsync` 静态校验边；随后 `RuntimeEngine.RunAsync` 用运行时会话驱动这些不可变分段。

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

源码：`CompilerEx/Compile/CompilerViewModel.cs`、`CompilerEx/Compile/CompilerViewModel.Reverse.cs`、`CompilerEx/Runtime/RuntimeEngine.cs`、`CompilerEx/Compile/Model/*.cs` + `Runtime/Model/*.cs`、`Interfaces/WorkflowSystem/Execution/IContext.cs`、`IAccessContext.cs`、`ITaskContext.cs`。
