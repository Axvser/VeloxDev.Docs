# Razor 适配器

`VeloxDev.Razor` 把工作流表面表达成一棵 Blazor 组件树。这里没有附着属性：组件暴露 `[Parameter]`，一个静态 JavaScript 模块（`wwwroot/veloxdev.workflow.js`，随包发布）负责滚轮手势、元素测量与缩放那一帧的曲线刷新。

程序集的工作流类型在 `VeloxDev.WorkflowSystem.AttachedBehaviors` 下；过渡类型重新实现共享引擎；主题转换器面向 CSS 字符串。

## 类型组

1. [表面与视图池](00_表面与视图池/index.md) —— `WorkflowSurfaceBehavior`、`ViewPool`。
2. [输入组件](01_输入组件/index.md) —— 节点拖动、插槽连线、槽布局与 `SurfacePointerKind`。
3. [覆盖层与装饰器](02_覆盖层与装饰器/index.md) —— `WorkflowGridDecorator`、`WorkflowMinimapOverlay`。
4. [呈现辅助](03_呈现辅助/index.md) —— 画布变换、事件、几何作用域、呈现与运行时 id。
5. [脚本模块](04_脚本模块/index.md) —— 支撑互操作的导出，也可以由宿主手调。
6. [过渡与主题](05_过渡与主题/index.md) —— Razor 过渡类型与 `IThemeValueConverter` 实现。

生成时每个角色都是一个 `.razor` + `.razor.cs` 对；表面把这一对当作一个组件消费。
