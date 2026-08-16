# Workflow System — Design Patterns — Composition

`IWorkflowNodeViewModel.Slots` owns `IWorkflowSlotViewModel` instances; links are derived from `sender.Targets` / `receiver.Sources` and are indexed as node pairs (`NodePairBoundsProvider`) by `WorkflowSpatialManager`:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/WorkflowSpatialManager.cs`, lines 142-164

```csharp
private void InsertLink(IWorkflowLinkViewModel link)
{
    if (link == null || _nodePairProviders.ContainsKey(link)) return;
    if (link.Sender?.Parent is IWorkflowNodeViewModel nodeA &&
        link.Receiver?.Parent is IWorkflowNodeViewModel nodeB &&
        nodeA != nodeB &&
        _nodeProviders.TryGetValue(nodeA, out var providerA) &&
        _nodeProviders.TryGetValue(nodeB, out var providerB))
    {
        var pairProvider = new NodePairBoundsProvider(nodeA, nodeB, providerA, providerB);
        _nodePairProviders[link] = pairProvider;
        _pairToLink[pairProvider] = link;
        _nodePairMap.Insert(pairProvider);
        AddToNodeIndex(nodeA, pairProvider);
        AddToNodeIndex(nodeB, pairProvider);
    }
}
```
