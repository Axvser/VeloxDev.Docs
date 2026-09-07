# Workflow System — Design Patterns — Template Method

Each component's Helper defines the lifecycle skeleton — `Install` subscribes collection events, `Uninstall` unsubscribes, `Closing/CloseAsync/Closed` drive the whole command set — and exposes overridable hooks. `TreeHelper<T>` calls `base.Install`; when it was constructed with a cell size it also enables spatial virtualization (`EnableMap`) and starts a 10 fps MonoBehaviour loop that re-virtualizes while the tree is dirty.

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`, lines 109-124

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

The same skeleton shapes `NodeHelper<T>`: it subscribes `Slots.CollectionChanged` in `Install`, defaults `ReceiveAsync` to return `null`, and lets a concrete helper override just the execution hook. The demo `EnumSelectorHelper` (derived from `NodeHelper<EnumSelectorNodeViewModel>`) overrides `ReceiveAsync` to implement routing-only semantics — it returns `ctx.Data` unchanged under a compiled run so the selected branch reads the incoming payload.

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/EnumSelectorHelper.cs`, lines 8-19

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

The compiled run, by contrast, never enters these helpers through the node's commands — the engine calls `Helper.ReceiveAsync` directly (see the [Data Flow page](../../../03_data-flow/00_workflow-system/index.md)).
