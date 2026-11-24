# WPF 适配器

`VeloxDev.WPF` 用一组 WPF 附着行为闭合 Core 的工作流表面：命名部件表面、池化视图宿主、节点拖拽、插槽连接、插槽布局、小地图，以及既有的过渡与主题桥。本 QuickStart 在一个 `net8.0-windows` WPF 应用里搭出可用的编辑器表面。

参考实现是 `Examples/Workflow/WPF Trimmed/Demo/Views/Workflow/` —— `TreeView.xaml`（表面与两个模板）、`NodeView.xaml`、`SlotView.xaml`、`LinkView.xaml`，以及旁边的 ViewModel。「Trimmed」指**最小 demo**，不是发布设置。

## 页面

- [前置条件](00_前置条件/index.md) —— 包、目标框架与 SDK。
- [表面搭建](01_表面搭建/index.md) —— 工程、生成的 ViewModel、命名部件与池化节点模板。
- [交互与连线](02_交互与连线/index.md) —— 插槽连接、连线渲染、输入路由、滚轮/按键与小地图。
- [验证与完整代码](03_验证与完整代码/index.md) —— 可运行的文件集与运行声明。
