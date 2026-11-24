# WinForms 适配器

`VeloxDev.WinForms` 把工作流表面画在一个 Easel `VisualHost` 里。单一相机矩阵缩放整张图；树是一个视觉 `UserControl`；`ViewPool` 为每个可见项物化一个视图。槽测量、节点拖动与插槽连线都是附着行为，不是逐控件的鼠标事件。

本快速开始搭建一个可运行的 WinForms 窗口，包含两个节点、它们的端口、一条连线和一个能用的相机。

## 最终会得到什么

- 一个 `net8.0-windows` 工程 —— 被验证过的 demo 配置是 `net10.0-windows`。
- 由 `VeloxDev.WinForms.Templates` 生成的七个视图角色。
- 一棵含两个节点、一个受通道约束的输入端口和一条可见连线的树。
- 在运行窗口中核对平移、滚轮滚动、Ctrl+滚轮缩放、节点拖动与插槽连线。

## 按顺序阅读

1. [前置条件与安装](00_前置条件/index.md) —— 支持目标、包、Easel XAML 生成器。
2. [表面与宿主](01_表面与宿主/index.md) —— ViewModel、七个视图、`VisualHost` 接线、示例图。
3. [验证与完整代码](02_验证/index.md) —— 运行、预期行为、完整宿主文件、运行声明。

这些视图本身由 WinForms 条目模板包产出；[工作流条目模板](../32_工作流条目模板/index.md) 说明该包与全部七个短名。
