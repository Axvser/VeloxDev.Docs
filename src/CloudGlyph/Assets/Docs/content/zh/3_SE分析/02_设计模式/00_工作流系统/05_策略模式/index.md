# 工作流系统 — 设计模式 — 策略模式

选择器节点实现 `ICompileTimeRouter`，向编译器插入两个策略：`GetRouteTable()` 声明分支结构，`ResolveRouteKey(payload)` 为当前负载挑选分支。`RouterCompileMode` 选择策略变体 —— `Static` 在编译期锁定当前选中分支（编译器剪掉其余分支，并把它们的下游标成 Order = -1 绝对停止）；`Dynamic` 保留所有分支，运行期重新解析键（编译期负载为 null，所以 `ResolveRouteKey(null)` 返回 null → `IsDynamic`）。

demo 的 `EnumSelectorNodeViewModel`（基于 `VoltageRange` 枚举的 `SlotEnumerator<SlotViewModel>`）展示了随模式变化的 `GetRouteTable`：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`，198-243 行

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

`SlotEnumerator.TrySelect`（底层的查找）只是对选择器条件映射的字典读取 —— 映射在条目增删时增量维护：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`，255-258 行

```csharp
public bool TrySelect(object value, out TSlot? slot)
{
    return conditionMap.TryGetValue(value, out slot);
}
```

运行期引擎询问同一接口：对 `BranchSegment`，它解析 `key = branch.IsDynamic ? await router.ResolveRouteKey(context) : branch.CompileKey`，然后运行选中选项的子图。完整驱动序列见数据流页。
