# Workflow System — 设计模式 — 策略模式

选择器节点实现 `ICompileTimeRouter`，给编译器插两个策略：`GetRouteTable()` 声明分支结构，`ResolveRouteKey(payload)` 为当前负载选定走哪个分支。`RouterCompileMode` 选择策略变体——`Static` 编译期锁定当前选中分支（其余分支被编译器剪除，其下游节点标记为 `Order = -1` 绝对停止）；`Dynamic` 让全部分支存活，运行期再解析 key（编译期负载为 null，故 `ResolveRouteKey(null)` 返回 null → 编为 `IsDynamic`）。

演示 `EnumSelectorNodeViewModel`（一个基于 `VoltageRange` 枚举的 `SlotEnumerator<SlotViewModel>`）展示了随模式变化的 `GetRouteTable`：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`，第 198-243 行

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

`ResolveRouteKey`（第 158-185 行）是运行期 key 的统一入口：`Dynamic` 且负载为 null 时返回 null（编译期不可判定）；运行期先读共享变量 `selector.value`，再按负载里的逐成员 0/1 标志路由（演示里 Python 节点按 grade 发 High/Low/Zero 标志），兜底取当前选中值。

`TrySelect` 底层是选择器条件映射的一次字典读取——映射在条目增删时增量维护：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/SelectorEx/SlotEnumerator.cs`，第 255-258 行

```csharp
public bool TrySelect(object value, out TSlot? slot)
{
    return conditionMap.TryGetValue(value, out slot);
}
```

运行期引擎查询同一接口：对 `BranchSegment`，`key = branch.IsDynamic ? await router.ResolveRouteKey(context) : branch.CompileKey`，再驱动所选 option 的子图。完整驱动序列见[数据流分析](../../../03_数据流分析/00_工作流系统/index.md)。
