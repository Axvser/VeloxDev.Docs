# 平台适配器契约

契约位于 `VeloxDev.Core`，命名空间 `VeloxDev.WorkflowSystem`。它是每个 GUI 适配器都要闭合的那一层表面：一条输入路由、一对滚动/导航能力、度量与覆盖层的数据交换、视图池组合，以及模型事件接收器。这些类型都不提及具体平台；平台那一半由适配器提供。

| 角色 | 契约类型 | 由谁实现 |
| --- | --- | --- |
| 输入路由 | `WorkflowInput`、`IInputEvents`、`InputRelay` | Core 拥有路由；适配器把原生输入翻译成标准参数 |
| 滚动与导航 | `IWorkflowSurfaceScroller`、`IWorkflowSurfaceNavigator` | 适配器在表面挂载期间向 `WorkflowInput` 注册 |
| 表面度量 | `SurfaceMetrics`、`SurfaceViewport`、`SurfaceCanvas`、`SurfaceViewportRestoreCore` | Core 计算；适配器读取自己的滚动容器 |
| 网格与小地图 | `IWorkflowGridDecorator`、`IWorkflowMinimapOverlay` | Core 声明；宿主或适配器实现 |
| 视图池 | `ViewPool`、`ViewPoolCore`、`ViewSourcePipelineCore`、`IViewPoolPolicy` | Core 拥有池；各适配器闭合泛型组合 |
| 模型事件 | `INodeEventSink`、`ISlotEventSink`、`ITreeEventSink` | Core 声明；适配器通过标记挂载接收器 |
| 一致性 | `VeloxDev.AdapterTestKit.TestGraph` | 每个无头套件驱动的共享夹具 |

## 页面

- [输入路由](00_输入路由/index.md) —— 每棵树一条路由、每组件一个中继，以及事件句柄。
- [事件参数](01_事件参数/index.md) —— 适配器构造的指针与键盘参数类型。
- [输入枚举](02_输入枚举/index.md) —— `InputKey`、`InputModifiers` 与 `MouseButton`。
- [滚动与导航](03_滚动与导航/index.md) —— 两项能力、平台宿主契约与 `SurfaceScrollerCore`。
- [表面度量](04_表面度量/index.md) —— 不可变快照与推送辅助方法。
- [视口恢复](05_视口恢复/index.md) —— 保存/恢复状态机与它驱动的宿主。
- [表面数学](06_表面数学/index.md) —— 各适配器共享的坐标换算。
- [覆盖层契约](07_覆盖层契约/index.md) —— `IWorkflowGridDecorator` 与 `IWorkflowMinimapOverlay`。
- [视图池](08_视图池/index.md) —— 池引擎、策略与可序列化的调优配置。
- [视图托管层](09_视图托管层/index.md) —— 池组合的九个小契约。
- [事件接收器](10_事件接收器/index.md) —— 路由输入之外的模型事件方向。
- [一致性测试包](11_一致性测试包/index.md) —— 共享的 `TestGraph` 夹具。

一次最小契约调用不需要 GUI：

```csharp
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
tree.SetHelper(new TreeHelper(200d));

var input = WorkflowInput.For(tree);      // 每棵树一个实例
input.Scroller?.ScrollBy(0d, -120d);      // 在适配器注册之前为 null
```

**预期结果：** 每次调用 `WorkflowInput.For(tree)` 都返回同一个对象；在表面挂载之前 `Scroller` 为 `null`。
