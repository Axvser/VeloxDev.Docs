# Workflow System — 设计模式 — 代理 / 装饰器

`[WorkflowBuilder.Node<THelper>]` 等把用户的 `partial` 类作为被装饰的表面；生成器产生属性/命令成员，而 Helper（通过 `SetHelper` 注入的独立对象）拥有行为。`NodeDefaultViewModel` 具体展示了该模式：生成的 `ReceiveCommand` 把参数包装成 `TaskContext` 并转发给 `Helper.ReceiveAsync`：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/ViewModels/NodeDefaultViewModel.cs`，第 67-72 行

```csharp
[VeloxCommand]
private async Task<object?> Receive(object? parameter, CancellationToken ct)
{
    var ctx = parameter as ITaskContext ?? new TaskContext(parameter);
    return await Helper.ReceiveAsync(ctx, ct);
}
```
