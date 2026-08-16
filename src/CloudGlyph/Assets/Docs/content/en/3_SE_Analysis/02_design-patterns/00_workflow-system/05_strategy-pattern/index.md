# Workflow System — Design Patterns — Strategy Pattern

A `SlotEnumerator<TSlot>` swaps its output-slot strategy via `SetSelector(type)`. `BoolSelectorNodeViewModel` and `EnumSelectorNodeViewModel` implement `ICompileTimeRouter`, letting the compiler pre-collect the routing table (`GetRouteTable`) while `ResolveRouteKey` decides which branch to take — static mode locks the key at compile time and prunes unchosen branches; dynamic mode re-resolves at runtime:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/BoolSelectorNodeViewModel.cs`, lines 94-120

```csharp
public Task<object?> ResolveRouteKey(object? payload)
{
    if (CompileMode == RouterCompileMode.Dynamic && payload is null)
        return Task.FromResult<object?>(null);

    if (payload is RuntimeContext ctx && ctx.TryGet("selector.bool", out var v) && v is string s)
        return Task.FromResult<object?>(bool.TryParse(s, out var b) ? b : Condition);

    return Task.FromResult<object?>(Condition);
}

public Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()
{
    var dict = new Dictionary<object, List<IWorkflowNodeViewModel>>();
    if (CompileMode == RouterCompileMode.Static)
    {
        AddBranch(dict, Condition, Condition ? TrueSlot : FalseSlot);
    }
    else
    {
        AddBranch(dict, true, TrueSlot);
        AddBranch(dict, false, FalseSlot);
    }
    return Task.FromResult<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>>(
        dict.ToDictionary(kv => kv.Key, kv => (IReadOnlyList<IWorkflowNodeViewModel>)kv.Value.AsReadOnly()));
}
```
