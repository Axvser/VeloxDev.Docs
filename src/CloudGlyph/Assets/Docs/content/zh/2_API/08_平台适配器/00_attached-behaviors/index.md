# API — 工作流附加行为

每个 GUI 适配器都通过 **`VeloxDev.WorkflowSystem.AttachedBehaviors`** 命名空间中共享的一组类型承载工作流视图（源码：`Src/Adapters/<Adapter>/Attached/Workflow/*.cs`）。类名在所有平台一致，但各适配器用该框架的基类与属性系统来声明它们：

| 适配器 | 行为类使用的基类 / 属性系统 |
|---|---|
| WPF、WinUI、Jalium | 附加 `DependencyProperty`；行为类派生自 `DependencyObject`（框架要求处用静态类） |
| Avalonia | 附加 `AvaloniaProperty`（`RegisterAttached<Owner, Host, T>`）；类派生自 `AvaloniaObject` |
| MAUI | `BindableProperty.CreateAttached`；带 `BindableObject` 上 `Get*` / `Set*` 的静态持有类 |
| WinForms | 无附加属性系统 —— 带 `Control` 上 `Get*` / `Set*` 与私有「控件级状态表」的静态持有类 |
| Razor | Blazor 组件（`.razor` 分部类）而非附加属性；事件处理器以公共方法形式暴露 |

于是 XAML 视图绑定 `behaviors:WorkflowSurfaceBehavior.IsEnabled="True"`，WinForms 宿主调用 `WorkflowSurfaceBehavior.SetIsEnabled(control, true)`，Razor 页面使用 `<WorkflowSurfaceBehavior>` 组件。**下面这些名称与形态在全部七个适配器上均已按源码验证**；未被工作流 Demo 驱动的行为细节标记为 `*推断所得*`。

## 类型清单

| 类型 | 角色 | 适配器 |
|---|---|---|
| `WorkflowSurfaceBehavior` | 表面宿主行为：平移、缩放钩子、滚动/视口数据推送、命名控件解析 | 全部七个 |
| `WorkflowCanvasTransformBehavior` | 持有应用到节点/连接视图的画布渲染变换或平移偏移 | WPF、Avalonia、WinUI、WinForms、Jalium、Razor（MAUI 无） |
| `ViewPool` / `ViewManager` | 基于条目集合的对象池视图容器 | 全部七个（Razor 为组件形式） |
| `WorkflowNodeDragBehavior` | 让节点可拖拽（执行 `MoveCommand`） | 全部七个 |
| `WorkflowSlotConnectionBehavior` | 按下/松开时连接槽（执行 `SendConnectionCommand` / `ReceiveConnectionCommand`） | 全部七个 |
| `WorkflowSlotLayoutBehavior` | 让槽锚点与节点布局保持同步 | 全部七个 |
| `WorkflowMinimapOverlay` | 节点/连接缩略图 + 可拖拽视口指示框 | 全部七个 |
| `WorkflowLinkOverlay` | 仅 MAUI：连接折线覆盖层，同时承载拖拽几何 | MAUI |
| `WorkflowGridDecorator` | 仅 Jalium：网格/标尺装饰元素 | Jalium |
| `WorkflowTreeView` | 仅 Jalium：复合宿主控件（`PART_*` 命名部件） | Jalium |
| `IWorkflowTemplateSelector` | 对应 `DataTemplateSelector` 的工厂契约 | WinForms、Jalium |
| `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` | 覆盖层实现的数据交换契约；**现定义于 Core**，命名空间 `VeloxDev.WorkflowSystem` | 全部七个（由覆盖层实现） |

## 页面

- [00_surface](00_surface/index.md) — `WorkflowSurfaceBehavior` 与 `WorkflowCanvasTransformBehavior`。
- [01_view-pool](01_view-pool/index.md) — `ViewPool`、`ViewManager` 与模板选择契约。
- [02_node-slot](02_node-slot/index.md) — `WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`。
- [03_minimap](03_minimap/index.md) — `WorkflowMinimapOverlay` 与 `IWorkflowGridDecorator` / `IWorkflowMinimapOverlay` 契约。
- [04_adapter-overlays](04_adapter-overlays/index.md) — 适配器特有的覆盖层 / 宿主类型（`WorkflowLinkOverlay`、Jalium 的 `WorkflowGridDecorator` / `WorkflowTreeView`、Razor 组件辅助）。
