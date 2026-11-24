# 工作流运行时

`RunAsync` 驱动一张编译图。结构性遍历是线性的，扇出是交错的异步而非线程并行；真正出乎意料的代价在记账上：产物登记每次成功都扫描不断增长的完成列表，检查点保存又对产物表逐节点扫描。开启检查点的宽图上，单轮工作变成三次方。

记号：$V$ 个节点，$E$ 条边，单次扇出 $B$ 个分支，重定向 $R$（上限 50），检查点保存 $X$ 次，嵌套深度 $D$。

## 代价模型

| 操作 | 时间 | 出处 |
|---|---|---|
| `RunAsync` 入口 | $O(V)$ 图遍历 + $O(R \cdot \text{单轮})$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:56` |
| 单次结构遍历 | $O(V + E)$ | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:145` |
| 单节点驱动 | $O(1)$ + 汇合 $O(\text{入度})$ + 重试循环 | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:507` |
| 产物登记 | 每次成功 $O(V)$ — **单轮 $O(V^2)$** | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Model/RuntimeContext.cs:391` |
| 检查点保存 | 每次成功 $O(V^2)$，**单轮 $O(V^3)$** | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:764` |
| 并行扇出 | 总工作量 $\sum_B$；墙钟在 await 处重叠 | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:413` |
| 重定向 | 重启整图，上限 50 | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:94` |
| 上游判定 | 每次重定向校验 $O(V + E)$ 反向 BFS | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:501` |
| 补偿 | $O(V)$ 逆序 | `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:671` |

## 结构遍历

入口按顺序派发，一条链就是对节点的一个循环，编译序号从绑定表常数时间取得：

```csharp
for (int i = 0; i < exec.Nodes.Count; i++)
{
    ...
    if (done?.Contains(node) == true)
        ...
    await DriveAsync(node, context, bindings, ct);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:192-219`

重定向不是就地恢复，而是带目标序号重启整图，跳过目标之前的节点：

```csharp
while (true)
{
    var terminated = await RunGraphAsync(graph, context, bindings, ct, redirectTarget, redirects == 0 ? done : null);
    if (!terminated && context.PendingRedirectTarget is { } next)
    {
        redirects++;
        if (redirects > MaxRedirects)
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:94-109`

由于 `MaxRedirects` 为 50，最坏是 51 次结构遍历，而不是无限重试。

## 扇出是异步交错，不是线程并行

分支作为任务启动并一起等待：

```csharp
for (int i = 0; i < count; i++)
{
    branchContexts[i] = new BranchRuntimeContext(context) { Data = sourceData };
    tasks[i] = RunOneBranchAsync(branches[i], branchContexts[i], bindings, i, ct, redirectTarget, done, gate);
}

var terminated = await Task.WhenAll(tasks);
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs:437-443`

总工作量是各分支之和。只有当节点体真正挂起（I/O）时墙钟才下降；CPU 密集的节点体在宿主线程上依次运行。可选的信号量限制每组在飞分支数。

## 二次记账

登记产物时会写入当前轮标记，并重建完成列表——先移除同一节点的旧条目：

```csharp
_outputs[node] = (Attempt, value);
...
_completed.RemoveAll(entry => ReferenceEquals(entry.Node, node));
_completed.Add((node, value));
```

出处：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Model/RuntimeContext.cs:394-400`

这个 `RemoveAll` 是 $O(V)$，每个成功节点执行一次，所以产物记账每轮 $O(V^2)$。配置了检查点存储时，保存还要遍历产物表并对每个条目做线性键查找，即每次成功再来一个 $O(V^2)$——每轮 $O(V^3)$：

$$
T_{\text{pass}}^{\text{checkpoint}}(V,E) = O(V + E + V^3)
$$

```plot
{
  "title": "运行时每轮记账",
  "grid": true,
  "xAxis": { "domain": [0, 40] },
  "yAxis": { "domain": [0, 64000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "结构遍历，O(V)" },
    { "fn": "x*x", "color": "#a78bfa", "title": "产物登记，O(V^2)" },
    { "fn": "x*x*x", "color": "#f472b6", "title": "逐次检查点，O(V^3)" }
  ]
}
```

关闭检查点存储就完全去掉三次项；登记仍是二次，但几百个节点的完成列表让它在实践中可忽略。

## 内存

上下文持有产物表 $O(V)$、完成列表 $O(V)$，以及各含三个集合的检查点 $O(V)$。扇出每组增加 $O(B)$ 个分支上下文与任务，嵌套增加 $O(D)$ 栈。日志默认不设上限保留；配置上限后，裁剪从 `ObservableCollection` 前端移除，每移除一行 $O(n)$。
