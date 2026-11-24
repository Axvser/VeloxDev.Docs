# Avalonia 适配器

`VeloxDev.Avalonia` 通过 `AvaloniaProperty` 注册、用 `FindControl` 解析，闭合与 WPF 适配器相同的七个工作流角色。demo 默认启用编译绑定，因此模板带有具体的 `x:DataType`。公开表面位于命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors`（程序集 `VeloxDev.Avalonia`），另有 `VeloxDev.WorkflowSystem.ViewHosting`、`VeloxDev.TransitionSystem` 与 `VeloxDev.DynamicTheme`。

| 角色 | Avalonia 类型 |
| --- | --- |
| 表面宿主 | `WorkflowSurfaceBehavior` |
| 画布变换 | `WorkflowCanvasTransformBehavior` |
| 节点拖拽 | `WorkflowNodeDragBehavior` |
| 插槽连接 | `WorkflowSlotConnectionBehavior` |
| 插槽布局 | `WorkflowSlotLayoutBehavior` |
| 视图池 | `ViewPool` |
| 小地图 | `WorkflowMinimapOverlay` |
| 模型事件 | `WorkflowEvents` |

网格装饰器由宿主提供：由 `GridDecoratorName` 命名的元素实现 `IWorkflowGridDecorator`。Avalonia 没有预览滚轮阶段，适配器因此以 `RoutingStrategies.Tunnel` 注册滚轮处理器。

参考 demo 位于 `Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/`；工程位于 `Demo/Demo/`，因此视图比 WPF demo 深一层。Avalonia 无头套件还会驱动真实指针输入，验证 Ctrl+滚轮方向与 `[0.1, 10]` 缩放钳制。

## 页面

- [表面行为](00_表面行为/index.md) —— 附着点与 `Refresh`。
- [画布变换与节点拖拽](01_画布变换与节点拖拽/index.md) —— 变换载体与拖拽行为。
- [插槽行为](02_插槽行为/index.md) —— 连接与锚点测量。
- [视图池](03_视图池/index.md) —— 附着池、管道与 Avalonia 池策略。
- [视图托管](04_视图托管/index.md) —— 具体托管层。
- [小地图覆盖层](05_小地图覆盖层/index.md) —— 覆盖元素及其管道。
- [工作流事件](06_工作流事件/index.md) —— 接收器附着属性。
- [过渡与主题桥接](07_过渡与主题桥接/index.md) —— 过渡与主题类型。

```csharp
using VeloxDev.WorkflowSystem.AttachedBehaviors;

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**预期结果：** 表面解析命名部件、发布视口，并注册 `WorkflowInput.Scroller` / `Navigator`；普通滚轮经适配器滚动，而不是 `ScrollViewer` 惯性。
