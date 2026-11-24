# WPF 适配器

`VeloxDev.WPF` 用 WPF 附着行为闭合 Core 的工作流表面。公开表面位于命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors`（程序集 `VeloxDev.WPF`），另有 `VeloxDev.WorkflowSystem.ViewHosting` 中闭合的视图托管组合，以及 `VeloxDev.TransitionSystem` 与 `VeloxDev.DynamicTheme` 中的过渡/主题桥接。

| 角色 | WPF 类型 |
| --- | --- |
| 表面宿主 | `WorkflowSurfaceBehavior` |
| 画布变换 | `WorkflowCanvasTransformBehavior` |
| 节点拖拽 | `WorkflowNodeDragBehavior` |
| 插槽连接 | `WorkflowSlotConnectionBehavior` |
| 插槽布局 | `WorkflowSlotLayoutBehavior` |
| 视图池 | `ViewPool` |
| 小地图 | `WorkflowMinimapOverlay` |
| 模型事件 | `WorkflowEvents` |

适配器不附带网格装饰器；由 `GridDecoratorName` 命名的宿主元素实现 `IWorkflowGridDecorator`。`ViewPool` 与各行为从宿主的 `NameScope` 解析 `PART_*` 名称。

参考 demo 位于 `Examples/Workflow/WPF Trimmed/Demo/Views/Workflow/`。`Src/Test/Headless/` 下的 WPF 无头套件在没有窗口的情况下驱动同一表面。

## 页面

- [表面行为](00_表面行为/index.md) —— 附着点、`Refresh` 与生命周期。
- [画布变换与节点拖拽](01_画布变换与节点拖拽/index.md) —— 变换载体与拖拽行为。
- [插槽行为](02_插槽行为/index.md) —— 连接与锚点测量。
- [视图池](03_视图池/index.md) —— 附着池及其闭合管道。
- [视图托管](04_视图托管/index.md) —— 九个具体托管层。
- [小地图覆盖层](05_小地图覆盖层/index.md) —— 覆盖元素及其管道。
- [工作流事件](06_工作流事件/index.md) —— 接收器附着属性。
- [过渡与主题桥接](07_过渡与主题桥接/index.md) —— `VeloxDev.TransitionSystem` 与 `VeloxDev.DynamicTheme` 类型。

```csharp
using VeloxDev.WorkflowSystem.AttachedBehaviors;

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**预期结果：** 表面绑定命名部件，开始发布视口，并为 `host.DataContext` 中的树注册 `WorkflowInput.Scroller` / `Navigator`。
