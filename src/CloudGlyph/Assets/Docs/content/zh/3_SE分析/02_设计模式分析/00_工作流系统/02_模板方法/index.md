# Workflow System — 设计模式 — 模板方法

每个组件的 Helper 定义生命周期骨架（`Install` → 订阅集合、`Uninstall` → 取消订阅、`Closing/CloseAsync/Closed`）并暴露可覆写的钩子。`TreeHelper<T>` 调用 `base.Install` 后启用虚拟化；`HttpHelper<T>` 覆写 `Install` 订阅 `ReceiveCommand` 事件、`ReceiveAsync` 执行业务逻辑。

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
        Debug.Fail("EnableMap did not return a non-negative value as expected...");
    }
    InitializeMonoBehaviour();
}
```
