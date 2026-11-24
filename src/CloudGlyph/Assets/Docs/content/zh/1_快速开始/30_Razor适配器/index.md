# Razor 适配器

`VeloxDev.Razor` 把工作流表面当成一棵 Blazor 组件树。这里没有画布控件，也没有附着属性：`WorkflowSurfaceBehavior` 是一个组件，它的 `[Parameter]` 取代桌面适配器的附着属性；一个小型 JS 模块（`wwwroot/veloxdev.workflow.js`，随包发布）负责滚轮手势、元素测量与缩放那一帧的曲线刷新。

本快速开始搭建一个 Interactive Server 页面，渲染两个节点、它们的端口和一条连线。

## 最终会得到什么

- 一个目标为 `net8.0` 的 Blazor Web App 工程 —— 被验证过的 demo 是 `net10.0`。
- 由 `VeloxDev.Razor.Templates` 生成的七个视图角色，每个都是 `.razor` + `.razor.cs` 一对。
- 一棵含两个节点、一个受通道约束的输入端口和一条可见连线的树。
- 在浏览器里核对平移、滚轮滚动、Ctrl+滚轮缩放、节点拖动与插槽连线。

## 按顺序阅读

1. [前置条件与安装](00_前置条件/index.md) —— 目标框架、包、静态 Web 资源与服务端渲染模式。
2. [表面与宿主](01_表面与宿主/index.md) —— ViewModel、七个组件、`Home` 页面与示例图。
3. [验证与完整代码](02_验证/index.md) —— 运行、预期行为、完整页面、运行声明。

七个角色来自 Razor 条目模板包；[工作流条目模板](../32_工作流条目模板/index.md) 列出全部短名。
