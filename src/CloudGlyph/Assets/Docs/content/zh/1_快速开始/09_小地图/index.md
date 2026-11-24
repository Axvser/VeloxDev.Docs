# 小地图

小地图是同一棵树的另一份、小得多的读法：每个节点变成缩略块，一个矩形表示表面当前显示的范围。在小地图里拖动会移动视口。这个功能是一条 Core 管线加每家适配器的一个覆盖层控件；表面行为负责持续给管线喂数据。

## 这个功能覆盖什么

- **一次绘制基于缓存几何。** Core 的 `MinimapPipelineCore` 订阅树、节点与连线变化，标脏，并在下一次渲染前重建一次映射。一串属性变化只花一趟。
- **放在可用角落。** 小地图默认 200 × 140，离角落 12 px，被标尺带与滚动条让出的区域夹取。
- **拖动导航。** 在小地图里按下会把视口居中到该点；移动会继续居中，滚动偏移通过适配器的视口层写回表面。
- **自定义绘制是虚方法。** 适配器覆盖层画背景、节点缩略块与视口块；子类可以重写 `DrawMinimap`，也可以只设置画刷。

## 各部分在哪里

| 层 | 类型 | 职责 |
|---|---|---|
| Core | `MinimapPipelineCore<TSurface,TRenderer,TViewport,TInput>`、`MinimapHostCore<...>` | 树订阅、脏标记去抖、内容/视口映射、放置、拖动数学。 |
| Core | `IMinimapRenderer<TSurface>`、`IMinimapViewportHost`、`IMinimapInputHost` | 管线组合的三个平台层。 |
| Core | `MinimapDrawContext`、`MinimapMetrics`、`SurfaceAvailableArea` | 一趟的几何与尺寸/放置输入。 |
| Core | `IWorkflowMinimapOverlay` | 表面推入数据的交换契约。 |
| WPF | `WorkflowMinimapOverlay`、`MinimapPipeline`、`MinimapRenderer`、`MinimapViewportHost`、`MinimapInputHost` | WPF 闭合、依赖属性与绘制。 |
| WPF | `WorkflowSurfaceBehavior` | 解析 `MinimapOverlayName`，推入树、偏移、视口与可用角落。 |

其余六家适配器各有一个同角色的 `WorkflowMinimapOverlay`；Razor 的那个是组件，不是 `FrameworkElement`。

## 页面

- [前置条件](00_前置条件/index.md) —— 目标、包与示例。
- [挂载覆盖层](01_挂载覆盖层/index.md) —— 命名它、给它滚动容器、让表面喂它。
- [外观与导航](02_外观与导航/index.md) —— 尺寸、画刷、可见性、拖动、自定义绘制。
- [验证](03_验证/index.md) —— 运行、拖动、完整代码与运行声明。

## 一趟画什么

WPF 的默认绘制是小地图外框、`MappedNodes` 里每个节点一个缩略块，以及 `MappedViewport` 的视口指示块。它不画连线。`MinimapDrawContext` 携带节点矩形与视口矩形，不携带连线几何；想画连线的子类要从 `context.Tree` 自己算。

## 证据

- 示例：`Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/MinimapOverlay.cs`；完整示例在 `Examples/Workflow/Avalonia/Demo/Views/Workflow/MinimapOverlay.cs` 与 `Examples/Workflow/WPF/Demo/Views/Workflow/MinimapOverlay.cs`。
- 测试：`Src/Test/Unit/Core/VeloxDev.Core.Test/WorkflowSystem/MinimapPipelineTests.cs`、`MinimapDrawContextTests.cs`；`Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/MinimapHeadlessTests.cs`。
