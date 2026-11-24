# WinUI 适配器

`VeloxDev.WinUI` 为 WinUI 3 / Windows App SDK 实现同一组七个工作流角色。它的平台形态与桌面 XAML 适配器有两处重要差别：画布平移是合成变换，连线视图使用**偏移帧**，让几何永远不离开元素自己的盒子。

参考实现是 `Examples/Workflow/WinUI Trimmed/Demo/Views/Workflow/` —— `TreeView.xaml` 与 `LinkView.xaml.cs` 要放在一起读，因为它们正是实现偏移帧的那一对。「Trimmed」指**最小 demo**，不是发布设置。

WinUI 有 demo，但**没有无头一致性套件**；`Src/Test/Headless/README.md` 记录它没有窗口无关的宿主。

## 页面

- [前置条件](00_前置条件/index.md) —— 目标框架、Windows App SDK 与 SDK。
- [表面搭建](01_表面搭建/index.md) —— 工程、生成的 ViewModel、命名部件与节点模板。
- [交互与连线](02_交互与连线/index.md) —— 连接、偏移帧连线、路由输入与菜单。
- [验证与完整代码](03_验证与完整代码/index.md) —— 运行检查与完整文件集。
