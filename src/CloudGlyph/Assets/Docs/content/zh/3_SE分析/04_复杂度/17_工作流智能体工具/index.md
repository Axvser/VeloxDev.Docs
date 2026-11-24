# 工作流智能体工具

`WorkflowAgentToolkit` 里的每个工具都直接操作活树，所以它的代价取决于图规模而不是提示词长度。真正的开销大头不是遍历本身，而是每个对象上的一次元数据遍历：`AppendScalarProperties` 每次调用都会重读该类型记录在案的成员表 —— 含继承成员 —— 所以“按节点线性”的读工具实际是按“节点 × 成员”线性。下列界均从所引用的控制流读出；若某个辅助函数的内部不在所引模块内，该界标记为推断。

## 代价模型

| 符号 | 含义 |
|---|---|
| $n$ | 树中节点数 |
| $m$ | 树中连线数 |
| $s$ | 单个节点的插槽数 |
| $p$ | 单个类型记录的属性数（含继承） |
| $k$ | 一次遍历返回的节点数 |
| $q$ | 一份补丁文档中的键数 |
| $T$ | 按类别掩码构造的工具数 |

`p` 没有被记忆化。`PropertiesOf` 在每个对象上重新解析访问器并再次遍历 `AIContextDirectory.Shared.MembersAcross(TypeName, "Properties")`，所以看似线性的读操作，实际是节点数与成员数的乘积。

## 工具构造

`CreateAllTools` 通过局部函数 `Add(category, items)` 填充列表，判断条件是 `(categories & category) == category`，每个工具块一次常数级位运算（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs:88-99`）。

```csharp
AITool T(Delegate method, string name, AgentActionCategory action)
    => new TrackedAIFunction(AIFunctionFactory.Create(method, name), Tools, _scope.Pipeline, action);

var tools = new List<AITool>();

void Add(WorkflowToolCategory category, params AITool[] items)
{
    if ((categories & category) == category)
        tools.AddRange(items);
}
```

构造本身是 $O(T)$ 的列表操作，外加每个工具一次 `AIFunctionFactory.Create`。第二遍按 `_scope.IsToolEnabled` 的哈希集合过滤。`ResetToolCallLimit` 在所有类别块之外添加，因此收窄掩码也删不掉它。

## 读与查询工具

| 操作 | 时间 | 空间 |
|---|---|---|
| `ListNodes` | $O(n \cdot p)$ | $O(n)$ JSON |
| `GetNodeDetail` | $O(p + s + \text{targets})$ | $O(p + s)$ |
| `ListConnections` | $O(m)$ 扫描，再 $O(m)$ 的 `Skip/Take` | $O(m)$ |
| `GetFullTopology` | $O(n \cdot (p+s) + m)$ | $O(n + m)$ |
| `FindNodes` | $O(n \cdot p)$ | $O(k)$ 输出 |
| `FindComponentById` | $O(n \cdot (p+s) + m)$ | $O(n)$ 临时字典 |
| `FindNodeById`、`IndexOfNode` | $O(n)$ | $O(1)$ |

`ListConnections` 先扫描全部连线、物化匹配列表，然后才分页，所以 `skip`/`take` 减少的是输出而不是工作量（`WorkflowAgentToolkit.cs:742-805`）。`FindComponentById` 在回答之前为每个节点构造一张插槽属性表，这是所有 `*ById` 工具共同承担的代价（`WorkflowAgentToolkit.cs:3480-3502`）。

## 遍历与结果报告

BFS 本身是线性的。`FindPath` 用父指针表加队列，时间 $O(n+m)$、空间 $O(n)$（`WorkflowAgentToolkit.cs:1880-1929`）。结果报告层破坏了这个界：`BuildNodeListResult` 对每个结果调用 `IndexOfNode`，而 `IndexOfNode` 是对 `Tree.Nodes` 的线性扫描（`WorkflowAgentToolkit.cs:1931-1944`、`:3460-3465`）。

```csharp
private string BuildNodeListResult(IEnumerable<INodeComponent> nodes)
{
    var arr = new VeloxJsonArray();
    foreach (var n in nodes)
    {
        arr.Add(new VeloxJsonObject
        {
            ["i"] = IndexOfNode(n),
            ["id"] = GetComponentId(n),
            ["t"] = n.GetType().Name,
        });
    }
    return arr.ToJson();
}
```

一次返回 $k$ 个节点的遍历，报告代价是

$$
T_{\text{report}} = O(k \cdot n)
$$

路径重建还要再加 $O(L_{\text{path}} \cdot n)$。瓶颈不在图遍历，而在给答案编号。

```plot
{
  "title": "遍历与索引化报告",
  "grid": true,
  "xAxis": { "domain": [1, 200] },
  "yAxis": { "domain": [0, 40000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "BFS: n" },
    { "fn": "x*ln(x)", "color": "#a78bfa", "title": "n log n" },
    { "fn": "x^2", "color": "#f472b6", "title": "k = n 时的报告" }
  ]
}
```

## 补丁、模式与校验

`ComponentPatcher.ApplyPatch` 对每个补丁键做一次成员查找、一次框架管理属性集合判断、一次后备命令探测、一次到声明类型的转换和一次相等性比较，然后才写入（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/ComponentPatcher.cs:76-90`）。对 $q$ 个键和 $p$ 个成员：

