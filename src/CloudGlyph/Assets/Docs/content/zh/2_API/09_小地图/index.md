# 小地图

小地图是同一棵树的第二份、小得多的读法：每个节点变成一个缩略块，一个矩形表示当前视口。Core 拥有管线、映射数学与三个平台接缝；每家适配器提供一个覆盖层与一个渲染器。

Core 类型都在 `VeloxDev.WorkflowSystem`。WPF 覆盖层在 `VeloxDev.WorkflowSystem.AttachedBehaviors`，其管线与平台类在 `VeloxDev.WorkflowSystem.ViewHosting`。

## 页面

- [小地图契约](00_小地图契约/index.md) —— 覆盖层、渲染器、视口宿主与输入宿主接口，以及 `MinimapMetrics` 与 `SurfaceAvailableArea`。
- [处理管线](01_处理管线/index.md) —— `MinimapHostCore`、`MinimapPipelineCore` 与 `MinimapDrawContext`。
- [小地图数学](02_小地图数学/index.md) —— `WorkflowSurfaceMath` 的适配、映射与拖动函数。
- [适配器覆盖层](03_适配器覆盖层/index.md) —— WPF `WorkflowMinimapOverlay` 与它的三个平台类。

## 分层

| 层 | 类型 | 职责 |
|---|---|---|
| Core | `IWorkflowMinimapOverlay` | 由表面行为推送的数据。 |
| Core | `IMinimapRenderer<TSurface>`、`IMinimapViewportHost`、`IMinimapInputHost` | 管线组合的三个平台接缝。 |
| Core | `MinimapPipelineCore<...>`、`MinimapHostCore<...>` | 树订阅、脏标记去抖、映射、放置、拖动。 |
| Core | `MinimapDrawContext`、`MinimapMetrics`、`SurfaceAvailableArea` | 一次绘制的几何与尺寸输入。 |
| Core | `WorkflowSurfaceMath`（小地图成员） | 适配、局部映射、视口矩形、拖动转换。 |
| 适配器（以 WPF 为例） | `WorkflowMinimapOverlay`、`MinimapPipeline`、`MinimapRenderer`、`MinimapViewportHost`、`MinimapInputHost` | 属性系统、绘制、滚动应用、指针捕获。 |

## 相关

- [小地图快速开始](../../1_快速开始/09_小地图/index.md) 把覆盖层挂到表面上。
- [视图托管与虚拟化](../08_视图托管与虚拟化/index.md) 提供小地图读取的视口与可见集。
- [画布输入与导航](../07_画布输入与导航/index.md) 定义覆盖层收到的表面指标。
