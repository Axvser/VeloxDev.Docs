# 网格装饰器与标尺

网格装饰器是表面与内容之间的一层：它在滚动视图下方画画布网格，在上方画浮动标尺，并按表面推送的偏移对齐。Core 定义数据契约与全部算术；绘制类从条目模板生成，或手写。

Core 类型都在 `VeloxDev.WorkflowSystem`。Razor 装饰器在 `VeloxDev.WorkflowSystem.AttachedBehaviors`；XAML 装饰器由条目模板包生成。

## 页面

- [装饰器契约](00_装饰器契约/index.md) —— `IWorkflowGridDecorator`、它收到的表面指标，以及网格推送。
- [网格数学](01_网格数学/index.md) —— 让线与标尺保持对齐的五个 `WorkflowSurfaceMath` 函数。
- [适配器装饰器](02_适配器装饰器/index.md) —— Razor 组件、XAML 条目模板契约，以及 `GridDecoratorName` 附着属性。

## 分层

| 层 | 类型 | 职责 |
|---|---|---|
| Core | `IWorkflowGridDecorator` | 偏移与 `RulerBand` 契约。 |
| Core | `WorkflowSurfaceMath.GridCanvasLeft` / `GridCanvasTop` / `GridFirstLine` / `GridX` / `GridY` | 全部网格算术。 |
| Core | `SurfaceMetricsPush.PushGrid` | 写入偏移并应用标尺 inset。 |
| Core | `WorkflowSpatialEx.SetVirtualizeInset` | 避免标尺下的节点被提前剔除。 |
| 适配器 / 模板 | `WorkflowGridDecorator`（Razor）、生成的 XAML 装饰器 | 绘制类。 |

## 相关

- [网格装饰器与标尺快速开始](../../1_快速开始/10_网格装饰器与标尺/index.md) 构建装饰器并把它装在滚动视图外层。
- [画布输入与导航](../07_画布输入与导航/index.md) 定义表面指标与命名部件。
- [视图托管与虚拟化](../08_视图托管与虚拟化/index.md) 消费标尺 inset。
