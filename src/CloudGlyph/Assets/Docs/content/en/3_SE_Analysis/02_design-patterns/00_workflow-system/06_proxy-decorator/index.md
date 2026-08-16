# Workflow System — Design Patterns — Proxy / Decorator

`[WorkflowBuilder.Node<THelper>]` etc. make the user's `partial` class the decorated surface; the generator emits property/command members while the Helper (a separate object injected via `SetHelper`) owns behavior. `NodeDefaultViewModel` shows the pattern concretely: the generated `ReceiveCommand` wraps the parameter into `TaskContext` and forwards to `Helper.ReceiveAsync`:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/ViewModels/NodeDefaultViewModel.cs`, lines 67-72

```csharp
[VeloxCommand]
private async Task<object?> Receive(object? parameter, CancellationToken ct)
{
    var ctx = parameter as ITaskContext ?? new TaskContext(parameter);
    return await Helper.ReceiveAsync(ctx, ct);
}
```
