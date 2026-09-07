# Workflow Agent — 设计模式 — 备忘录

`WorkflowStateTracker` 以最小上下文为 Agent 提供备忘录式变化观察：`TakeSnapshot` 把当前树状态存为 JSON `JObject`（即*备忘录*），`GetChangesSinceLastSnapshot` 将已存快照与新建快照比对，按 `RuntimeId` 返回属性级差异（增删改的节点/连接），而不是让 agent 每轮重读完整状态。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowStateTracker.cs`，第 31-71 行

```csharp
public string GetChangesSinceLastSnapshot()
{
    var current = BuildSnapshot();

    if (_lastSnapshot == null)
    {
        _lastSnapshot = current;
        Interlocked.Increment(ref _version);
        return JsonConvert.SerializeObject(new
        {
            status = "full",
            message = "No previous snapshot; returning full state.",
            version = _version,
            state = current
        }, Formatting.Indented);
    }

    var diff = ComputeDiff(_lastSnapshot, current);
    _lastSnapshot = current;
    Interlocked.Increment(ref _version);

    return JsonConvert.SerializeObject(new
    {
        status = "diff",
        version = _version,
        changes = diff
    }, Formatting.Indented);
}
```

`ComputeDiff` 按 `RuntimeId`（来自每个组件的 `IWorkflowIdentifiable.Helper`）为节点/连接建索引，且只通过 `JToken.DeepEquals` 比较标量/枚举属性，因此差异绝不会物化整棵子树比较（`WorkflowStateTracker.cs`，第 73-192 行）。工具包每作用域持有一个追踪器（`WorkflowAgentToolkit.cs`，第 27 行），并通过 `TakeSnapshot` 与 `GetChangesSinceSnapshot` 工具暴露它。底层的撤销/重做（Core）是发起者自身的历史机制；该追踪器是对同一张图的轻量正交视图。
