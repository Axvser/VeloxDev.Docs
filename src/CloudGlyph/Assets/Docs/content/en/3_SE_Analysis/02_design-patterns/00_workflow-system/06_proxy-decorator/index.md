# Workflow System — Design Patterns — Proxy / Decorator

`[WorkflowBuilder.Node<THelper>]` and friends make the user's `partial class` the decorated surface: the class declares `[VeloxCommand]`/`[VeloxProperty]` members and the source generator turns them into the `IVeloxCommand`/notification surface, while the Helper — a separate object owned by the VM — implements the actual behavior. `NodeDefaultViewModel` (the framework default node) shows the forwarding concretely: its `Receive` command method normalizes the parameter to an `ITaskContext` and forwards to `Helper.ReceiveAsync`, chaining the return value:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/ViewModels/NodeDefaultViewModel.cs`, lines 115-120

```csharp
[VeloxCommand]
private async Task<object?> Receive(object? parameter, CancellationToken ct)
{
    var ctx = parameter as ITaskContext ?? new TaskContext(parameter);
    return await Helper.ReceiveAsync(ctx, ct);
}
```

In a compiled run the engine does not go through this command proxy at all — it calls `GetHelper().ReceiveAsync` directly with the `IRuntimeContext` session. The proxy layer remains the contract for single-node tasks (`ReceiveCommand.Execute(ctx)`) and stateless broadcast dispatch.

On the demo side, generated members are visible on `EnumSelectorNodeViewModel` (`OutputSlots`, `InputSlot`, `SelectedValue`, `CompileMode`, ...), each compiled by `[VeloxProperty]`/`[SlotSelectors(typeof(VoltageRange))]` from the partial declarations.
