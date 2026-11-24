# MAUI 适配器

`VeloxDev.MAUI` 为 .NET MAUI 闭合工作流表面。宿主是 `ContentView`，树通过 `BindingContext` 到达；连线由一个视口尺寸的 `WorkflowLinkOverlay` 统一绘制，而不是每条线一个池化视图。适配器没有 `WorkflowCanvasTransformBehavior`；几何由表面与视图排列器共同拥有。

参考实现是 `Examples/Workflow/MAUI Trimmed/Demo/Controls/Workflow/` —— 注意是 `Controls/`，不是 `Views/`。「Trimmed」指**最小 demo**，不是发布设置。

MAUI 有 demo，但**没有无头一致性套件**；`Src/Test/Headless/README.md` 记录它没有窗口无关的宿主。

## 页面

- [前置条件](00_前置条件/index.md) —— 目标框架、MAUI 工作负载与包版本。
- [表面搭建](01_表面搭建/index.md) —— 工程、生成的 ViewModel、ContentView 宿主与节点模板。
- [交互与连线](02_交互与连线/index.md) —— 节点拖拽、连接、共享连线层、手势与菜单。
- [验证与完整代码](03_验证与完整代码/index.md) —— 运行检查与完整文件集。
