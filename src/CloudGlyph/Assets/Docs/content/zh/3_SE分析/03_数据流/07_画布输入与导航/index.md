# 画布输入与导航

`WorkflowInput` 把指针与键盘事件路由到树的组件。适配器把平台输入翻译成标准参数并调用 `Route`；由 Core 决定谁听到，由宿主决定做什么。导航与命中测试是建立在同一份模型数据上的另两个操作。

- [输入路由](00_输入路由/index.md) — `WorkflowInput.Route`、冒泡、`WorkflowEventHandle` 与适配器边界。
- [表面导航](01_表面导航/index.md) — `Locate`、滚动器算术、插槽与连线命中测试。

```csharp
var input = WorkflowInput.For(tree);
input.Route(new PointerMovedEventArgs(anchor, modifiers, source, target, handle));
```

命名空间：`VeloxDev.WorkflowSystem`。
