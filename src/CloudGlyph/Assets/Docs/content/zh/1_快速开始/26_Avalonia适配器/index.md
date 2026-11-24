# Avalonia 适配器

`VeloxDev.Avalonia` 用 `AvaloniaProperty` 注册、用 `FindControl` 解析，闭合与 WPF 适配器相同的七个工作流角色。demo 默认开启编译绑定，所以模板都带具体的 `x:DataType`。

参考实现是 `Examples/Workflow/Avalonia Trimmed/Demo/Demo/Views/Workflow/` —— 工程位于 `Demo/Demo/`，所以视图比 WPF demo 深一层。「Trimmed」指**最小 demo**，不是发布设置。

## 页面

- [前置条件](00_前置条件/index.md) —— 包、目标框架与 Avalonia 版本。
- [表面搭建](01_表面搭建/index.md) —— 工程、生成的 ViewModel、表面与池化节点模板。
- [交互与连线](02_交互与连线/index.md) —— 连接、连线渲染、路由输入与小地图。
- [验证与完整代码](03_验证与完整代码/index.md) —— 可运行的文件集与运行声明。
