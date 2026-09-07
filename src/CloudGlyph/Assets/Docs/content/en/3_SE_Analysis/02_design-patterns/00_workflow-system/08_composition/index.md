# Workflow System — Design Patterns — Composition

`IWorkflowNodeViewModel.Slots` owns `IWorkflowSlotViewModel` instances; links are not stored on the nodes — each link is a derived edge `sender.Targets` / `receiver.Sources`, and the spatial manager re-derives them as **node-pair bounds** (`NodePairBoundsProvider`) so a long link crossing the viewport keeps both endpoint nodes visible:

> Source: `Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs`, lines 146-180

```csharp
private void InsertLink(IWorkflowLinkViewModel link)
{
    if (link == null || _nodePairProviders.ContainsKey(link)) return;

    // Insert an AgentBounds proxy so the spatial grid can detect that both
    // endpoints should be considered visible when their combined bounds
    // intersect the viewport (e.g. a long link crossing the viewport).
    if (link.Sender?.Parent is IWorkflowNodeViewModel nodeA &&
        link.Receiver?.Parent is IWorkflowNodeViewModel nodeB &&
        nodeA != nodeB &&
        _nodeProviders.TryGetValue(nodeA, out var providerA) &&
        _nodeProviders.TryGetValue(nodeB, out var providerB))
    {
        _pendingLinks.Remove(link);

        var pairProvider = new NodePairBoundsProvider(nodeA, nodeB, providerA, providerB);
        _nodePairProviders[link] = pairProvider;
        _pairToLink[pairProvider] = link;
        _nodePairMap.Insert(pairProvider);

        // Build reverse index for graph-traversal queries
        AddToNodeIndex(nodeA, pairProvider);
        AddToNodeIndex(nodeB, pairProvider);
    }
    else if (link.Sender?.Parent is IWorkflowNodeViewModel &&
             link.Receiver?.Parent is IWorkflowNodeViewModel &&
             link.Sender.Parent != link.Receiver.Parent)
    {
        // Both endpoints exist and differ, but at least one endpoint node is not registered yet
        // (LinkAdded fired before that node was inserted, e.g. deserialized/undo orderings).
        // Hold it for a retry on the next OnNodeAdded — otherwise it would be silently dropped
        // and never become spatially visible, while the slot state still updates.
        _pendingLinks.Add(link);
    }
}
```

A link whose endpoint node is not indexed yet is parked in `_pendingLinks` and retried on the next `OnNodeAdded` (`RetryPendingLinks`) — the composition keeps the pair index consistent under arbitrary add/remove/undo orderings. The compiler consumes the same shape: it walks each node's slots' `Targets`/`Sources` to decompose the topology into segments.
