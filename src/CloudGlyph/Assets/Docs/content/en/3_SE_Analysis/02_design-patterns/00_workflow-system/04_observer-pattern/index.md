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

> Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/EnumSelectorNodeViewModel.cs`, lines 41-61

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

Runtime instrumentation is the same pattern at the command layer: node helpers subscribe to `ReceiveCommand.Started/Exited/...` to track active work.
