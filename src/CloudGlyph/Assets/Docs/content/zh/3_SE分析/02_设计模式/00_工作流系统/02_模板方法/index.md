# 工作流系统 — 设计模式 — 模板方法

每个组件的 Helper 定义生命周期骨架 —— `Install` 订阅集合事件、`Uninstall` 退订、`Closing/CloseAsync/Closed` 驱动整套命令 —— 并暴露可重写钩子。`TreeHelper<T>` 调用 `base.Install`；若构造时给了 cell 尺寸，它还会启用空间虚拟化（`EnableMap`），并启动一个 10 fps 的 Tickable 循环，在树变脏时重新虚拟化。

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`，109-124 行

```csharp
public virtual void Install(IWorkflowTreeViewModel tree)
{
    Component = tree as T;
    commands = tree.GetStandardCommands();
    VisibleItems = [];
    tree.Nodes.CollectionChanged += OnNodesChanged;
    tree.Links.CollectionChanged += OnLinksChanged;

    if (!useVirtualization) return;

    if (Component is null || tree.EnableMap(CellSize, VisibleItems) < 0)
    {
        Debug.Fail("EnableMap did not return a non-negative value as expected. Please check the implementation of EnableMap in the IWorkflowTreeViewModel.");
    }
    InitializeTickable();
}
```

同一骨架也塑造 `NodeHelper<T>`：它在 `Install` 订阅 `Slots.CollectionChanged`，`ReceiveAsync` 默认返回 `null`，具体 Helper 只需重写执行钩子。demo 的 `EnumSelectorHelper`（派生自 `NodeHelper<EnumSelectorNodeViewModel>`）重写 `ReceiveAsync` 实现只做路由的语义 —— 编译运行时它原样返回 `ctx.Data`，让选中的分支读到传入负载。

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/EnumSelectorHelper.cs`，8-19 行

```csharp
public override async Task<object?> ReceiveAsync(ITaskContext ctx, CancellationToken ct)
{
    if (Component is null) return null;

    // Compiled execution: the engine passes RuntimeContext (IRuntimeContext + ITaskContext).
    // The router is routing-only: it must pass the incoming payload through (return ctx.Data),
    // otherwise the selected branch would see null Data.
    if (ctx is IRuntimeContext)
    {
        Component.LastRouted = Component.SelectedValue is { } sv ? $"[{sv}]" : "[?]";
        return ctx.Data;
    }
    // ...stateless broadcast path (NetworkFlowContext + SelectorBroadcast)...
}
```

相比之下，编译运行从不通过节点命令进入这些 Helper —— 引擎直接调用 `Helper.ReceiveAsync`（见数据流页）。