$$
T_{\text{patch}} = O(q \cdot (p + b))
$$

其中 $b$ 是后备命令发现代价。补丁文档在截断之前就已完整构造，所以结果长度上限约束的是令牌，不是峰值内存。

`TypeIntrospector.GetTypeSchema` 比“只读元数据”贵得多：它解析引用、遍历 `MembersAcross`、遍历所有语言，并且构造并序列化一个默认实例（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/TypeIntrospector.cs:106-120`）。

`ValidateWorkflow` 先做一遍节点扫描（含插槽与属性），建立邻接表，再用递归三色 DFS 找环（`WorkflowAgentToolkit.cs:2968-3101`）。时间为 $O(n \cdot (p+s) + m + \sum \text{validators})$；递归深度等于最长无环路径，病态图会栈溢出。

## 选择集与快照状态

`WorkflowAgentSelection.Add` 先复制当前数组，再用 `ContainsReference` 线性扫描每个新节点（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentSelection.cs:109-123`、`:446-452`）。把 $a$ 个节点加入大小为 $s$ 的集合：

$$
T_{\text{add}} = O(a \cdot (s+a))
$$

全选是最坏情况 $O(a^2)$。`Render` 把输出限制在 64 行，这约束的是提示词而不是更新代价。

`WorkflowStateTracker.GetChangesSinceLastSnapshot` 每次都先调用 `BuildSnapshot()`，即使什么都没变；没有脏标记，也不复用上一份对象（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowStateTracker.cs:42-56`）。因此一次差分的下限就是一次完整快照：

$$
T_{\text{diff}} = O(n \cdot (p+s) + m + \text{chars})
$$

## 上下文信封与缓存

每轮信封缓存在打包的 `ContextKey` 上：版本、选择修订号、用量档位，读取是常数时间（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:2106-2116`）。命中时提供方直接返回同一个 `AIContext` 实例，无锁、零分配（`Agent/Workflow/WorkflowAgentContextProvider.cs:86-110`）。未命中时渲染代价为 $O(g \log g + \text{disabled} \log \text{disabled} + r + T + \text{chars})$：规则列表与工具开关先快照再排序，预算读取是常数时间，且只重新发出与骨架不一致的段落。

## 相关

- [智能体安全与预算](../18_智能体安全与预算/index.md) —— 这些工具每次调用都要经过的闸门。
- [MCP集成](../20_MCP集成/index.md) —— 加入同一轮工具数组的外部工具。
- [子智能体](../21_子智能体/index.md) —— 在更小账本下继承这套工具集的子级。
