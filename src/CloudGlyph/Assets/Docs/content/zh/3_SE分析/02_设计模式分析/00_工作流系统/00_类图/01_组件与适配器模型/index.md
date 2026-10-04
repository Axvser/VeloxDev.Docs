# Workflow System — 设计模式 — 组件与适配器模型

图 B 是**组件模型**（VM 接口 + Helper + 对外拓扑）；图 C 是**适配器 / 附加行为侧**（各框架画布如何承载该 VM 树）。每个类型均存在于真实源码，来源见各图后的路径。

## B. 组件模型（VM 接口 + Helper）

编辑器树由四个 VM 接口组成；每个接口配对一个*Helper*（模板方法 / 命令模式）。节点暴露编译器消费的拓扑：`Slots` → `Targets`/`Sources` 边。

```mermaid
classDiagram
    class IWorkflowViewModel {
        <<interface>>
        +InitializeWorkflow()
        +CloseCommand IVeloxCommand
    }
    class IWorkflowTreeViewModel {
        <<interface>>
        +Nodes ObservableCollection~IWorkflowNodeViewModel~
        +Links ObservableCollection~IWorkflowLinkViewModel~
        +LinksMap Dictionary
        +VirtualLink IWorkflowLinkViewModel
        +CreateNodeCommand
        +SendConnectionCommand
        +ReceiveConnectionCommand
        +SubmitCommand
        +UndoCommand
        +RedoCommand
        +GetHelper() IWorkflowTreeViewModelHelper
    }
    class IWorkflowNodeViewModel {
        <<interface>>
        +Parent IWorkflowTreeViewModel?
        +Anchor Anchor
        +Size Size
        +Slots ObservableCollection~IWorkflowSlotViewModel~
        +ReceiveCommand IVeloxCommand
        +BroadcastCommand IVeloxCommand
        +GetHelper() IWorkflowNodeViewModelHelper
    }
    class IWorkflowSlotViewModel {
        <<interface>>
        +Targets ObservableCollection~IWorkflowSlotViewModel~
        +Sources ObservableCollection~IWorkflowSlotViewModel~
        +Parent IWorkflowNodeViewModel?
        +Channel SlotChannel
        +State SlotState
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
        +Install(node)
        +Delete()
    }
    class TreeHelper~T~ {
        +Install(IWorkflowTreeViewModel) virtual
        +Uninstall(IWorkflowTreeViewModel) virtual
        +CreateLink(sender, receiver) IWorkflowLinkViewModel
        +ValidateConnection() bool virtual
    }
    class NodeHelper~T~ {
        +ReceiveAsync(ITaskContext, ct) Task~object?~ virtual
        +AccessAsync(IAccessContext, ct) Task~bool~ virtual
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
    IWorkflowNodeViewModelHelper <|.. NodeHelper~T~
    IWorkflowNodeViewModel --> IWorkflowNodeViewModelHelper : 委托 ReceiveAsync/AccessAsync
    TreeHelper~T~ ..> WorkflowActionPair : Submit/Undo/Redo
```

来源：`Interfaces/WorkflowSystem/IWorkflow*.cs`、`Templates/Helpers/TreeHelper.cs`、`Templates/Helpers/NodeHelper.cs`、`Templates/WorkflowBuilder.cs`。

## C. 适配器 / 附加行为侧（attached behaviors）

