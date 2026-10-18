# 工作流系统 — 设计模式 — 观察者模式

Helper 观察树的 `ObservableCollection` 并抛出领域事件。`TreeHelper` 把 `Nodes`/`Links` 的 `CollectionChanged` 转发成 `NodeAdded/NodeRemoved/LinkAdded/LinkRemoved`，同时把树标脏，让虚拟化循环重跑：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`，169-197 行

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

`WorkflowSpatialManager` 订阅这四个事件以同步空间索引（`OnNodeAdded` 插入节点 provider，并重试暂存为 pending 的连线；`OnLinkAdded` 插入 `NodePairBoundsProvider`）。

值一侧同样如此：demo 的 `EnumSelectorNodeViewModel` 观察它的 `SlotEnumerator<SlotViewModel>`，对 `SelectorTypeName` / `CurrentValue` 变化作出反应，并把选中值的重新绑定延后一帧，好让 UI 的 `ItemsSource` 替换先完成：

> 源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`，41-62 行

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

运行期观测是命令层的同一模式：`IVeloxCommand` 抛出八个 `CommandEventType` 阶段；需要知道一次派发如何结束的调用方应等待完成，而不是订阅 —— `WorkflowAgentToolkit.WaitForCommandAsync`（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs`）等待 `IVeloxCommandCompletion.ExecuteAndWaitAsync`，这样才能观察到一次因锁被拒、永远不会抛 `Exited` 的调用。生产代码不订阅生命周期事件，只有测试订阅。

**第三个实例，在运行层（2026-09-27）。** `IExecutionObserver` 观察的是编译运行而非树：引擎在七个点调用 `OnObservedAsync`，参数为 `ExecutionObservation(kind, node, detail, attempt, elapsed)` —— `RunStarted`、`BranchStarted`、`NodeStarted`、`NodeSucceeded`、`NodeFailed`、`NodeRetried`、`RunEnded`。它配置为 `RuntimeContext.Observer`，与其他宿主接缝一样默认 `null`。

与树侧观察者相比有两点不同：

- **一个带 kind 的形状，而不是每个事件一个方法。** 新 kind 因此不会打断现有观察者。
- **抛异常的观察者不改变任何东西**（记 `[Observer]`），这与日志写入器的契约相反：丢一行日志是丢证据，所以那次失败报告在 `RuntimeContext.LogWriteFailed`；丢一条观察不是。

demo 在 `RunEnded` 把整条时间线折回一行摘要（`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`），因为一次运行驱动二十多个节点，逐个写会淹没日志。
