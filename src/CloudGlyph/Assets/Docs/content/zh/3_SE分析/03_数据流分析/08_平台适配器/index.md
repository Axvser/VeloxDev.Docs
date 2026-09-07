# 08 · 平台适配器 — 数据流分析

下面的时序图追踪平台适配器层的核心数据流。它们以 WPF 适配器源码、Core 模型（`VeloxDev.WorkflowSystem`）以及 WPF/Avalonia/WinUI/MAUI 演示为依据；未经演示覆盖的各平台细节以源码推断并标注 `*推断所得*`。反复出现的关键步骤是可见区域馈送：画布写入 `Helper.Viewport`，空间索引据此重算 `Helper.VisibleItems`，`ViewPool` 只实例化这些视图。WPF/Avalonia/WinUI 演示把 `ViewPool` 绑定到 `Helper.VisibleItems`，MAUI 演示绑定其去链接包装；WinForms 与 Blazor 演示则绑定完整节点集合，把可见区域簿记交给画布自身。

## (a) 附加与布局接线 → 虚拟化 → 池化实例化

```plantuml
@startuml
skinparam maxMessageSize 200
participant "XAML Loader" as X
participant "WorkflowView (UserControl)" as W
participant "WorkflowSurfaceBehavior" as B
participant "CanvasLayout" as L
participant "Tree helper (Core)" as H
participant "ViewPool / ViewManager" as VP

X -> W : 设置 IsEnabled + ScrollViewerName/CanvasName/\\nGridDecoratorName/PointerPressSourceName/MinimapOverlayName + ZoomEnabled
B -> B : OnIsEnabledChanged -> Attach(control)
B -> B : 订阅 Loaded/Unloaded/DataContextChanged/\\nPreviewMouseMove + MouseUp
X -> W : 加载完成；DataContext = 树 VM
B -> B : Refresh(host)
B -> B : ApplyLayout: WorkflowCanvasTransformBehavior.Apply(host,\\nTranslateTransform(Layout.ActualOffset))
B -> L : 读取 ActualOffset（世界平移 == NegativeOffset）
B -> B : UpdateGridDecorator -> 推送滚动/内容偏移\\n+ SetVirtualizeInset(decorator.RulerBand)
B -> B : UpdateMinimapOverlay -> 推送偏移 + 视口 + 树
B -> H : UpdateVisibleRegion: Helper.Viewport = Viewport(x,y,w,h)
B -> L : Layout.ViewportOffset = 视口（供序列化往返）
H -> H : Virtualize(Viewport): 空间地图 -> VisibleItems\\n(VirtualLink + 可见节点 + 它们完整的连线)
H --> VP : VisibleItems.CollectionChanged（增/删）
VP -> VP : ViewManager.OnCollectionChanged -> 待处理批次
VP -> VP : 每 dispatcher Background 滴答 3 项
VP -> VP : AddOrReuseView: 命中池或 template.LoadContent
VP --> X : 只在 Canvas 上实例化可见的节点/连线视图
@enduml
```

## (b) 平移与指针追踪（空白画布）

平移只在按下"空白"画布表面时开始（绝不在节点/槽视觉或滚动条之上）；每次未平移的移动仍会喂给 `SetPointerCommand`。

```plantuml
@startuml
actor User
participant "PointerPressSource" as S
participant "WorkflowView" as W
participant "WorkflowSurfaceBehavior" as B
participant "ScrollViewer / Canvas" as SV
participant "WorkflowSurfaceMath" as M
participant "Tree (Core)" as T

User -> S : 在空白画布上按下左键
S -> B : PreviewMouseDown（PointerPressSource 已订阅）
B -> B : IsSurfaceBlankInteraction? 是 -> IsPanning = true; 捕获
User -> W : 移动
B -> B : OnCanvasPanMoved
B -> M : 期望偏移；ClampScrollOffset（越界增长）
M --> B : 越过边缘时增长 NegativeOffset/PositiveOffset\\n(DefaultPanExtendRatio = 0.15)
B -> SV : ScrollToHorizontal/VerticalOffset
B -> B : UpdateVisibleRegion -> 写入 Helper.Viewport
B -> T : 未平移时 SetPointerCommand.Execute(ToWorldAnchor(x,y))
User -> W : 松开左键
B -> B : OnMouseUp -> IsPanning = false; 释放捕获
@enduml
```

## (c) 缩放（Ctrl + 鼠标滚轮）

缩放是一个*折叠*因子：画布在滚轮向上时把 `Layout.Scale` 除以 $1/1.1$。节点 `Anchor`/`Size` getter 按该比例朝世界原点折叠，因此缩放移动的是模型几何，而非单个画布变换。

