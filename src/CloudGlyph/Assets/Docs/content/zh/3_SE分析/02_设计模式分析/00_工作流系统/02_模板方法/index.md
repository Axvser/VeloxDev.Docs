# Workflow System — 设计模式 — 模板方法

每个组件的 Helper 定义了生命周期骨架——`Install` 订阅集合事件、`Uninstall` 退订、`Closing/CloseAsync/Closed` 走完整命令集——并暴露可覆写的钩子。`TreeHelper<T>` 在 `Install` 中装配（订阅 `Nodes`/`Links` 的 `CollectionChanged`）；若以格子尺寸构造（启用虚拟化）还会调用 `EnableMap` 打开空间索引，并以 10 fps 的 MonoBehaviour 循环在树变脏时重跑虚拟化：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`，第 109-124 行

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
    InitializeMonoBehaviour();
}
```

`Uninstall`（第 126-141 行）退订事件并 `ClearMap`；`Closing/CloseAsync/Closed`（第 143-148 行）调用 `GetStandardCommands` 的命令锁生命周期（`WorkflowCommandEx.StandardClosing/ClosingAsync/Close/CloseAsync/Closed`）。骨架内其余可覆写点：`CreateLink`（150-157）、`ValidateConnection`（235-238，默认 `=> true`）、事件提早点 `OnNodeAdded/OnNodeRemoved/OnLinkAdded/OnLinkRemoved`。

同一骨架也塑造 `NodeHelper<T>`：`Install`（第 28-33 行）订阅 `Slots.CollectionChanged`，默认 `ReceiveAsync`（57-60）直接返回 `null`（“汇/终点”默认），`AccessAsync`（61-64）默认返回 `true`（放行），具体 Helper 只覆写执行钩子。演示 `EnumSelectorHelper`（派生自 `NodeHelper<EnumSelectorNodeViewModel>`）覆写 `ReceiveAsync` 实现仅路由语义——编译驱动时原样返回 `ctx.Data`，使被选分支读到传入负载：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/EnumSelectorHelper.cs`，第 8-40 行

```csharp
public override async Task<object?> ReceiveAsync(ITaskContext ctx, CancellationToken ct)
{
    if (Component is null) return null;

    // Compiled execution: the engine passes RuntimeContext (IRuntimeContext + ITaskContext); the sequence number is fixed at compile time.
    // Only record the routing direction; do not rewrite the badge. The router is routing-only: it must pass
    // the incoming payload through (return ctx.Data), otherwise the selected branch would see null Data.
    if (ctx is IRuntimeContext)
    {
        Component.LastRouted = Component.SelectedValue is { } sv ? $"[{sv}]" : "[?]";
        return ctx.Data;
    }
    // ...（后续为无状态广播路径：NetworkFlowContext + SelectorBroadcast）...
}
```

编译运行不会经由节点的命令进入这些 Helper——引擎直接调用 `Helper.ReceiveAsync`（详见[数据流分析](../../../03_数据流分析/00_工作流系统/index.md)）。
