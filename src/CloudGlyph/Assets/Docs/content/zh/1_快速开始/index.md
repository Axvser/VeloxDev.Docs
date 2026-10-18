# 快速开始

每个 VeloxDev 功能都有一条从空项目到可运行程序的路径：前置条件、安装、最小配置、核心用法、验证。每一步都给出可观察的**预期结果**，QuickStart 末尾保留诚实的**运行声明**。

| 模块 | 你会构建什么 |
|---|---|
| [工作流系统](00_工作流系统/index.md) | 画布上的节点图：Tree / Node / Slot / Link、撤销重做、编译与运行 |
| [工作流代理](01_工作流代理/index.md) | 通过 60+ 工具与 MCP 在运行时编辑工作流的 AI |
| [MVVM](02_MVVM/index.md) | 源生成器驱动的可观察属性与异步命令 |
| [过渡动画](03_过渡动画/index.md) | Fluent 属性插值与缓动 |
| [动态主题](04_动态主题/index.md) | 带过渡动画的运行时主题切换 |
| [AOP](05_AOP/index.md) | 编译期切面代理 |
| [Tickable](06_Tickable/index.md) | 帧驱动的生命周期循环 |
| [弱引用类型](07_弱引用类型/index.md) | 弱集合与弱委托 |
| [平台适配器](08_平台适配器/index.md) | GUI 适配器与 `dotnet new` 视图模板 |
| [序列化](09_序列化/index.md) | 标注类型、写入 JSON、重建对象图 |

## 通用前置条件

- **.NET SDK**：以各模块前置条件页为准。`VeloxDev.Core` 多目标 `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`；`VeloxDev.Core.Extension` 为 `netstandard2.0;net8.0`。仓库内的示例项目使用更新的目标框架（常见为 `net9.0`，Jalium 为 `net10.0`），它们只是**已测试配置**，不是库的最低要求。
- **GUI 工作负载**：选择哪个适配器，就安装对应工作负载（WPF / Avalonia / WinUI / MAUI / WinForms / Razor / Jalium）。
- **NuGet 访问**：用于还原 `VeloxDev.*` 包。
- 具体版本、包名和 TFM 以各模块 `00_前置条件` 页为准；不要用示例项目的运行时反推最低版本。
