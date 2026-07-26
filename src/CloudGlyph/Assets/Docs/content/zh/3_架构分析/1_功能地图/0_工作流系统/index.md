# 功能地图 — 工作流系统

## 职责

工作流系统提供了在任何 .NET UI 平台上构建可视化工作流编辑器的基本构建块。它拥有画布抽象、空间索引、节点/槽位/连接线生命周期、撤销/重做以及编译管道。

## 功能分解

### 1. Tree 管理（`IWorkflowTreeViewModel`）
- **所属**: `VeloxDev.WorkflowSystem` 命名空间
- **关键文件**: `Interfaces/WorkflowSystem/IWorkflowTreeViewModel.cs`
- **用途**: 根容器，持有所有节点、连接线和布局状态。提供节点创建、连接构建、撤销/重做和序列化命令。
- **命令**: `CreateNode`, `SetPointer`, `SendConnection`, `ReceiveConnection`, `Submit`, `Undo`, `Redo`

### 2. Node 管理（`IWorkflowNodeViewModel`）
- **关键文件**: `Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`
- **用途**: 表示具有位置（`Anchor`）、尺寸（`Size`）和槽位集合的可视节点。每个节点有 `WorkCommand` 用于执行业务逻辑。
- **命令**: `Move`, `SetAnchor`, `SetSize`, `CreateSlot`, `Delete`, `Work`, `Broadcast`, `ReverseBroadcast`

### 3. Slot 管理（`IWorkflowSlotViewModel`）
- **关键文件**: `Interfaces/WorkflowSystem/IWorkflowSlotViewModel.cs`
- **用途**: 节点上的连接点。每个槽位有通道方向（`Input`/`Output`）并维护连接的源/目标槽位列表。
- **命令**: `SetChannel`, `SendConnection`, `ReceiveConnection`, `Delete`, `Close`

### 4. Link 管理（`IWorkflowLinkViewModel`）
- **关键文件**: `Interfaces/WorkflowSystem/IWorkflowLinkViewModel.cs`
- **用途**: 槽位之间的可视化连接。支持贝塞尔曲线和折线渲染模式。

### 5. 画布布局（`CanvasLayout`）
- **关键文件**: `WorkflowSystem/CanvasLayout.cs`
- **用途**: 管理画布尺寸（`ActualSize`, `OriginSize`）和滚动/视口偏移（`ViewportOffset`, `ActualOffset`）。提供 `UpdateCommand` 在变更后重新计算。

### 6. 空间索引（`SpatialGridHashMap<T>` / `WorkflowSpatialManager`）
- **关键文件**: `WorkflowSystem/SpatialGridHashMap.cs`, `WorkflowSystem/WorkflowSpatialManager.cs`
- **用途**: 基于网格的空间哈希，用于高效视口查询。`WorkflowSpatialManager` 在 Tree 级别封装此功能，索引节点和节点对（连接线）。

### 7. Helper 系统
- **关键文件**: `Templates/Helpers/TreeHelper.cs`, `NodeHelper.cs`, `SlotHelper.cs`, `LinkHelper.cs`
- **用途**: 生命周期钩子（`Install`/`Uninstall`）和行为覆写。每个组件类型都有对应的 Helper 基类。

### 8. 编译管道
- **关键文件**: `WorkflowSystem/Compilation/`
- **用途**: 将工作流程图编译为可执行形式。支持不同的 `CompileMode`、`CompileDirection`、`CompileScope` 和 `CycleHandling` 策略。

### 9. 撤销/重做（`WorkflowActionPair`）
- **关键文件**: `WorkflowSystem/WorkflowActionPair.cs`
- **用途**: 封装单一可逆操作。Tree 的 `SubmitCommand` / `UndoCommand` / `RedoCommand` 构成撤销栈。

### 10. 条件/选择器槽位（`SelectorEx`）
- **关键文件**: `WorkflowSystem/SelectorEx/`
- **用途**: 基于条件路由执行路径的高级槽位类型（例如 `BoolSelectorNode`、`EnumSelectorNode`）。使用 `SlotEnumerator` 和 `ConditionalSlot` 动态选择输出路径。

## 依赖关系

```
IWorkflowTreeViewModel  ──包含──▶ IWorkflowNodeViewModel[]
								  ──包含──▶ IWorkflowLinkViewModel[]
								  ──使用──▶ CanvasLayout
								  ──使用──▶ WorkflowSpatialManager
								  ──使用──▶ IWorkflowTreeViewModelHelper

IWorkflowNodeViewModel  ──包含──▶ IWorkflowSlotViewModel[]
						──使用──▶ Anchor, Size
						──使用──▶ IVeloxCommand (Work, Broadcast 等)
						──使用──▶ IWorkflowNodeViewModelHelper

IWorkflowSlotViewModel  ──引用──▶ IWorkflowSlotViewModel[] (Targets/Sources)
						──使用──▶ SlotChannel, SlotState
						──使用──▶ IWorkflowSlotViewModelHelper
```
