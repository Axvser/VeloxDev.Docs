# 08 · 平台适配器 — 数据流分析

下面的时序图追踪平台适配器层的五条核心数据流。它们以 WPF 适配器源码和 WPF/Avalonia/Blazor 演示为依据；未经演示覆盖的各平台细节以源码推断并标注 `*推断所得*`。

## (a) 附加行为接线：XAML 加载 → 行为附加 → 视口 → `ViewPool` 虚拟化

```plantuml
@startuml
skinparam maxMessageSize 200
participant "XAML Loader" as X
participant "WorkflowView (host)" as W
participant "WorkflowSurfaceBehavior" as B
participant "ScrollViewer / Canvas" as SV
participant "Helper (tree VM)" as H
participant "ViewPool / ViewManager" as VP

X -> W : 加载 XAML；设置 DataContext = IWorkflowTreeViewModel
X -> W : WorkflowSurfaceBehavior.IsEnabled = True
activate B
B -> B : Attach(control)
B -> B : 订阅 Loaded / DataContextChanged / ScrollChanged / 鼠标事件
B -> W : Refresh(host)
B -> SV : 解析 PART_ScrollViewer / PART_Canvas / 装饰层 / 小地图
B -> B : ApplyLayout -> WorkflowCanvasTransformBehavior.Apply(host, translate)
B -> H : GetHelper().Viewport = Viewport(x, y, viewportW, viewportH)
B -> H : Layout.ViewportOffset = Offset(x, y)
X -> VP : ViewPool.ItemsSource = Helper.VisibleItems
activate VP
VP -> VP : ViewManager.Attach(collection)
VP -> VP : 安排分批渲染（每 dispatcher 滴答 3 个）
VP -> VP : 每个可见项 AddOrReuseView（命中池或 template.LoadContent）
VP --> X : 只在 Canvas 上实例化可见的节点/连接视图
deactivate VP
deactivate B
@enduml
```

## (b) 拖拽移动：`WorkflowNodeDragBehavior` → `MoveCommand`

```plantuml
@startuml
actor User
participant "NodeView header" as N
participant "WorkflowNodeDragBehavior" as D
participant "IWorkflowNodeViewModel" as VM
participant "Layout" as L

User -> N : 按下左键
N -> D : PreviewMouseLeftButtonDown
D -> D : 解析 CoordinateHost（PART_Canvas 或类型回退）
D -> D : state.IsDragging = true; Mouse.Capture(header)
User -> N : 移动
N -> D : PreviewMouseMove
D -> VM : MoveCommand.Execute(new Offset(dx, dy))
VM -> L : Anchor += delta；必要时增长 NegativeOffset/PositiveOffset
N -> D : 松开左键 / LostMouseCapture
D -> D : state.IsDragging = false；释放捕获
@enduml
```

## (c) 槽连线：`WorkflowSlotConnectionBehavior` → `SendConnectionCommand` / `ReceiveConnectionCommand`

```plantuml
@startuml
actor User
participant "SlotView" as S
participant "WorkflowSlotConnectionBehavior" as C
participant "IWorkflowSlotViewModel" as Slot
participant "Tree (IWorkflowTreeViewModel)" as Tree

User -> S : 按下左键
S -> C : PreviewMouseLeftButtonDown
C -> Slot : SendConnectionCommand.Execute(null)
Slot -> Tree : 从此槽开始虚拟连接
User -> S : 松开左键
S -> C : PreviewMouseLeftButtonUp
C -> Slot : ReceiveConnectionCommand.Execute(null)
Slot -> Tree : 解析接收槽；创建 Link（可撤销、入空间索引）
User -> S : 在空白画布上松开
S -> Tree : ResetVirtualLinkCommand.Execute(null)（经画布行为）
@enduml
```

## (d) 小地图投影流

```plantuml
@startuml
participant "ScrollViewer" as SV
participant "WorkflowSurfaceBehavior" as B
participant "WorkflowMinimapOverlay" as M
participant "Tree (IWorkflowTreeViewModel)" as VM
actor User

SV -> B : ScrollChanged
B -> M : 设置 ScrollOffsetX/Y、ContentOffsetX/Y、ViewportWidth/Height、WorkflowTree
B -> VM : GetHelper().Viewport = 当前视口
M -> M : RefreshMinimapData：节点包围盒求并 -> globalBounds
M -> M : ComputeTransform：scale = min(drawW/gb.W, drawH/gb.H)
M -> M : OnRender：绘制节点矩形 + 视口指示矩形
User -> M : 按下 / 拖拽视口指示框
M -> M : NavigateToWorld(adjX, adjY) 映射回世界坐标
M -> SV : ScrollToHorizontalOffset / ScrollToVerticalOffset
M -> VM : 在边缘增长 Layout.NegativeOffset/PositiveOffset
SV -> B : ScrollChanged（反馈回路闭合）
@enduml
```

## (e) 模板脚手架流：`dotnet new` → 生成文件

```plantuml
@startuml
actor User
participant "dotnet CLI" as CLI
participant "Template Engine" as T
participant "File System" as FS

User -> CLI : dotnet new install VeloxDev.WPF.Templates
CLI -> T : 注册 wpf-v-* 短名
User -> CLI : dotnet new wpf-v-tree -n TreeView -ns MyApp.Views -o Views
CLI -> T : 实例化 workflow-tree-view 模板
T -> T : 替换 TemplateNamespace -> MyApp.Views；TemplateClass -> TreeView
T -> FS : 写入 TreeView.xaml + TreeView.xaml.cs（WorkflowSurfaceBehavior 已接好）
User -> CLI : dotnet new wpf-v-node / -slot / -link / -selector / -decorator / -minimap
CLI -> T : 实例化每个项模板
T -> FS : 写入 NodeView / SlotView / LinkView / TemplateSelector / GridDecorator / MinimapOverlay
User -> CLI : dotnet build
CLI -> FS : 编译 Views 并引用 VeloxDev.WPF 包
@enduml
```
