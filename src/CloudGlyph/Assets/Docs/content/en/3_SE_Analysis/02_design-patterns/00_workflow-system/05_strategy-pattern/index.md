# Workflow System — Design Patterns — Strategy Pattern

A selector node implements `ICompileTimeRouter` and plugs two strategies into the compiler: `GetRouteTable()` declares the branch structure, while `ResolveRouteKey(payload)` picks the branch for the current payload. `RouterCompileMode` selects the strategy variant — `Static` locks the currently selected branch at compile time (the compiler prunes every other branch and marks their downstream as Order = -1 absolute stop); `Dynamic` keeps all branches alive and re-resolves the key at runtime (compile-time payload is null, so `ResolveRouteKey(null)` returns null → `IsDynamic`).

The demo `EnumSelectorNodeViewModel` (a `SlotEnumerator<SlotViewModel>` over the `VoltageRange` enum) shows the mode-dependent `GetRouteTable`:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`, lines 198-243

```csharp
public Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()
{
    var dict = new Dictionary<object, List<IWorkflowNodeViewModel>>();
    if (OutputSlots is null)
        return Task.FromResult(EmptyRouteTable());

    if (CompileMode == RouterCompileMode.Static)
    {
        // Static: return only the currently selected branch (register as terminal branch if it has no downstream)
        var key = OutputSlots.NormalizeSelectorValue(OutputSlots.CurrentValue);
        var slot = key is not null && OutputSlots.TrySelect(key, out var s) ? s : null;
        if (slot is not null)
        {
            if (slot.Targets.Count == 0)
            {
                if (key is not null && !dict.ContainsKey(key)) dict[key] = [];
            }
            else
            {
                foreach (var target in slot.Targets)
                    if (target.Parent is not null)
                        AddTarget(dict, key!, target.Parent);
            }
        }
    }
    else
    {
        // Dynamic: all branches (terminal branches without downstream are registered as empty lists)
        foreach (var item in OutputSlots.Items)
        {
            var slot = item.Slot;
            if (item.Value is null || slot is null) continue;
            if (slot.Targets.Count == 0)
            {
                if (!dict.ContainsKey(item.Value)) dict[item.Value] = [];
                continue;
            }
            foreach (var target in slot.Targets)
                if (target.Parent is not null)
                    AddTarget(dict, item.Value, target.Parent);
        }
    }

    return Task.FromResult<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>>(
        dict.ToDictionary(kv => kv.Key, kv => (IReadOnlyList<IWorkflowNodeViewModel>)kv.Value.AsReadOnly()));
}
```

`SlotEnumerator.TrySelect` (the low-level lookup `TrySelect` uses) is a plain dictionary read of the selector's condition map — the map is maintained incrementally when items are added/removed:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`, lines 255-258

```csharp
public bool TrySelect(object value, out TSlot? slot)
{
    return conditionMap.TryGetValue(value, out slot);
}
```

At runtime the engine consults the same interface: for a `BranchSegment` it resolves `key = branch.IsDynamic ? await router.ResolveRouteKey(context) : branch.CompileKey` and runs the chosen option's sub-graph. See the [Data Flow page](../../../03_data-flow/00_workflow-system/index.md) for the full drive sequence.
