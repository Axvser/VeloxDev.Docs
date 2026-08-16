# Workflow System — Design Patterns — Template Method

Each component's Helper defines the lifecycle skeleton (`Install` → subscribe collections, `Uninstall` → unsubscribe, `Closing/CloseAsync/Closed`) and exposes overridable hooks. `TreeHelper<T>` calls `base.Install`, then enables virtualization; `HttpHelper<T>` overrides `Install` to subscribe `ReceiveCommand` events and `ReceiveAsync` to run business logic.

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
        Debug.Fail("EnableMap did not return a non-negative value as expected...");
    }
    InitializeMonoBehaviour();
}
```
