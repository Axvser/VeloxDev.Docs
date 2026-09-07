# Workflow System — 设计模式 — 观察者模式

Helper 观察树的 `ObservableCollection` 并引发领域事件。`TreeHelper` 把 `Nodes`/`Links` 的 `CollectionChanged` 转发为 `NodeAdded/NodeRemoved/LinkAdded/LinkRemoved` 事件，并把树标脏以让虚拟化循环重跑：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`，第 169-197 行

```csharp
private void OnNodesChanged(object? sender, NotifyCollectionChangedEventArgs e)
{
    switch (e.Action)
    {
        case NotifyCollectionChangedAction.Add:
            if (e.NewItems is null) return;
            foreach (var item in e.NewItems)
            {
                if (item is IWorkflowNodeViewModel node)
                {
                    OnNodeAdded(node);
                    isDirty = true;
                }
            }
            break;
        case NotifyCollectionChangedAction.Remove:
            if (e.OldItems is null) return;
            foreach (var item in e.OldItems)
            {
                if (item is IWorkflowNodeViewModel node)
                {
                    OnNodeRemoved(node);
                    isDirty = true;
                }
            }
            break;
    }
    Component?.Virtualize(Viewport);
}
```

`WorkflowSpatialManager` 订阅这四个事件以保持空间索引同步：`OnNodeAdded` 插入节点 provider 并重试停在 `_pendingLinks` 的连接；`OnLinkAdded` 插入 `NodePairBoundsProvider`（`WorkflowSpatialManager.cs` 第 62-64 行订阅、第 240-266 行处理）。

在“值”一侧，演示 `EnumSelectorNodeViewModel` 观察其 `SlotEnumerator<SlotViewModel>`，对 `SelectorTypeName`/`CurrentValue` 的属性变化作出反应——值类型变化时推迟一帧重绑选中值，让 UI 的 `ItemsSource` 先换好新的 item 容器：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`，第 41-61 行

```csharp
private void OnOutputSlotsPropertyChanged(object? sender, PropertyChangedEventArgs e)
{
    if (e.PropertyName == nameof(SlotEnumerator<>.SelectorTypeName))
    {
        OnPropertyChanged(nameof(EnumType));
        OnPropertyChanged(nameof(EnumValues));
    }
    if (e.PropertyName == nameof(SlotEnumerator<>.CurrentValue))
    {
        var sc = SynchronizationContext.Current;
        if (sc is not null)
            sc.Post(_ => OnPropertyChanged(nameof(SelectedValue)), null);
        else
            OnPropertyChanged(nameof(SelectedValue));
    }
}
```

运行期仪器化是命令层的同款观察：`IVeloxCommand` 暴露 `Started/Exited/Enqueued/Dequeued` 生命周期事件，工作流代理工具用 `command.Exited += onExited` 等待单次/多次派发（`WorkflowAgentToolkit.WaitForCommandAsync/WaitForExitedAsync` 等，`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs` 第 2672-2754 行）。
