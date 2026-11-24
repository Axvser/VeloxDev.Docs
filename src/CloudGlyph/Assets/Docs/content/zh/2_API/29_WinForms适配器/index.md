# WinForms 适配器

`VeloxDev.WinForms` 用 Easel 闭合共享的平台契约：一个 `VisualHost`、`PART_Canvas` 上的一台相机、一个与工作流无关的视图池，以及负责槽测量、节点拖动与插槽连线的附着行为。本节按类型组枚举这套公开接口。

所有工作流类型都在 `VeloxDev.WinForms` 程序集的 `VeloxDev.WorkflowSystem.*` 命名空间下。过渡类型在 Easel 视觉之上重新实现共享过渡引擎；主题类型转换 `System.Drawing` 值。

## 类型组

1. [表面与视图池](00_表面与视图池/index.md) —— `WorkflowSurfaceBehavior`、`ViewPool`、`ViewPoolChangedEventArgs`、`WorkflowEvents`。
2. [手势行为](01_手势行为/index.md) —— `WorkflowNodeDragBehavior`、`WorkflowSlotConnectionBehavior`、`WorkflowSlotLayoutBehavior`。
3. [覆盖层](02_覆盖层/index.md) —— `WorkflowMinimapOverlay`、`WorkflowInfoOverlay`、`IWorkflowMinimapScrollSource`。
4. [视图宿主](03_视图宿主/index.md) —— 为 Easel 闭合的 Core 视图池与小地图层。
5. [过渡与动画](04_过渡与动画/index.md) —— `Interpolator`、`Transition<T>`、采样器集合与 `EaselAnimationBootstrap`。
6. [主题转换器](05_主题转换器/index.md) —— 面向 `System.Drawing` 与 WinForms 值类型的 `IThemeValueConverter` 实现。

表面在模板上解析的名称在七家适配器中保持一致：`PART_Canvas`、`PART_ScrollViewer`、`PART_GridDecorator`、`PART_SurfaceBorder`、`PART_MinimapOverlay`、`PART_InfoOverlay` 以及 `WorkflowTemplateSelector` 资源键。
