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

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`，第 41-62 行

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

运行期仪器化是命令层的同款观察：`IVeloxCommand` 会抛出八个 `CommandEventType` 阶段，而需要知道某一次派发如何结束的调用方，采用的是**等待完成**而不是订阅事件 —— `WorkflowAgentToolkit.WaitForCommandAsync`（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs` 第 3215-3233 行）await `IVeloxCommandCompletion.ExecuteAndWaitAsync`，正因如此它才能观察到「被锁挡下、永远不会抛 `Exited`」的调用。生产代码中没有任何地方订阅这些生命周期事件，只有测试会订阅。

**运行层的第三处实例（2026-09-27）。** `IExecutionObserver` 观察的是编译运行而不是树：引擎在七个点上调用 `OnObservedAsync`，参数是一个 `ExecutionObservation(kind, node, detail, attempt, elapsed)` —— `RunStarted`、`BranchStarted`、`NodeStarted`、`NodeSucceeded`、`NodeFailed`、`NodeRetried`、`RunEnded`。它配在 `RuntimeContext.Observer` 上，并且与其它宿主接缝一样默认是 `null`。

与上面树侧的观察者相比有两处差别值得注意：

- **一个形状带一个种类，而不是每种事件一个方法。** 新增一种因此不会破坏既有的观察者 —— 与库里别处已经采用的同一套理由。
- **抛异常的观察者什么都不改变**（记一行 `[Observer]`），这与日志写入器的契约正好相反：丢一行日志就是丢一份证据，所以那种失败要在 `RuntimeContext.LogWriteFailed` 上上报；丢一条观察不是。

demo 把整条时间线在 `RunEnded` 时折成一行汇总（`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`），因为一轮跑二十来个节点，逐条写会把日志本身淹掉。
