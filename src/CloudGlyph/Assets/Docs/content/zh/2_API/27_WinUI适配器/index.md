# WinUI 适配器

`VeloxDev.WinUI` 为 WinUI 3 / Windows App SDK 闭合七个工作流角色。两处平台形态与 XAML 桌面适配器不同：画布平移是组合平移而不是附着渲染变换；连线视图把自身放在画布负偏移处，使几何不越出自己的盒子。公开表面位于命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors`（程序集 `VeloxDev.WinUI`），另有 `VeloxDev.WorkflowSystem.ViewHosting`、`VeloxDev.TransitionSystem` 与 `VeloxDev.DynamicTheme`。

| 角色 | WinUI 类型 |
| --- | --- |
| 表面宿主 | `WorkflowSurfaceBehavior` |
| 画布变换 | `WorkflowCanvasTransformBehavior` |
| 节点拖拽 | `WorkflowNodeDragBehavior` |
| 插槽连接 | `WorkflowSlotConnectionBehavior` |
| 插槽布局 | `WorkflowSlotLayoutBehavior` |
| 视图池 | `ViewPool` |
| 小地图 | `WorkflowMinimapOverlay` |
| 模型事件 | `WorkflowEvents` |

网格装饰器由宿主提供。参考 demo 位于 `Examples/Workflow/WinUI Trimmed/Demo/Views/Workflow/`；请把 `TreeView.xaml` 与 `LinkView.xaml.cs` 一起读，它们是实现偏移帧的那一对。

WinUI 有 demo，但**没有无头一致性套件**：`Src/Test/Headless/README.md` 记录了它没有无窗口宿主。本页面的内容描述的是 demo 验证过的表面。

## 页面

- [表面行为](00_表面行为/index.md) —— 附着点、`Refresh` 与组合平移的平移方式。
- [画布变换与节点拖拽](01_画布变换与节点拖拽/index.md) —— 变换载体与拖拽行为。
- [插槽行为](02_插槽行为/index.md) —— 连接与画布局部锚点测量。
- [视图池](03_视图池/index.md) —— 附着池及其管道。
- [视图托管](04_视图托管/index.md) —— 托管层，含内部布局跟踪器。
- [小地图覆盖层](05_小地图覆盖层/index.md) —— 覆盖层及其管道。
- [工作流事件](06_工作流事件/index.md) —— 接收器附着属性。
- [过渡与主题桥接](07_过渡与主题桥接/index.md) —— 过渡与主题类型。

```csharp
using VeloxDev.WorkflowSystem.AttachedBehaviors;

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
host.Loaded += (_, _) => WorkflowSurfaceBehavior.Refresh(host);
```

**预期结果：** 表面在 `Loaded` 后解析命名部件，通过平移画布完成平移，并注册 `WorkflowInput.Scroller` / `Navigator`。
