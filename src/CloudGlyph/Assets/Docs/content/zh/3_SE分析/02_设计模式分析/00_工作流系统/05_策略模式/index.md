# Workflow System — 设计模式 — 策略模式

`SlotEnumerator<TSlot>` 通过 `SetSelector(type)` 交换输出槽策略。`BoolSelectorNodeViewModel` 与 `EnumSelectorNodeViewModel` 实现 `ICompileTimeRouter`，让编译器预先收集路由表（`GetRouteTable`），`ResolveRouteKey` 决定当前走哪个分支 —— 静态模式编译期锁定、剪枝未选中分支；动态模式运行期重解析：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/BoolSelectorNodeViewModel.cs`，第 94-120 行

```csharp
public Task<object?> ResolveRouteKey(object? payload)
{
    if (CompileMode == RouterCompileMode.Dynamic && payload is null)
        return Task.FromResult<object?>(null);

    if (payload is IRuntimeContext ctx && ctx.TryGet("selector.bool", out var v) && v is string s)
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
