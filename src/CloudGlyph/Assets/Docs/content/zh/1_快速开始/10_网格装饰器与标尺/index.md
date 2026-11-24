# 网格装饰器与标尺

网格装饰器是画布周围绘制画布网格与浮动标尺的表面层。它不属于滚动内容：它包住滚动容器，读到表面推给它的滚动与内容偏移，并画出在内容平移时仍然对齐的线。

## 这个功能覆盖什么

- **一份很小的数据契约。** `IWorkflowGridDecorator` 有两个滚动偏移、两个内容偏移与一个 `RulerBand` 厚度。表面行为在每次渲染前写入偏移；装饰器在 `OnRender` 里读。
- **画布网格。** `WorkflowSurfaceMath` 提供装饰器需要的四个公式：可见左/上边界、第一条对齐线、以及两轴各自的画布到内容换算。
- **浮动标尺。** 顶部与左侧带画在内容之上，并且不参与命中测试；画布按带厚平移，让原点落在带的内边缘。
- **虚拟化与小地图尊重这条带。** `RulerBand` 被推给 `SetVirtualizeInset`，标尺下的节点不会被提前剔除；它同时成为小地图的 `AvailableTop`。

## 各部分在哪里

| 层 | 类型 | 职责 |
|---|---|---|
| Core | `IWorkflowGridDecorator` | 偏移与 `RulerBand` 契约。 |
| Core | `WorkflowSurfaceMath.GridCanvasLeft` / `GridCanvasTop` / `GridFirstLine` / `GridX` / `GridY` | 全部网格算术，只写一次。 |
| Core | `SurfaceMetricsPush.PushGrid`、`SetVirtualizeInset` | 推入偏移与标尺 inset。 |
| WPF | `WorkflowSurfaceBehavior` | 解析 `GridDecoratorName`，每次滚动、平移、缩放都推一次。 |
| 模板 / 示例 | `WorkflowGridDecorator` | 绘制类：条目模板 `wpf-v-decorator`、`ava-v-decorator`……以及示例里的本地类。 |

适配器不自带网格装饰器类型。你用条目模板生成一个，或自己写这个类；平台相关的只有绘制 API。

## 页面

- [前置条件](00_前置条件/index.md) —— 目标、包、装饰器条目模板。
- [契约与放置](01_契约与放置/index.md) —— 接口、装饰器放在哪、表面推什么。
- [绘制网格与标尺](02_绘制网格与标尺/index.md) —— 四个公式、分层、标签与失效。
- [验证](03_验证/index.md) —— 运行、平移缩放、完整代码与运行声明。

## 为什么标尺带不是装饰

`RulerBand` 每趟会被读两次。网格用它偏移画布；虚拟化用它放大可见查询；小地图用它作为可用角落的顶部。画了带却报告 `0`，标尺下的节点会提前一个带厚消失，小地图也会压到标尺上。

## 证据

- 示例：`Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/WorkflowGridDecorator.cs`；完整示例是同一类形状，换工作台配色。
- 模板：`Src/Templates/VeloxDev.WPF.Templates/working/content/workflow-grid-decorator/TemplateClass.cs`（短名 `wpf-v-decorator`），其余六包同构。
- 测试：`Src/Test/Headless/VeloxDev.Razor.Headless.Tests/Tests/GridDecoratorTests.cs`；`Src/Test/Headless/VeloxDev.WPF.Headless.Tests/Tests/WorkflowSurfaceHeadlessTests.cs`（`Scroll_PushesOffsetsToTheGridDecorator`）；`Src/Test/Unit/Core/VeloxDev.Core.Test/WorkflowSystem/SurfacePipelineTests.cs`（`SurfaceMetricsPush_PushGrid_WritesOffsets`）。
