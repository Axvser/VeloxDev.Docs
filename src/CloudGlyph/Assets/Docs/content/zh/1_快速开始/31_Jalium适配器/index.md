# Jalium 适配器

`VeloxDev.Jalium` 与 WPF 适配器一样是标记驱动的，但没有可派生的工作流控件。表面是树模板，根上挂 `WorkflowSurfaceBehavior` 的附着属性；节点、插槽、连线、网格、小地图与选择器是分开的视图角色。适配器是平台中立的（`net10.0`，基于 `Jalium.UI.Controls`），因此同一个包可服务 Windows、Linux 与 Android 宿主。

两条 Jalium 特有契约塑造了每个模板：

- 绑定引擎读不到带前缀的附着属性，所以树类把 `WorkflowSurfaceBehavior.CanvasTransform` 以普通 `CanvasTransform` 属性再暴露一次，节点/连线模板绑它对。
- 渲染器按布局盒判断是否绘制子元素，所以连线视图通过 `WorkflowLinkBounds.Apply` 把自己的盒子挪到曲线上。画到盒外的连线会被静默丢弃。

本快速开始搭建一个桌面窗口，包含两个节点、它们的端口和一条可见连线。

## 最终会得到什么

- 一个 `net10.0-windows` 桌面宿主 —— 适配器本身是平台中立的 `net10.0`。
- 由 `VeloxDev.Jalium.Templates` 生成的七个视图角色（四对 `.jalxaml` + 三个 `.cs`）。
- 一棵含两个节点、一个受通道约束的输入端口和一条可见连线的树。
- 在运行窗口中核对平移、Ctrl+滚轮缩放、节点拖动与插槽连线。

## 按顺序阅读

1. [前置条件与安装](00_前置条件/index.md) —— `net10.0` 底线、`Jalium.UI.Controls` 26.10.8 与桌面宿主包。
2. [表面与宿主](01_表面与宿主/index.md) —— ViewModel、七个角色、`CanvasTransform` 镜像、模型宿主。
3. [验证与完整代码](02_验证/index.md) —— 运行、预期行为、完整宿主文件、运行声明。

七个角色来自 Jalium 条目模板包；[工作流条目模板](../32_工作流条目模板/index.md) 列出全部短名。
