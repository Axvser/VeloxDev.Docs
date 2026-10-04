# Workflow System — Design Patterns — Component Model

The component model: the four VM interfaces, their helpers, and the topology the compiler consumes (`Slots` → `Targets`/`Sources` edges).

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
