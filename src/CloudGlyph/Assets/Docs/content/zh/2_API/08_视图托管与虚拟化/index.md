# 视图托管与虚拟化

虚拟化有两半。Core 在树 Helper 上维护空间索引与可见集；视图池把可见集变成一项一个 UI 视图，并在视口移动时回收视图。本节列出池、五层宿主契约、空间索引，以及这些层的 WPF 闭合。

除页面另行说明外，Core 类型都在 `VeloxDev.WorkflowSystem`。`WorkflowSpatialEx` 在 `VeloxDev.WorkflowSystem.StandardEx`；WPF 类型在 `VeloxDev.WorkflowSystem.ViewHosting` 与 `VeloxDev.WorkflowSystem.AttachedBehaviors`。

## 页面

- [视图池](00_视图池/index.md) —— `ViewPool`、`ViewPoolCore`、`ViewPoolOptions`、`AdaptiveViewPoolPolicy` 与 `IViewPoolPolicy`。
- [视图宿主契约](01_视图宿主契约/index.md) —— 九个层接口、`ViewStage`、`ViewHostCore` 与 `ViewSourcePipelineCore`。
- [空间虚拟化](02_空间虚拟化/index.md) —— `TreeHelper` 开关、`Viewport`、`SpatialGridHashMap<T>`、`WorkflowSpatialManager` 与 `WorkflowSpatialEx` 扩展。
- [适配器视图池](03_适配器视图池/index.md) —— WPF `ViewPool` 附着属性与闭合契约的层类。

## 分层

| 层 | 类型 | 职责 |
|---|---|---|
| Core | `TreeHelper(double)`、`VisibleItems`、`Viewport`、`MarkDirty`、`WithSynchronizationContext` | 虚拟化开关与可见集 observable。 |
| Core | `WorkflowSpatialManager`、`SpatialGridHashMap<T>`、`WorkflowSpatialEx` | 节点网格、节点对网格、视口查询、标尺 inset。 |
| Core | `ViewPool<...>`、`ViewPoolCore<...>`、`ViewHostCore<...>`、`ViewSourcePipelineCore<...>` | 分批、回收与契约组合。 |
| Core | `AdaptiveViewPoolPolicy`、`ViewPoolOptions`、`IViewPoolPolicy` | 分批与回收策略。 |
| 适配器（以 WPF 为例） | `ViewPool.ItemsSource`、`ViewPool.TemplateSelector`、`ViewSourcePipeline`、`ViewFactory`、`ViewContainer`、`ViewScheduler` | 各层的平台闭合。 |

## 相关

- [视图托管与虚拟化快速开始](../../1_快速开始/08_视图托管与虚拟化/index.md) 在可运行宿主里接上 Helper 与池。
- [小地图](../09_小地图/index.md) 消费同一份视口与可见集。
