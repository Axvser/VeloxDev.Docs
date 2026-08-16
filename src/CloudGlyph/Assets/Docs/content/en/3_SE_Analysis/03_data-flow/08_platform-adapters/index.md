# 08 · Platform Adapters — Data Flow

The sequence diagrams below trace the five core flows of the platform-adapter layer. They are derived from the WPF adapter source and the WPF/Avalonia/Blazor demos; per-platform details not exercised by a demo are `*inferred*` from source.

## (a) Attached-behavior wiring: XAML loads → behavior attaches → viewport → `ViewPool` virtualizes

```plantuml
@startuml
skinparam maxMessageSize 200
participant "XAML Loader" as X
participant "WorkflowView (host)" as W
participant "WorkflowSurfaceBehavior" as B
participant "ScrollViewer / Canvas" as SV
participant "Helper (tree VM)" as H
participant "ViewPool / ViewManager" as VP

X -> W : load XAML; set DataContext = IWorkflowTreeViewModel
X -> W : WorkflowSurfaceBehavior.IsEnabled = True
activate B
B -> B : Attach(control)
B -> B : subscribe Loaded / DataContextChanged / ScrollChanged / mouse events
B -> W : Refresh(host)
B -> SV : resolve PART_ScrollViewer / PART_Canvas / decorator / minimap
B -> B : ApplyLayout -> WorkflowCanvasTransformBehavior.Apply(host, translate)
B -> H : GetHelper().Viewport = Viewport(x, y, viewportW, viewportH)
B -> H : Layout.ViewportOffset = Offset(x, y)
X -> VP : ViewPool.ItemsSource = Helper.VisibleItems
activate VP
VP -> VP : ViewManager.Attach(collection)
VP -> VP : schedule batched render (3 views per dispatcher tick)
VP -> VP : AddOrReuseView per visible item (pool hit or template.LoadContent)
VP --> X : only visible node/link views materialized on the Canvas
deactivate VP
deactivate B
@enduml
```

## (b) Drag-to-move: `WorkflowNodeDragBehavior` → `MoveCommand`

```plantuml
@startuml
actor User
participant "NodeView header" as N
participant "WorkflowNodeDragBehavior" as D
participant "IWorkflowNodeViewModel" as VM
participant "Layout" as L

User -> N : press left button
N -> D : PreviewMouseLeftButtonDown
D -> D : resolve CoordinateHost (PART_Canvas or type fallback)
D -> D : state.IsDragging = true; Mouse.Capture(header)
User -> N : move
N -> D : PreviewMouseMove
D -> VM : MoveCommand.Execute(new Offset(dx, dy))
VM -> L : Anchor += delta; grow NegativeOffset/PositiveOffset if needed
N -> D : release left button / LostMouseCapture
D -> D : state.IsDragging = false; release capture
@enduml
```

## (c) Slot connect: `WorkflowSlotConnectionBehavior` → `SendConnectionCommand` / `ReceiveConnectionCommand`

```plantuml
@startuml
actor User
participant "SlotView" as S
participant "WorkflowSlotConnectionBehavior" as C
participant "IWorkflowSlotViewModel" as Slot
participant "Tree (IWorkflowTreeViewModel)" as Tree

User -> S : press left button
S -> C : PreviewMouseLeftButtonDown
C -> Slot : SendConnectionCommand.Execute(null)
Slot -> Tree : begin virtual link from this slot
User -> S : release left button
S -> C : PreviewMouseLeftButtonUp
C -> Slot : ReceiveConnectionCommand.Execute(null)
Slot -> Tree : resolve receiver; create Link (undoable, spatial index)
User -> S : release on blank surface
S -> Tree : ResetVirtualLinkCommand.Execute(null) (via surface behavior)
@enduml
```

## (d) Minimap projection flow

```plantuml
@startuml
participant "ScrollViewer" as SV
participant "WorkflowSurfaceBehavior" as B
participant "WorkflowMinimapOverlay" as M
participant "Tree (IWorkflowTreeViewModel)" as VM
actor User

SV -> B : ScrollChanged
B -> M : set ScrollOffsetX/Y, ContentOffsetX/Y, ViewportWidth/Height, WorkflowTree
B -> VM : GetHelper().Viewport = current viewport
M -> M : RefreshMinimapData: union node bounds -> globalBounds
M -> M : ComputeTransform: scale = min(drawW/gb.W, drawH/gb.H)
M -> M : OnRender: draw node rects + viewport indicator rect
User -> M : press / drag viewport indicator
M -> M : NavigateToWorld(adjX, adjY) back to world coords
M -> SV : ScrollToHorizontalOffset / ScrollToVerticalOffset
M -> VM : grow Layout.NegativeOffset/PositiveOffset at edges
SV -> B : ScrollChanged (feedback loop closes)
@enduml
```

## (e) Template-scaffold flow: `dotnet new` → generated files

```plantuml
@startuml
actor User
participant "dotnet CLI" as CLI
participant "Template Engine" as T
participant "File System" as FS

User -> CLI : dotnet new install VeloxDev.WPF.Templates
CLI -> T : register wpf-v-* short names
User -> CLI : dotnet new wpf-v-tree -n TreeView -ns MyApp.Views -o Views
CLI -> T : instantiate workflow-tree-view template
T -> T : substitute TemplateNamespace -> MyApp.Views; TemplateClass -> TreeView
T -> FS : write TreeView.xaml + TreeView.xaml.cs (WorkflowSurfaceBehavior wired)
User -> CLI : dotnet new wpf-v-node / -slot / -link / -selector / -decorator / -minimap
CLI -> T : instantiate each item template
T -> FS : write NodeView / SlotView / LinkView / TemplateSelector / GridDecorator / MinimapOverlay
User -> CLI : dotnet build
CLI -> FS : compile Views against VeloxDev.WPF package
@enduml
```
