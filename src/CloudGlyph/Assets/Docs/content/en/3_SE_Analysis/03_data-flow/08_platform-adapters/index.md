# 08 · Platform Adapters — Data Flow

The sequence diagrams below trace the core data flows of the platform-adapter layer. They are derived from the WPF adapter source, the Core model (`VeloxDev.WorkflowSystem`), and the WPF/Avalonia/WinUI/MAUI demos; per-platform detail not exercised by a demo is `*inferred*` from source. A recurring step is the visible-region feed: the surface writes `Helper.Viewport`, the spatial index re-computes `Helper.VisibleItems`, and `ViewPool` materializes only those views. The WPF/Avalonia/WinUI demos bind `ViewPool` to `Helper.VisibleItems` and the MAUI demo binds a node-only wrapper of it; the WinForms and Blazor demos instead bind the full node collection and rely on the surface for visible-region bookkeeping.

## (a) Attach & layout wiring → virtualize → pooled materialization

```plantuml
@startuml
skinparam maxMessageSize 200
participant "XAML Loader" as X
participant "WorkflowView (UserControl)" as W
participant "WorkflowSurfaceBehavior" as B
participant "CanvasLayout" as L
participant "Tree helper (Core)" as H
participant "ViewPool / ViewManager" as VP

X -> W : set IsEnabled + ScrollViewerName/CanvasName/\\nGridDecoratorName/PointerPressSourceName/MinimapOverlayName + ZoomEnabled
B -> B : OnIsEnabledChanged -> Attach(control)
B -> B : subscribe Loaded/Unloaded/DataContextChanged/\\nPreviewMouseMove + MouseUp
X -> W : load finishes; DataContext = tree VM
B -> B : Refresh(host)
B -> B : ApplyLayout: WorkflowCanvasTransformBehavior.Apply(host,\\nTranslateTransform(Layout.ActualOffset))
B -> L : read ActualOffset (world translate == NegativeOffset)
B -> B : UpdateGridDecorator -> push scroll/content offsets\\n+ SetVirtualizeInset(decorator.RulerBand)
B -> B : UpdateMinimapOverlay -> push offsets + viewport + tree
B -> H : UpdateVisibleRegion: Helper.Viewport = Viewport(x,y,w,h)
B -> L : Layout.ViewportOffset = viewport (serialization round-trip)
H -> H : Virtualize(Viewport): spatial maps -> VisibleItems\\n(VirtualLink + visible nodes + their whole links)
H --> VP : VisibleItems.CollectionChanged (add/remove)
VP -> VP : ViewManager.OnCollectionChanged -> pending batch
VP -> VP : 3 items per dispatcher Background tick
VP -> VP : AddOrReuseView: pool hit or template.LoadContent
VP --> X : only visible node/link views on the Canvas
@enduml
```

## (b) Pan & pointer tracking (blank surface)

Panning starts only on "blank" surface presses (never over a node/slot visual or the scroll bar); every non-panning move still feeds `SetPointerCommand`.

```plantuml
@startuml
actor User
participant "PointerPressSource" as S
participant "WorkflowView" as W
participant "WorkflowSurfaceBehavior" as B
participant "ScrollViewer / Canvas" as SV
participant "WorkflowSurfaceMath" as M
participant "Tree (Core)" as T

User -> S : left-press on blank surface
S -> B : PreviewMouseDown (PointerPressSource subscribed)
B -> B : IsSurfaceBlankInteraction? yes -> IsPanning = true; capture
User -> W : move
B -> B : OnCanvasPanMoved
B -> M : desired offset; ClampScrollOffset (overshoot growth)
M --> B : grows NegativeOffset/PositiveOffset past an edge\\n(DefaultPanExtendRatio = 0.15)
B -> SV : ScrollToHorizontal/VerticalOffset
B -> B : UpdateVisibleRegion -> Helper.Viewport write
B -> T : SetPointerCommand.Execute(ToWorldAnchor(x,y)) when not panning
User -> W : release left button
B -> B : OnMouseUp -> IsPanning = false; release capture
@enduml
```

## (c) Zoom (Ctrl + mouse wheel)

Zoom is a *collapse* factor: the surface divides `Layout.Scale` by $1/1.1$ on wheel-up. Node `Anchor`/`Size` getters collapse toward the world origin by that scale, so zooming moves the model geometry, not a single canvas transform.

