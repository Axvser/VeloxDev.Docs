# 视图托管与虚拟化

大工作流的节点数远超一个视口能有效显示的数量。VeloxDev 把问题拆成两半：**空间索引**决定给定视口下哪些组件可见，**视图池**把可见集变成一项一个 UI 视图，并在视口移动时回收视图。

## 这个功能覆盖什么

- **可见集，而不是整张图。** `TreeHelper(cellSize)` 打开虚拟化；`Helper.VisibleItems` 是一个 `ObservableCollection<IWorkflowComponent>`，包含虚拟连线、视口附近的节点，以及它们之间的连线。
- **一个可见项一个视图。** 适配器的 `ViewPool` 附着属性消费 `VisibleItems`，通过模板选择器创建视图，条目离开时按运行时类型回收。
- **五层契约。** 工厂、容器、摆位、调度、诊断是 Core 里彼此独立的接口，由 `ViewSourcePipelineCore` 组合；每家适配器用自己的属性系统闭合这些层。
- **可选策略。** `AdaptiveViewPoolPolicy` 根据实测吞吐调整批大小与帧预算；平台也可以换成固定策略。

## 各部分在哪里

| 层 | 类型 | 职责 |
|---|---|---|
| Core | `TreeHelper(double cellSize)`、`Viewport`、`VisibleItems`、`MarkDirty`、`WithSynchronizationContext` | 虚拟化开关与可见集 observable。 |
| Core | `WorkflowSpatialManager`、`SpatialGridHashMap<T>`、`WorkflowSpatialEx.Virtualize` / `EnableMap` / `SetVirtualizeInset` | 节点网格、连线的节点对网格、视口查询、标尺 inset。 |
| Core | `ViewPoolCore<...>`、`ViewPool<...>`、`ViewHostCore<...>`、`ViewSourcePipelineCore<...>`、`AdaptiveViewPoolPolicy`、`ViewPoolOptions` | 池、分批、回收与契约组合。 |
| WPF | `ViewPool.ItemsSource` / `ViewPool.TemplateSelector`、`ViewSourcePipeline`、`ViewFactory`、`ViewContainer`、`ViewScheduler` | 各层的 WPF 闭合。 |
| WPF | `WorkflowSurfaceBehavior` | 把视口推进树里，这正是触发虚拟化的东西。 |

## 页面

- [前置条件](00_前置条件/index.md) —— 目标、包与示例。
- [启用虚拟化](01_启用虚拟化/index.md) —— Helper、格子尺寸、可见集与它的线程规则。
- [托管视图](02_托管视图/index.md) —— 挂上池、写选择器、了解什么会被回收。
- [验证](03_验证/index.md) —— 运行、数可见项、完整代码与运行声明。

## 两半

```mermaid
flowchart LR
    Scroll["滚动 / 缩放"] --> Viewport["TreeHelper.Viewport"]
    Viewport --> Virtualize["WorkflowSpatialEx.Virtualize"]
    Virtualize --> Visible["Helper.VisibleItems"]
    Visible --> Pool["ViewPool.ItemsSource"]
    Pool --> View["一项一个视图"]
    View --> Recycle["移除时回池"]
```

左半边是 Core 几何，运行在安装 Helper 的那个线程上。右半边是适配器的池，必须运行在宿主 UI 线程；调度器是唯一的线程边界。

## 证据

- 示例：`Examples/Workflow/Avalonia Trimmed/Demo/Demo/ViewModels/Workflow/Helper/VirtualizeHelper.cs`、`TreeView.axaml`、`TreeView.axaml.cs`；WPF Trimmed 镜像同样是这个形状。
- 测试：`Src/Test/Unit/Core/VeloxDev.Core.Test/WorkflowSystem/ViewPoolTests.cs`、`AdaptiveViewPoolPolicyTests.cs`、`SpatialIndexFreshnessTests.cs`、`TreeHelperTickTests.cs`；`Src/Test/Headless/VeloxDev.Avalonia.Headless.Tests/Tests/ViewPoolHeadlessTests.cs`。
