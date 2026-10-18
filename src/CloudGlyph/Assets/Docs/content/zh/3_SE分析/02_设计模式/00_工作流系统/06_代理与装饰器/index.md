# 工作流系统 — 设计模式 — 代理 / 装饰器

`[WorkflowBuilder.Node<THelper>]` 等特性把用户的 `partial class` 变成被装饰的表面：类里声明 `[VeloxCommand]`/`[VeloxProperty]` 成员，源生成器把它们变成 `IVeloxCommand`/通知表面；而 Helper —— 由 VM 拥有的独立对象 —— 实现真正行为。`NodeDefaultViewModel`（框架默认节点）具体展示了转发：它的 `Receive` 命令方法把参数归一化为 `ITaskContext`，转发给 `Helper.ReceiveAsync`，并链回返回值：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/ViewModels/NodeDefaultViewModel.cs`，115-120 行

```csharp
[VeloxCommand]
private async Task<object?> Receive(object? parameter, CancellationToken ct)
{
    var ctx = parameter as ITaskContext ?? new TaskContext(parameter);
    return await Helper.ReceiveAsync(ctx, ct);
}
```

编译运行时引擎完全不经过这个命令代理 —— 它带着 `IRuntimeContext` 会话直接调用 `GetHelper().ReceiveAsync`。代理层仍是单节点任务（`ReceiveCommand.Execute(ctx)`）与 stateless 广播派发的契约。

demo 一侧，生成成员在 `EnumSelectorNodeViewModel` 上可见（`OutputSlots`、`InputSlot`、`SelectedValue`、`CompileMode` 等），各自由 `[VeloxProperty]`/`[SlotSelectors(typeof(VoltageRange))]` 从 partial 声明编译而来。