```plantuml
@startuml
actor User
participant "ScrollViewer" as SV
participant "WorkflowSurfaceBehavior" as B
participant "CanvasLayout" as L
participant "NodeDefaultViewModel" as N
participant "WorkflowSpatialEx" as S
participant "WorkflowSlotLayoutBehavior" as SL

User -> SV : Ctrl + wheel up
SV -> B : PreviewMouseWheel (ZoomEnabled hooked)
B -> B : factor = 1/1.1; next = clamp(Scale*factor, 0.1, 10)
B -> L : Layout.CollapsePivot = world point under viewport center
B -> L : Layout.Scale = next
L -> L : Update(): auto-extend ActualSize for Scale<1;\\nActualOffset = NegativeOffset
L -> N : Scale.PropertyChanged -> WorkflowNodeScaleTracker
N -> N : re-raise Anchor/Size (collapsed = world / Scale)
B -> L : EnsureNegativeCover(tree) - grow NegativeOffset if negative content
B -> B : ApplyLayout + UpdateLayout (canvas adopts new extent)
B -> B : PivotCenterScroll -> scroll target keeps pivot under center
B -> SV : ScrollToHorizontal/VerticalOffset
S -> S : re-virtualize (collapsed anchors moved) -> VisibleItems diff
SL -> SL : LayoutUpdated/SizeChanged -> slot anchors follow collapsed node
@enduml
```

## (d) Node drag → `MoveCommand` → world anchor update

The drag behavior converts the delta in the coordinate host's space into an `Offset`; `StandardMove` maps the view-space delta back to a world anchor by the current scale, so the node follows the pointer even while zoomed.

```plantuml
@startuml
actor User
participant "NodeView" as NV
participant "WorkflowNodeDragBehavior" as D
participant "IWorkflowNodeViewModel" as VM
participant "WorkflowNodeEx.StandardMove" as SM
participant "Tree helper (Core)" as H

User -> NV : press left button
NV -> D : PreviewMouseLeftButtonDown
D -> D : ResolveCoordinateHost (name or type, default Canvas)
D -> D : IsDragging = true; Mouse.Capture
User -> NV : move
NV -> D : PreviewMouseMove
D -> VM : MoveCommand.Execute(new Offset(dx, dy))
VM -> SM : Helper.Move -> StandardMove(offset)
SM -> VM : Anchor = ((collapsed + offset) * scale) as world anchor
VM -> H : re-raise Anchor; Parent.GetHelper().MarkDirty()
H -> H : re-virtualize; minimap / surface invalidate
NV -> NV : Canvas.Left/Top binding moves the view
User -> NV : release / LostMouseCapture
D -> D : IsDragging = false; release capture
@enduml
```

## (e) Slot connection gesture → virtual link lifecycle

Connecting is two commands on the slot plus a cancel path on the surface. When a valid receiver is reached the tree registers a link; the spatial index and the visible set are updated from the `LinkAdded` event.

```plantuml
@startuml
actor User
participant "SlotView" as S
participant "WorkflowSlotConnectionBehavior" as C
participant "IWorkflowSlotViewModel" as Slot
participant "Tree (IWorkflowTreeViewModel)" as Tree
participant "Spatial index" as Idx

User -> S : press left button on an output slot
S -> C : PreviewMouseLeftButtonDown
C -> Slot : SendConnectionCommand.Execute(null)
Slot -> Tree : StandardApplyConnection -> VirtualLink.IsVisible = true
User -> S : release over a compatible input slot
S -> C : PreviewMouseLeftButtonUp
C -> Slot : ReceiveConnectionCommand.Execute(null)
Slot -> Tree : validate receiver; create Link (Links/LinksMap registered)
Tree -> Idx : LinkAdded -> node-pair indexed
Tree -> Tree : re-virtualize -> VisibleItems + minimap dirty
User -> S : release on blank surface instead
C -> Tree : (surface behavior) ResetVirtualLinkCommand\\nwhen VirtualLink.IsVisible
@enduml
```

## (f) Minimap projection & drag navigation

The minimap is an overlay element implementing `IWorkflowMinimapOverlay` (WPF `FrameworkElement`, Avalonia `Control`, WinUI `Canvas`, MAUI `GraphicsView`, Jalium `FrameworkElement`, Razor SVG component). The surface pushes scroll/content offsets, the viewport size and the tree into it; it marks itself dirty from model events (never polls) and renders a whole-graph thumbnail plus a viewport indicator.

```plantuml
@startuml
actor User
participant "ScrollViewer" as SV
participant "WorkflowSurfaceBehavior" as B
participant "WorkflowMinimapOverlay" as M
participant "WorkflowSurfaceMath" as Math
participant "Tree nodes/links" as T

SV -> B : ScrollChanged
B -> M : ScrollOffsetX/Y, ContentOffsetX/Y,\\nViewportWidth/Height, WorkflowTree
B -> B : UpdateVisibleRegion (same pass)
T -> M : CollectionChanged / node Anchor/Size / slot Anchor
M -> M : MarkDirty (dirty flags, no polling)
M -> M : RefreshMinimapData: WorkflowBounds.FromNodes -> global bounds
M -> M : cache one thumb rect per node
User -> M : press / drag the viewport indicator
M -> Math : MinimapToWorld(mm -> world)
M -> Math : MinimapToScroll(world -> scroll offset)
M -> SV : ClampScrollOffset + ScrollToHorizontal/VerticalOffset
SV -> B : ScrollChanged (feedback loop closes)
@enduml
```
