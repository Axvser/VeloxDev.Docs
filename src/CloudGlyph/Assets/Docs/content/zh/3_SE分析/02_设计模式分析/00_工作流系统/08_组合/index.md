# Workflow System — 设计模式 — 组合

`IWorkflowNodeViewModel.Slots` 拥有 `IWorkflowSlotViewModel` 实例；连接由 `sender.Targets` / `receiver.Sources` 派生，并由 `WorkflowSpatialManager` 以节点对（`NodePairBoundsProvider`）索引：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/WorkflowSpatialManager.cs`，第 142-164 行

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
