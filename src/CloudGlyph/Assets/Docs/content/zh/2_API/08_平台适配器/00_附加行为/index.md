# API — 工作流附加行为

每个 GUI 适配器都通过 **`VeloxDev.WorkflowSystem.AttachedBehaviors`** 命名空间中共享的一组类型承载工作流视图（源码：`Src/Adapters/<Adapter>/Attached/Workflow/*.cs`）。类名在所有平台一致，但各适配器用该框架的基类与属性系统来声明它们：

| 适配器 | 行为类使用的基类 / 属性系统 |
|---|---|
| WPF、WinUI | 附加 `DependencyProperty`；行为类派生自 `DependencyObject`（表面与三个手势行为为 `sealed`；画布变换为 `static class`） |
| Jalium | 附加 `DependencyProperty`；表面为 `static class`，手势行为派生自 `DependencyObject`；画布变换是表面的 `CanvasTransform` 附加属性（无独立类） |
| Avalonia | 附加 `AvaloniaProperty`（`RegisterAttached<Owner, Host, T>`）；类派生自 `AvaloniaObject` |
| MAUI | `BindableProperty.CreateAttached`；带 `BindableObject` 上 `Get*` / `Set*` 的静态持有类 |
| WinForms | 无附加属性系统 —— 带 `Control` 上 `Get*` / `Set*` 与私有「控件级状态表」的静态持有类 |
| Razor | Blazor 组件（`.razor` 分部类）而非附加属性；事件处理器以公共方法形式暴露 |

于是 XAML 视图绑定 `behaviors:WorkflowSurfaceBehavior.IsEnabled="True"`，WinForms 宿主调用 `WorkflowSurfaceBehavior.SetIsEnabled(control, true)`，Razor 页面使用 `<WorkflowSurfaceBehavior>` 组件。**下面这些名称与形态在全部七个适配器上均已按源码验证**；未被工作流 Demo 驱动的行为细节标记为 `*推断所得*`。

## 类型清单

| 类型 | 角色 | 适配器 |
|---|---|---|
| `WorkflowSurfaceBehavior` | 表面宿主行为：平移、缩放钩子、滚动/视口数据推送、命名控件解析、连线菜单 | 全部七个（WPF/WinUI/Avalonia/MAUI 为 `sealed` 行为类；Jalium 为 `static class`） |
| `WorkflowCanvasTransformBehavior` | 持有应用到节点/连接视图的画布渲染变换或平移偏移 | WPF、Avalonia、WinUI、WinForms、Razor（MAUI 无；Jalium 改用 `WorkflowSurfaceBehavior.CanvasTransform`） |
| `ViewPool` / `ViewManager` | 基于条目集合的对象池视图容器 | 全部七个（Razor 为组件形式） |
| `WorkflowNodeDragBehavior` | 让节点可拖拽（执行 `MoveCommand`） | 全部七个 |
| `WorkflowSlotConnectionBehavior` | 按下/松开时连接槽（执行 `SendConnectionCommand` / `ReceiveConnectionCommand`），并在指针移动时报告候选接收口 | 全部七个 |
| `WorkflowSlotLayoutBehavior` | 让槽锚点与节点布局保持同步 | 全部七个 |
| `WorkflowMinimapOverlay` | 节点/连接缩略图 + 可拖拽视口指示框 | 全部七个 |
| `WorkflowLinkOverlay` | 仅 MAUI：视口大小的绘制层，画那些自己没有视图的连接（立即模式宿主，以及池化连接视图成形之前的帧） | MAUI |
| `WorkflowLinkBounds` | 仅 Jalium：按画布局部点集定位连线视图并报告原点的静态辅助类 | Jalium |
| `WorkflowGridDecorator` | 网格/标尺装饰元素。WinForms 自带实现 `IWorkflowGridDecorator` 的 `Panel` 子类；Razor 为组件；XAML 适配器（含 Jalium）由 `*-v-decorator` 模板生成 | WinForms、Razor（WPF/Avalonia/WinUI/MAUI/Jalium：模板） |
| `WorkflowTreeView` | 复合宿主控件，生成的 WinForms 树视图条目从它派生（`PART_*` 命名部件、视图工厂） | WinForms |
| `WorkflowNodeAttachment` / `WorkflowSlotAttachment` / `WorkflowLinkAttachment` | 各角色**附加类**：生成的 WinForms 条目模板对自己已持有的控件调 `Attach(Control)`，而不是从基类派生 | WinForms |
| `WorkflowTemplateSelector` | 把模型绑到它视图上的工厂 —— 生成的 WinForms 选择器派生的类型 | WinForms |
| `IWorkflowTemplateSelector` | 对应 `DataTemplateSelector` 的工厂契约（仅 WinForms；Jalium 使用 `DataTemplateSelector`） | WinForms |
| `WorkflowEvents` | 把组件的**模型**事件经 `WorkflowEventRelay` 交给 `IWorkflow*EventSink` 的 `Node` / `Slot` / `Tree` 附加属性 | WPF、WinUI、Avalonia、MAUI、Jalium |
| `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` | 覆盖层实现的数据交换契约；**定义于 Core**，命名空间 `VeloxDev.WorkflowSystem` | 全部七个（由覆盖层实现） |

## 页面

- [工作流表面](00_工作流表面/index.md) — `WorkflowSurfaceBehavior` 与 `WorkflowCanvasTransformBehavior`。
- [视图池](01_视图池/index.md) — `ViewPool`、`ViewManager` 与模板选择契约。
- [节点与插槽](02_节点与插槽/index.md) — `WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`。
- [小地图](03_小地图/index.md) — `WorkflowMinimapOverlay` 与 `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` 契约。
- [适配器浮层](04_适配器浮层/index.md) — 适配器特有的覆盖层 / 宿主类型（`WorkflowLinkOverlay`、Jalium 的 `WorkflowLinkBounds` 与模板提供的部件、Razor 组件辅助）。
