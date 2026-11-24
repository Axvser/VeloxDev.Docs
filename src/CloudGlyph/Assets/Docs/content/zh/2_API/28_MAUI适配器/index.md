# MAUI 适配器

`VeloxDev.MAUI` 为 .NET MAUI 闭合工作流表面。宿主是 `ContentView`，树作为其 `BindingContext` 传入，连线由单个视口尺寸的 `WorkflowLinkOverlay` 绘制，而不是每条连线一个池化视图。适配器没有 `WorkflowCanvasTransformBehavior`；表面与视图排列器拥有几何。公开表面位于命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors`（程序集 `VeloxDev.MAUI`），另有 `VeloxDev.WorkflowSystem.ViewHosting`、`VeloxDev.TransitionSystem` 与 `VeloxDev.DynamicTheme`。

| 角色 | MAUI 类型 |
| --- | --- |
| 表面宿主 | `WorkflowSurfaceBehavior` |
| 节点拖拽 | `WorkflowNodeDragBehavior` |
| 插槽连接 | `WorkflowSlotConnectionBehavior` |
| 插槽布局 | `WorkflowSlotLayoutBehavior` |
| 视图池 | `ViewPool` |
| 连线渲染 | `WorkflowLinkOverlay` |
| 小地图 | `WorkflowMinimapOverlay` |
| 模型事件 | `WorkflowEvents` |

参考 demo 位于 `Examples/Workflow/MAUI Trimmed/Demo/Controls/Workflow/` —— 是 `Controls/`，不是 `Views/`。MAUI 有 demo，但**没有无头一致性套件**：`Src/Test/Headless/README.md` 记录了它没有无窗口宿主。

## 页面

- [表面行为](00_表面行为/index.md) —— 附着点、`Refresh`、手势与 `RequestViewportRestore`。
- [节点拖拽](01_节点拖拽/index.md) —— 拖拽行为。
- [插槽行为](02_插槽行为/index.md) —— 连接（含候选接收端探测）与布局。
- [视图池](03_视图池/index.md) —— 附着池及其管道。
- [视图托管](04_视图托管/index.md) —— 具体托管层。
- [连线覆盖层](05_连线覆盖层/index.md) —— 单个视口尺寸的连线程。
- [小地图覆盖层](06_小地图覆盖层/index.md) —— 小地图及其管道。
- [工作流事件](07_工作流事件/index.md) —— 接收器附着属性。
- [过渡与主题桥接](08_过渡与主题桥接/index.md) —— 过渡与主题类型。

```csharp
using VeloxDev.WorkflowSystem.AttachedBehaviors;

WorkflowSurfaceBehavior.SetScrollViewerName(host, "PART_ScrollViewer");
WorkflowSurfaceBehavior.SetCanvasName(host, "PART_Canvas");
WorkflowSurfaceBehavior.SetIsEnabled(host, true);
WorkflowSurfaceBehavior.Refresh(host);
```

**预期结果：** 表面解析命名部件、池化节点视图，连线覆盖层绘制连线；树是 `ContentView.BindingContext`。
