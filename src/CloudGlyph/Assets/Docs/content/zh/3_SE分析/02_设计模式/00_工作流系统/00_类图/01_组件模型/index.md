# 工作流系统 — 设计模式 — 组件模型

组件模型：四个 VM 接口、它们的 Helper，以及编译器消费的拓扑（`Slots` → `Targets`/`Sources` 边）。

## B. 组件模型（VM 接口 + Helper）

编辑器树由四个 VM 接口构成；每个都配一个拥有行为的 *Helper*（模板方法 / 命令模式）。节点暴露编译器消费的拓扑：`Slots` → `Targets`/`Sources` 边。

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

源码：`Interfaces/WorkflowSystem/IWorkflow*.cs`、`Templates/Helpers/TreeHelper.cs`、`Templates/Helpers/NodeHelper.cs`、`Templates/WorkflowBuilder.cs`。