每套 GUI 适配器（WPF / WinUI / MAUI / WinForms / Avalonia / Jalium / Razor）都以**并行实现**的附加行为把上述 VM 树接到各自画布，共享命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors`。附加行为是“适配器”：消费 Core VM 的命令，并把界面位移回写为 Core 几何。

```mermaid
classDiagram
    class IWorkflowGridDecorator {
        <<interface>>
        +ScrollOffsetX double
        +ContentOffsetX double
        +RulerBand double
    }
    class IWorkflowMinimapOverlay {
        <<interface>>
        +ViewportWidth double
        +WorkflowTree IWorkflowTreeViewModel?
        +IsMinimapVisible bool
    }
    class IWorkflowNodeViewModel {
        <<interface>>
        +MoveCommand
    }
    class IWorkflowSlotViewModel {
        <<interface>>
        +SendConnectionCommand
        +ReceiveConnectionCommand
    }
    class WorkflowSurfaceMath {
        <<static>>
        +ToWorld(...)
        +ToScreen(...)
        +SlotAnchorFromVisualCenter(...)
    }
    class WorkflowSurfaceBehavior {
        <<attached>>
        +IsEnabledProperty
        +Refresh(host)
    }
    class WorkflowNodeDragBehavior {
        <<attached>>
    }
    class WorkflowSlotConnectionBehavior {
        <<attached>>
    }
    class WorkflowSlotLayoutBehavior {
        <<attached>>
    }
    class ViewPool {
        <<attached>>
        +ItemsSourceProperty
    }
    class ViewManager {
        +Attach(collection)
    }
    class WorkflowMinimapOverlay {
        <<overlay element>>
    }
    class WorkflowGridDecorator {
        <<decorator element>>
    }

    IWorkflowGridDecorator <|-- IWorkflowMinimapOverlay
    IWorkflowMinimapOverlay --> IWorkflowTreeViewModel : WorkflowTree
    WorkflowSurfaceBehavior ..> IWorkflowTreeViewModel : 观测 DataContext
    WorkflowSurfaceBehavior ..> IWorkflowGridDecorator : 每 pass 写偏移
    WorkflowSurfaceBehavior ..> IWorkflowMinimapOverlay : 写入 + WorkflowTree
    WorkflowSurfaceBehavior ..> WorkflowSurfaceMath
    WorkflowNodeDragBehavior ..> IWorkflowNodeViewModel : MoveCommand
    WorkflowSlotConnectionBehavior ..> IWorkflowSlotViewModel : Send/ReceiveConnectionCommand
    WorkflowSlotLayoutBehavior ..> IWorkflowSlotViewModel : 回写 slot.Anchor
    WorkflowSlotLayoutBehavior ..> WorkflowSurfaceMath : SlotAnchorFrom*
    ViewPool --> ViewManager : 构造并附着
    ViewManager ..> IWorkflowTreeViewModel : 绑定 Helper.VisibleItems
    WorkflowMinimapOverlay ..|> IWorkflowMinimapOverlay : 实现
    WorkflowGridDecorator ..|> IWorkflowGridDecorator : 实现
```

`WorkflowSurfaceBehavior`（六家；Jalium 无，由复合控件 `WorkflowTreeView` 承担）是画布协调器：从宿主 `DataContext as IWorkflowTreeViewModel` 读取 VM，每 pass 推送 `tree.GetHelper().Viewport` + `Layout.ViewportOffset`、调 `tree.SetVirtualizeInset(left: ruler, top: ruler)`，并把位移写入实现 `IWorkflowGridDecorator`/`IWorkflowMinimapOverlay` 的命名部件。手势行为消费 Core 命令：拖拽 → `MoveCommand`，连线 → `Send/ReceiveConnectionCommand`（配合 `SetPointerCommand`/`ResetVirtualLinkCommand`），槽布局 → 用 `WorkflowSurfaceMath.SlotAnchorFrom*` 回写 `slot.Anchor`。`ViewPool` → `ViewManager` 是对象池/视图物化器：`ItemsSource` 绑定 `Helper.VisibleItems`，按运行时类型复用视图并以其 `Anchor`/`Size` 定位。标尺装饰元素由 Jalium、WinForms 与 Razor 适配器自带（`WorkflowGridDecorator`），其余由宿主提供 `PART_GridDecorator` 命名部件；小地图元素在六个适配器实现 Core `IWorkflowMinimapOverlay`。

*代表源码：`Src/Adapters/VeloxDev.WPF/Attached/Workflow/*.cs`（`WorkflowSurfaceBehavior.cs` 第 12 行起、`ViewPool.cs` 第 12 行起、`ViewManager.cs` 第 13 行起、`WorkflowNodeDragBehavior.cs` 第 11 行起、`WorkflowSlotConnectionBehavior.cs` 第 8 行起、`WorkflowSlotLayoutBehavior.cs` 第 13 行起、`WorkflowMinimapOverlay.cs` 第 19 行起）；Core 契约 `Interfaces/WorkflowSystem/IWorkflowGridDecorator.cs`、`IWorkflowMinimapOverlay.cs`；坐标 `WorkflowSystem/GUI/Math/WorkflowSurfaceMath.cs`。*
