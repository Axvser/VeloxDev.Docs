# 子智能体

子智能体是一个嵌套的 `WorkflowAgentScope`，工具面更窄、账本更小。派生代价是配置工作 —— 集合求交与版本递增；反复出现的代价则是每次工具调用一次深度回溯，以及每次状态变化一次整表复制。

## 代价模型

| 符号 | 含义 |
|---|---|
| $n$ | 单个作用域的直接子级数 |
| $N$ | 整个子智能体森林的节点数 |
| $w$ | 单层树的宽度 |
| $d$ | 派生深度 |
| $T$ | 父级可用的工具数 |
| $g$ | 授予子级的工具数 |
| $S$ | 参与判断的技能或 MCP 服务器数 |

## 派生

`TrySpawn` 先沿账本下推预算：取父级账本的剩余额度，最多授予其余额减一（`Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentScope.cs:459-470`）。

```csharp
// ── the allowance: a share of what the parent has left, and never the whole of it ──
var parentLedger = parent.CreateToolkit().Ledger;
var remaining = RemainingAllowance(parent, parentLedger);
var granted = Math.Min(request.MaxToolCalls ?? remaining, remaining - 1);
if (granted < 1)
{
    refusal = "No tool-call allowance remains for a sub-agent. The session's budget is spent, or this "
            + "agent's own share is; report what you have done rather than delegating further.";
    return null;
}
```

`remaining - 1` 这个钳制就是终止性论证：

$$
\text{granted} = \min(\text{requested}, \text{remaining} - 1) < \text{remaining}
$$

所以授予量沿每条根到叶路径严格递减，$d$ 被根上限所界。

随后工具与技能选择把请求与父级实际提供的能力求交，逐名使用 `List.Contains(..., OrdinalIgnoreCase)`（`SubAgentScope.cs:510-522`、`:684-699`），并在一个扫描授权列表的循环里关闭所有未授权工具（`SubAgentScope.cs:562-564`）。

$$
T_{\text{spawn}} = O(d + w \cdot T + T \cdot g + S)
$$

每次真正关闭工具还会递增子作用域的 `Version`，所以派生代价包含一次渲染失效。

## 账本记账

`ToolCallLedger.Spend` 增加三个计数器并递归到 `Outer`（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/ToolCallLedger.cs:57-68`）；`RemainingAllowance` 读取 `Root` 与三个计数器（`SubAgentScope.cs:757-778`）。

$$
T_{\text{spend}} = O(d), \qquad T_{\text{remaining}} = O(d)
$$

这就是“子级无法悄悄超额”的代价：每次调用都要为整条祖先链付费。

## 名册更新

`Republish` 把每个条目重新投影成新的 `SubAgentSummary[]`，并复制每行的被丢弃请求列表（`SubAgentScope.cs:385-412`）。它挂到每一行的 `PropertyChanged` 上，因此一次行写入会复制整份名册。

$$
T_{\text{publish}} = O(n + D)
$$

其中 $D$ 是被丢弃行总数。`RefreshCallCounts` 以 $O(n)$ 读取每个子级的工具用量，因为工具集是缓存的（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:1555`）。`List`、`GetResult`、`RowsFor` 各自强制一次重发布，`Find` 是锁内线性扫描（`SubAgentScope.cs:915-919`、`:942-986`）。若调用方每次变化后都列一次，总代价是 $O(n^2)$。

## 等待、结果与取消

`WaitAsync` 物化选中的行，让 `Task.WhenAll` 与延时任务竞速，并通过引用区分超时（`SubAgentScope.cs:965-978`）。准备是 $O(n)$，实际耗时受 `timeoutMs` 限制。`Cancel` 先线性 `Find`，再 `GetResult`，含重发布在内为 $O(n)$。

## 树视图

`SubAgentTreeViewModel.Rebuild` 原地对账：已有节点按 id 在字典中查找，离开的节点从后往前删除，新增节点用 `IndexOf` 加 `Move`（`Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentTreeViewModel.cs:425-447`）。由于 `IndexOf` 与 `SubAgentsOf` 都是线性扫描，宽度为 $w$ 的一层代价是 $w^2$。

$$
T_{\text{tree}} = O\left(N + \sum_{\text{levels}} w^2\right)
$$

```plot
{
  "title": "树重建：均衡树与单层宽扇出",
  "grid": true,
  "xAxis": { "domain": [1, 100] },
  "yAxis": { "domain": [0, 10000] },
  "data": [
    { "fn": "x", "color": "#4a9eff", "title": "N 个节点" },
    { "fn": "x^2", "color": "#f472b6", "title": "扁平扇出" }
  ]
}
```

`RecomputeAggregates` 每个访问到的节点自底向上汇总一次子树，整个重建 $O(N)$，每个节点发出七次通知（`SubAgentTreeViewModel.cs:225-245`）。`QueueRebuild` 只有在存在且不在当前 `SynchronizationContext` 时才合并（`:493-510`）；没有 UI 上下文时，每次 `Changed` 都同步跑一次完整重建。

## 缓存渲染

`SubAgentAgentContextProvider` 按作用域 `Version` 缓存指令与工具，键不变就返回同一批实例（`Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentAgentContextProvider.cs:77-96`）。名册块只在版本变化时重建，但它在截断到 200 字符之前会先复制每个子级的结果（`SubAgentAgentToolkit.cs:296-334`），所以渲染是 $O(n + \sum \text{结果长度})$ 而不是 $O(n)$。

## 释放

`DisposeAsync` 快照运行中的条目、全部取消、等待每个运行结束并取消订阅每一行（`SubAgentScope.cs:1019-1054`）。簿记为 $O(n)$，实际耗时取决于最慢的子级。

## 相关

- [智能体安全与预算](../18_智能体安全与预算/index.md) —— 子级继承的账本与策略。
- [智能体仪表盘与转录](../22_智能体仪表盘与转录/index.md) —— 状态行的另一个消费者。
