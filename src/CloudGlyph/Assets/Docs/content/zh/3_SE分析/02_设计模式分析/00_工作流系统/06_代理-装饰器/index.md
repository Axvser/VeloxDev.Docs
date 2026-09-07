# Workflow System — 设计模式 — 代理 / 装饰器

`[WorkflowBuilder.Node<THelper>]` 等属性把用户的 `partial class` 当作被装饰的表面：类声明 `[VeloxCommand]`/`[VeloxProperty]`/`[SlotSelectors]` 成员，源生成器把它们变成 `IVeloxCommand`/通知表面，而 Helper——一个由 VM 拥有的独立对象——实现真正的行为。`NodeDefaultViewModel`（框架默认节点）把转发关系具体化：其 `Receive` 命令方法把参数归一为 `ITaskContext` 并转发给 `Helper.ReceiveAsync`，链式返回其结果：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/ViewModels/NodeDefaultViewModel.cs`，第 115-120 行

```csharp
[VeloxCommand]
private async Task<object?> Receive(object? parameter, CancellationToken ct)
{
    var ctx = parameter as ITaskContext ?? new TaskContext(parameter);
    return await Helper.ReceiveAsync(ctx, ct);
}
```

编译运行完全不经过这个命令代理——引擎直接用 `IRuntimeContext` 会话调用 `GetHelper().ReceiveAsync`。代理层仍是单节点任务（`ReceiveCommand.Execute(ctx)`）与无状态广播派发的契约。演示侧，`EnumSelectorNodeViewModel` 上的生成成员（`OutputSlots`、`InputSlot`、`SelectedValue`、`CompileMode` 等）均由 `[VeloxProperty]`/`[SlotSelectors(typeof(VoltageRange))]` 从 partial 声明编译而来。
