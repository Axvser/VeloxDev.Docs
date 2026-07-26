# Feature Map — WorkflowSystem

## Responsibility

The WorkflowSystem provides the foundational building blocks for visual workflow editing on any .NET UI platform. It owns the canvas abstraction, spatial indexing, node/slot/link lifecycle, undo/redo, and the compilation pipeline.

## Feature Breakdown

### 1. Tree Management (`IWorkflowTreeViewModel`)
- **Owner**: `VeloxDev.WorkflowSystem` namespace
- **Key file**: `Interfaces/WorkflowSystem/IWorkflowTreeViewModel.cs`
- **Purpose**: Root container holding all nodes, links, and layout state. Provides commands for node creation, connection building, undo/redo, and serialization.
- **Commands**: `CreateNode`, `SetPointer`, `SendConnection`, `ReceiveConnection`, `Submit`, `Undo`, `Redo`

### 2. Node Management (`IWorkflowNodeViewModel`)
- **Key file**: `Interfaces/WorkflowSystem/IWorkflowNodeViewModel.cs`
- **Purpose**: Represents a visual node with position (`Anchor`), size (`Size`), and a collection of slots. Each node has a `WorkCommand` for executing business logic.
- **Commands**: `Move`, `SetAnchor`, `SetSize`, `CreateSlot`, `Delete`, `Work`, `Broadcast`, `ReverseBroadcast`

### 3. Slot Management (`IWorkflowSlotViewModel`)
- **Key file**: `Interfaces/WorkflowSystem/IWorkflowSlotViewModel.cs`
- **Purpose**: Connection points on nodes. Each slot has a channel direction (`Input`/`Output`) and maintains lists of connected source/target slots.
- **Commands**: `SetChannel`, `SendConnection`, `ReceiveConnection`, `Delete`, `Close`

### 4. Link Management (`IWorkflowLinkViewModel`)
- **Key file**: `Interfaces/WorkflowSystem/IWorkflowLinkViewModel.cs`
- **Purpose**: Visual connections between slots. Supports Bezier and polyline rendering modes.

### 5. Canvas Layout (`CanvasLayout`)
- **Key file**: `WorkflowSystem/CanvasLayout.cs`
- **Purpose**: Manages canvas dimensions (`ActualSize`, `OriginSize`) and scroll/viewport offsets (`ViewportOffset`, `ActualOffset`). Provides `UpdateCommand` to recalculate after changes.

### 6. Spatial Indexing (`SpatialGridHashMap<T>` / `WorkflowSpatialManager`)
- **Key files**: `WorkflowSystem/SpatialGridHashMap.cs`, `WorkflowSystem/WorkflowSpatialManager.cs`
- **Purpose**: Grid-based spatial hash for efficient viewport queries. `WorkflowSpatialManager` wraps this at the tree level, indexing both nodes and node pairs (links).

### 7. Helper System
- **Key files**: `Templates/Helpers/TreeHelper.cs`, `NodeHelper.cs`, `SlotHelper.cs`, `LinkHelper.cs`
- **Purpose**: Lifecycle hooks (`Install`/`Uninstall`) and behavior overrides. Each component type has a corresponding Helper base class.

### 8. Compilation Pipeline
- **Key files**: `WorkflowSystem/Compilation/`
- **Purpose**: Compiles the workflow graph into an executable form. Supports different `CompileMode`, `CompileDirection`, `CompileScope`, and `CycleHandling` strategies.

### 9. Undo/Redo (`WorkflowActionPair`)
- **Key file**: `WorkflowSystem/WorkflowActionPair.cs`
- **Purpose**: Encapsulates a single reversible action. The Tree's `SubmitCommand` / `UndoCommand` / `RedoCommand` form the undo stack.

### 10. Conditional/Selector Slots (`SelectorEx`)
- **Key files**: `WorkflowSystem/SelectorEx/`
- **Purpose**: Advanced slot types that route execution based on conditions (e.g., `BoolSelectorNode`, `EnumSelectorNode`). Uses `SlotEnumerator` and `ConditionalSlot` to dynamically select output paths.

## Dependency Relationships

```
IWorkflowTreeViewModel  ──contains──▶ IWorkflowNodeViewModel[]
								  ──contains──▶ IWorkflowLinkViewModel[]
								  ──uses──▶ CanvasLayout
								  ──uses──▶ WorkflowSpatialManager
								  ──uses──▶ IWorkflowTreeViewModelHelper

IWorkflowNodeViewModel  ──contains──▶ IWorkflowSlotViewModel[]
						──uses──▶ Anchor, Size
						──uses──▶ IVeloxCommand (Work, Broadcast, etc.)
						──uses──▶ IWorkflowNodeViewModelHelper

IWorkflowSlotViewModel  ──references──▶ IWorkflowSlotViewModel[] (Targets/Sources)
						──uses──▶ SlotChannel, SlotState
						──uses──▶ IWorkflowSlotViewModelHelper
```
