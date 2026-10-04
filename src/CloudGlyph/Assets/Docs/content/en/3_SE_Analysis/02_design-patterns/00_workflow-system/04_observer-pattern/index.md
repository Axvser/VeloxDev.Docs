# Workflow System — Design Patterns — Observer Pattern

Helpers observe the tree's `ObservableCollection`s and raise domain events. `TreeHelper` forwards `CollectionChanged` of `Nodes`/`Links` into `NodeAdded/NodeRemoved/LinkAdded/LinkRemoved` events and marks the tree dirty so the virtualization loop re-runs:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`, lines 169-197

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

`WorkflowSpatialManager` subscribes to those four events to keep the spatial index in sync (`OnNodeAdded` inserts the node provider and retries links parked as pending; `OnLinkAdded` inserts a `NodePairBoundsProvider`).

On the value side, the demo `EnumSelectorNodeViewModel` observes its `SlotEnumerator<SlotViewModel>` and reacts to `SelectorTypeName` / `CurrentValue` property changes, deferring a re-bind of the selected value one frame so the UI's `ItemsSource` swap has generated new item containers first:

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`, lines 41-62

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

Runtime instrumentation is the same pattern at the command layer: `IVeloxCommand` raises the eight `CommandEventType` stages, and a caller that needs to know how one dispatch ended awaits the completion instead of subscribing — `WorkflowAgentToolkit.WaitForCommandAsync` (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs` lines 3215-3233) awaits `IVeloxCommandCompletion.ExecuteAndWaitAsync`, which is what lets it observe a call that was refused under lock and would never have raised `Exited`. No production code subscribes to the lifecycle events; only the tests do.

**A third instance, at the run layer (2026-09-27).** `IExecutionObserver` watches the compiled run rather than the tree: the engine calls `OnObservedAsync` with an `ExecutionObservation(kind, node, detail, attempt, elapsed)` at seven points — `RunStarted`, `BranchStarted`, `NodeStarted`, `NodeSucceeded`, `NodeFailed`, `NodeRetried`, `RunEnded`. It is configured as `RuntimeContext.Observer` and, like the other host seams, is `null` by default.

Two differences from the tree-side observers above are worth noting:

- **One shape with a kind, not one method per event.** A new kind therefore does not break an existing observer — the same reasoning the library already applies elsewhere.
- **A throwing observer changes nothing** (logged as `[Observer]`), which is the opposite of the log writer's contract: losing a log line is losing evidence, so that failure is reported on `RuntimeContext.LogWriteFailed`; losing an observation is not.

The demo folds the whole timeline back into one summary line on `RunEnded` (`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`), because a run drives twenty-odd nodes and one line each would drown the log.
