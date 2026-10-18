# 工作流代理 —— 设计模式 —— 备忘录

`WorkflowStateTracker` 为 Agent 提供备忘录式的变化观察，且只用最小上下文：`TakeSnapshot` 把当前树状态存成 `VeloxJsonObject`（*备忘录*），`GetChangesSinceLastSnapshot` 把存储的快照与新构建的快照比较，返回属性级差异 —— 按 `RuntimeId` 的新增/移除/修改节点与链接 —— 而不让 agent 每轮重读完整状态。

> 源码：`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowStateTracker.cs`

```csharp
public string GetChangesSinceLastSnapshot()
{
    var current = BuildSnapshot();

    if (_lastSnapshot == null)
    {
        _lastSnapshot = current;
        Interlocked.Increment(ref _version);
        return new VeloxJsonObject
        {
            ["status"] = "full",
            ["message"] = "No previous snapshot; returning full state.",
            ["version"] = _version,
            ["state"] = current,
        }.ToJson(VeloxJsonFormat.Indented);
    }

    var diff = ComputeDiff(_lastSnapshot, current);
    _lastSnapshot = current;
    Interlocked.Increment(ref _version);

    return new VeloxJsonObject
    {
        ["status"] = "diff",
        ["version"] = _version,
        ["changes"] = diff,
    }.ToJson(VeloxJsonFormat.Indented);
}
```

`ComputeDiff` 按 `RuntimeId`（经每个组件的 `IWorkflowIdentifiable.Helper`）索引节点与链接，只比较标量/枚举属性，因此差异从不物化完整子树比较。JSON 来自归档引擎自己的树（`VeloxDev.Serialization.VeloxJsonObject` / `VeloxJsonFormat`），而不是 Newtonsoft。工具包每个作用域拥有一个 tracker，并通过 `TakeSnapshot` 与 `GetChangesSinceSnapshot` 工具暴露它。底层 workflow 命令（Core 的撤销/重做）是发起者自己的历史机制；这个 tracker 是同一图上的轻量、正交视图。