```plantuml
@startuml
actor User
participant "ScrollViewer" as SV
participant "WorkflowSurfaceBehavior" as B
participant "CanvasLayout" as L
participant "NodeDefaultViewModel" as N
participant "WorkflowSpatialEx" as S
participant "WorkflowSlotLayoutBehavior" as SL

User -> SV : Ctrl + 滚轮向上
SV -> B : PreviewMouseWheel（已挂接 ZoomEnabled）
B -> B : factor = 1/1.1; next = clamp(Scale*factor, 0.1, 10)
B -> L : Layout.CollapsePivot = 视口中心下的世界点
B -> L : Layout.Scale = next
L -> L : Update(): Scale<1 时自动扩展 ActualSize;\\nActualOffset = NegativeOffset
L -> N : Scale.PropertyChanged -> WorkflowNodeScaleTracker
N -> N : 重新触发 Anchor/Size（折叠 = 世界 / Scale）
B -> L : EnsureNegativeCover(tree) - 存在负内容时增长 NegativeOffset
B -> B : ApplyLayout + UpdateLayout（画布采用新范围）
B -> B : PivotCenterScroll -> 滚动目标使枢轴保持在中心
B -> SV : ScrollToHorizontal/VerticalOffset
S -> S : 重新虚拟化（折叠锚点已移动）-> VisibleItems diff
SL -> SL : LayoutUpdated/SizeChanged -> 槽锚点跟随折叠后的节点
@enduml
```

## (d) 节点拖拽 → `MoveCommand` → 世界锚点更新

拖拽行为把坐标宿主空间中的增量转成 `Offset`；`StandardMove` 按当前比例把视图空间增量映射回世界锚点，使节点在缩放状态下也跟随指针。

```plantuml
@startuml
actor User
participant "NodeView" as NV
participant "WorkflowNodeDragBehavior" as D
participant "IWorkflowNodeViewModel" as VM
participant "WorkflowNodeEx.StandardMove" as SM
participant "Tree helper (Core)" as H

User -> NV : 按下左键
NV -> D : PreviewMouseLeftButtonDown
D -> D : 解析 CoordinateHost（名称或类型，默认 Canvas）
D -> D : IsDragging = true; Mouse.Capture
User -> NV : 移动
NV -> D : PreviewMouseMove
D -> VM : MoveCommand.Execute(new Offset(dx, dy))
VM -> SM : Helper.Move -> StandardMove(offset)
SM -> VM : Anchor = ((collapsed + offset) * scale) 作为世界锚点
VM -> H : 重新触发 Anchor; Parent.GetHelper().MarkDirty()
H -> H : 重新虚拟化；小地图 / 画布失效
NV -> NV : Canvas.Left/Top 绑定移动视图
User -> NV : 松开 / LostMouseCapture
D -> D : IsDragging = false; 释放捕获
@enduml
```

## (e) 槽连线手势 → 虚拟连线生命周期

连线是对槽的两个命令外加画布上的取消路径。到达合法接收槽时树会注册一条连线；`LinkAdded` 事件触发空间索引与可见集更新。

```plantuml
@startuml
actor User
participant "SlotView" as S
participant "WorkflowSlotConnectionBehavior" as C
participant "IWorkflowSlotViewModel" as Slot
participant "Tree (IWorkflowTreeViewModel)" as Tree
participant "Spatial index" as Idx

User -> S : 在输出槽上按下左键
S -> C : PreviewMouseLeftButtonDown
C -> Slot : SendConnectionCommand.Execute(null)
Slot -> Tree : StandardApplyConnection -> VirtualLink.IsVisible = true
User -> S : 在兼容输入槽上松开
S -> C : PreviewMouseLeftButtonUp
C -> Slot : ReceiveConnectionCommand.Execute(null)
Slot -> Tree : 校验接收槽；创建 Link（登记 Links/LinksMap）
Tree -> Idx : LinkAdded -> 节点对已索引
Tree -> Tree : 重新虚拟化 -> VisibleItems + 小地图置脏
User -> S : 改在空白画布上松开
C -> Tree : （经画布行为）VirtualLink.IsVisible 时\\nResetVirtualLinkCommand
@enduml
```

## (f) 小地图投影与拖拽导航

小地图是实现了 `IWorkflowMinimapOverlay` 的覆盖层元素（WPF `FrameworkElement`、Avalonia `Control`、WinUI `Canvas`、MAUI `GraphicsView`、Jalium `FrameworkElement`、Razor SVG 组件）。画布把滚动/内容偏移、视口尺寸与树推给它；它通过模型事件把自身标记为脏（从不轮询），并渲染整图缩略图外加视口指示框。

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
B -> B : UpdateVisibleRegion（同一次遍历）
T -> M : CollectionChanged / 节点 Anchor/Size / 槽 Anchor
M -> M : MarkDirty（脏标记，无轮询）
M -> M : RefreshMinimapData: WorkflowBounds.FromNodes -> 全局边界
M -> M : 缓存每个节点一个缩略图矩形
User -> M : 按下 / 拖拽视口指示框
M -> Math : MinimapToWorld(mm -> 世界)
M -> Math : MinimapToScroll(世界 -> 滚动偏移)
M -> SV : ClampScrollOffset + ScrollToHorizontal/VerticalOffset
SV -> B : ScrollChanged（反馈回路闭合）
@enduml
```
