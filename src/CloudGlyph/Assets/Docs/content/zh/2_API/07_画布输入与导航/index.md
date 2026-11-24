# 画布输入与导航

Core 把原生指针与按键输入变成一套可路由、可否决的词汇，并暴露挂载表面可以注册的滚动与导航能力。本节列出这套公开表面，以及共享的命中测试几何与四个把平台输入翻译进路由的 WPF 附着行为。

除页面另行说明外，所有类型都在 `VeloxDev.WorkflowSystem`。`WorkflowNavigationEx` 在 `VeloxDev.WorkflowSystem.StandardEx`；适配器行为在 `VeloxDev.WorkflowSystem.AttachedBehaviors`。

## 页面

- [输入路由](00_输入路由/index.md) —— `WorkflowInput`、`InputRelay`、`WorkflowEventHandle`、指针与按键事件参数，以及三个输入枚举。
- [表面导航](01_表面导航/index.md) —— scroller 与 navigator 契约、`SurfaceScrollerCore`、滚轮配置与 `Locate()`。
- [命中测试与几何](02_命中测试与几何/index.md) —— `LinkCurve`、`ILinkHitTestable`、`LinkHitTestEx` 与 `SlotHitTestEx`。
- [表面数学](03_表面数学/index.md) —— `WorkflowSurfaceMath`、`WorkflowBounds`、`SurfaceMetrics`、`SurfaceAvailableArea` 与指标推送助手。
- [视口状态](04_视口状态/index.md) —— `SurfaceViewport`、`SurfaceViewportFeed` 与 `SurfaceViewportRestoreCore`。
- [适配器行为](05_适配器行为/index.md) —— WPF 的表面、变换、节点拖动与插槽连线附着属性。

## 分层

| 层 | 类型 | 职责 |
|---|---|---|
| Core | `WorkflowInput`、`IInputEvents`、`InputRelay`、事件参数、枚举、`WorkflowEventHandle` | 路由、共享句柄、平台中立的参数形状。 |
| Core | `IWorkflowSurfaceScroller`、`IWorkflowSurfaceNavigator`、`SurfaceScrollerCore`、`SurfaceWheelProfile` | 滚轮转滚动、画布点居中的算术。 |
| Core | `LinkCurve`、`LinkHitTestEx`、`SlotHitTestEx`、`WorkflowSurfaceMath` | 所有适配器共享的几何。 |
| 适配器（以 WPF 为例） | `WorkflowSurfaceBehavior`、`WorkflowCanvasTransformBehavior`、`WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior` | 命名部件解析、原生手势翻译、逐视图拖动与连线。 |

## 相关

- [画布输入与导航快速开始](../../1_快速开始/07_画布输入与导航/index.md) 在可运行宿主里展示同一批类型。
- [平台适配器契约](../../1_快速开始/24_平台适配器契约/index.md) 说明每家适配器都会解析的命名部件。
