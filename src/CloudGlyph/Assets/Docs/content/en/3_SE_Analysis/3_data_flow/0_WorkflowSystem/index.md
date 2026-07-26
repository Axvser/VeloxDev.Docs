# Data Flow — WorkflowSystem

## 1. Node Work Execution Flow

When a node's `WorkCommand` is triggered, the following sequence occurs:

```mermaid
sequenceDiagram
	participant T as TreeViewModel
	participant N as NodeViewModel
	participant NH as NodeHelper
	participant Cmd as WorkCommand
	participant S as Slot System
	participant SN as Sibling Nodes

	Note over T,SN: Step 1: Work Execution
	T->>N: WorkCommand.Execute(parameter)
	N->>Cmd: Enqueue (if semaphore limits)
	Cmd-->>T: Enqueued event
	Cmd->>Cmd: Wait for semaphore
	Cmd-->>T: Dequeued event
	Cmd->>NH: WorkAsync(parameter, ct)
	NH->>NH: Business logic
	NH-->>Cmd: Task completed
	Cmd-->>T: Exited event

	Note over T,SN: Step 2: Broadcast (if configured)
	T->>N: BroadcastCommand.Execute(result)
	N->>S: For each output slot with targets...
	S->>SN: Forward data to connected node
	SN->>SN: Execute WorkCommand (recursive)
```

## 2. Connection Establishment Flow

```mermaid
sequenceDiagram
	participant T as TreeViewModel
	participant S1 as Source Slot
	participant S2 as Target Slot
	participant TH as TreeHelper

	Note over T,TH: Phase 1: Virtual connection
	T->>T: SendConnectionCommand.Execute(sourceSlot)
	T->>TH: SendConnection(slot)
	TH->>T: Set VirtualLink with sender
	T->>S1: Mark slot as connecting

	Note over T,TH: Phase 2: Complete connection
	T->>T: ReceiveConnectionCommand.Execute(targetSlot)
	T->>TH: ReceiveConnection(slot)
	TH->>TH: ValidateConnection(sender, receiver)
	alt Valid connection
		TH->>TH: CreateLink(sender, receiver)
		TH->>T: Add link to Links collection
		TH->>S1: Add target to Targets
		TH->>S2: Add source to Sources
		TH->>TH: ResetVirtualLink()
	else Invalid connection
		TH->>TH: ResetVirtualLink()
		Note over T: Connection rejected
	end
```

## 3. Spatial Query Flow (Viewport Culling)

```mermaid
sequenceDiagram
	participant View as UI ScrollViewer
	participant Tree as TreeViewModel
	participant TH as TreeHelper
	participant SM as WorkflowSpatialManager
	participant Grid as SpatialGridHashMap
	participant Items as VisibleItems

	Note over View,Items: On Scroll / Zoom
	View->>TH: Viewport changes
	TH->>SM: Query(viewport)
	SM->>Grid: Query(viewport)
	Grid-->>SM: Intersecting nodes + pairs
	SM-->>TH: Result set
	TH->>Items: Replace VisibleItems
	Items-->>View: UI recycles views
```

## 4. Undo/Redo Flow

```mermaid
sequenceDiagram
	participant User
	participant Tree as TreeViewModel
	participant Stack as Undo Stack
	participant Pair as WorkflowActionPair

	User->>Tree: SubmitCommand.Execute(pair)
	Tree->>Pair: pair.Do()
	Tree->>Stack: Push(pair)

	Note over User,Stack: Later...
	User->>Tree: UndoCommand.Execute(null)
	Tree->>Stack: Pop → pair
	Tree->>Pair: pair.Undo()
	Tree->>RedoStack: Push(pair)

	Note over User,Stack: Or...
	User->>Tree: RedoCommand.Execute(null)
	Tree->>RedoStack: Pop → pair
	Tree->>Pair: pair.Do()
	Tree->>Stack: Push(pair)
```

## 5. Serialization Flow

```mermaid
flowchart LR
	A[TreeViewModel] -->|Serialize| B[JSON]
	B -->|Deserialize| C[TreeViewModel copy]
	C -->|UpdateCommand.Execute| D[Layout restored]
	D -->|WorkflowBehaviors.Refresh| E[UI re-renders]
```

The `VeloxDev.MVVM.Serialization` namespace provides `Serialize()` and `Deserialize<T>()` extension methods. Serialization preserves the full object graph: nodes, slots, links, layout state, and custom data properties.
