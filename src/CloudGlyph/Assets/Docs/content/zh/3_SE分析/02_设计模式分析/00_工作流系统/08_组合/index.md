# Workflow System — 设计模式 — 组合

`IWorkflowNodeViewModel.Slots` 拥有 `IWorkflowSlotViewModel` 实例；连接不存储在节点上——每条连接是派生边 `sender.Targets` / `receiver.Sources`，空间管理器把连接再派生为**节点对边界**（`NodePairBoundsProvider`），使横穿视口的长连接保持两个端点节点都可见：

> 源码：`Src/Core/VeloxDev.Core/WorkflowSystem/GUI/Virtualization/WorkflowSpatialManager.cs`，第 146-180 行

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
        // Hold it for a retry on the next OnNodeAdded ...
        _pendingLinks.Add(link);
    }
}
```

端点节点尚未索引的连接被停在 `_pendingLinks`，并在下一次 `OnNodeAdded` 时经 `RetryPendingLinks`（第 249-259 行）重试——组合在任意增删/撤销/反序列化次序下都保持节点对索引一致。编译器消费同一形状：它沿每个节点槽位的 `Targets`/`Sources` 走，把拓扑分解成段（`ChainSegment`/`BranchSegment`/`ParallelSegment`）。
