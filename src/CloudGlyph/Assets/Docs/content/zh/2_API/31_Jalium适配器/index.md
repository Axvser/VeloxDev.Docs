# Jalium 适配器

`VeloxDev.Jalium` 与 WPF 适配器一样是标记驱动的，但没有可派生的工作流控件。表面是树模板，根上挂 `WorkflowSurfaceBehavior` 的附着属性；节点、插槽、连线、网格、小地图与选择器是分开的视图角色。适配器基于 `Jalium.UI.Controls`，目标为平台中立的 `net10.0`。

两条 Jalium 特有契约塑造了表面：

- 绑定引擎读不到带前缀的附着属性，所以树类把 `WorkflowSurfaceBehavior.CanvasTransform` 以普通 `CanvasTransform` 属性再暴露一次；节点与连线模板绑它。
- 渲染器按布局盒判断是否绘制子元素，所以连线视图调用 `WorkflowLinkBounds.Apply` 把自己的盒子挪到曲线上。画到盒外的连线会被静默丢弃。

所有工作流类型都在 `VeloxDev.WorkflowSystem.AttachedBehaviors` 与 `VeloxDev.WorkflowSystem.ViewHosting` 下。

## 类型组

1. [表面与视图池](00_表面与视图池/index.md) —— `WorkflowSurfaceBehavior`、`ViewPool`。
2. [手势与连线边界](01_手势与连线边界/index.md) —— 节点拖动、插槽连线、槽布局与 `WorkflowLinkBounds`。
3. [事件与小地图](02_事件与小地图/index.md) —— `WorkflowEvents`、`WorkflowMinimapOverlay`。
4. [视图宿主](03_视图宿主/index.md) —— 为 Jalium 闭合的 Core 视图池与小地图。
5. [过渡系统](04_过渡系统/index.md) —— `Interpolator`、`Transition<T>` 与 Jalium 采样器集合。

本适配器不提供 `VeloxDev.DynamicTheme` 转换器集合；该平台的主题值不经过这个命名空间转换。
