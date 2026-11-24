# 智能体安全与预算

一次工具调用先经过两道闸门，再记到与祖先共享的账本上。每道闸门都遍历规则数组，所以安全代价与宿主规则数成正比，而不是与图规模；预算代价与派生深度成正比，而不是与花费成正比。

## 代价模型

| 符号 | 含义 |
|---|---|
| $r$ | 当前权限策略上的规则数 |
| $d$ | 调用方所在的派生链深度 |
| $|v|, |p|$ | 被匹配值与通配模式长度 |
| $t$ | 链上已花费的调用数 |
| $c$ | 工具结果的字符数 |

## 决策评估

`AgentPermissionPolicy` 不可变：`WithMode`、`WithRule`、`WithJudge`、`WithoutRules` 每次都分配新实例（`Src/Core/VeloxDev.Core.Extension/Agent/Safety/AgentPermissionPolicy.cs:73-95`）。切换模式或判定器是按引用的 $O(1)$；逐条添加规则会重建数组，所以增量建立 $r$ 条规则是

$$
T_{\text{setup}} = O(r^2)
$$

`Evaluate` 的顺序固定：拒绝扫描、Plan 模式拒绝、询问扫描、允许扫描、Auto 判定器、模式默认（`AgentPermissionPolicy.cs:100-124`）。

```csharp
if (Has(PermissionDecision.Deny, invocation)) return PermissionDecision.Deny;
if (Mode == AgentPermissionMode.Plan && ModeDefault(Mode, invocation.Category) == PermissionDecision.Deny)
    return PermissionDecision.Deny;
if (Has(PermissionDecision.Ask, invocation)) return PermissionDecision.Ask;
if (Has(PermissionDecision.Allow, invocation)) return PermissionDecision.Allow;

if (Mode == AgentPermissionMode.Auto && Judge is { } judge)
{
    try
    {
        return judge(invocation);
    }
    catch (Exception)
    {
        // A judge that cannot answer must not answer "yes". Nothing here is worth failing open for.
        return PermissionDecision.Deny;
    }
}
```

当没有规则能裁决时，`Has` 被调用三次，每次都是对同一数组的完整 LINQ 扫描。规则本身的代价是带一个回溯点的双指针通配匹配，而不是正则（`Src/Core/VeloxDev.Core.Extension/Agent/Safety/AgentPermissionRule.cs:70-103`），所以一次调用的最坏情况是

$$
T_{\text{eval}} = O(r \cdot |v| \cdot |p|)
$$

未决调用每次要做 $O(3r)$ 次 `Matches`。

## 闸门执行两遍

`TrackedAIFunction` 先请求管线拒绝，再请求确认，两条路径都会评估策略（`Src/Core/VeloxDev.Core.Extension/Agent/TrackedAIFunction.cs:77`、`:90`）。`ConfirmMutationAsync` 重新评估时没有类别判断，所以在注册了判定器的 `Auto` 模式下，读调用也可能两次进入判定器（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs:299-313`）。被拒绝时 `DescribePermissionRefusal` 还会再加第三次规则扫描。

代码没有按决策对规则做单遍划分，所以一次允许的调用付两遍扫描，一次拒绝最多付四遍。

## 预算执行

`CheckInvocation` 先评估规则集，然后（除非模式是 Bypass）读取账本并检查总量、读、写与令牌上限（`WorkflowAgentToolkit.cs:352-414`）。

```csharp
var (spent, readCalls, writeCalls) = _ledger.Usage;
if (_scope.MaxToolCalls.HasValue && spent >= _scope.MaxToolCalls.Value)
    return BudgetRefusal($"Tool call limit ({_scope.MaxToolCalls.Value}) reached.");

bool isQueryTool = IsQueryTool(toolName);
if (!isQueryTool && _scope.MaxWriteToolCalls.HasValue && writeCalls >= _scope.MaxWriteToolCalls.Value)
    return BudgetRefusal($"Mutation tool call limit ({_scope.MaxWriteToolCalls.Value}) reached.");
if (isQueryTool && _scope.MaxReadToolCalls.HasValue && readCalls >= _scope.MaxReadToolCalls.Value)
    return BudgetRefusal($"Query tool call limit ({_scope.MaxReadToolCalls.Value}) reached.");
```

计数器读取是 $O(1)$；它之前的规则评估才是唯一的超线性项。调用成功后，`AccountAsync` 增加账本；若 `AutoMarkDirty` 开启，非查询工具还会把树标脏（`WorkflowAgentToolkit.cs:469-483`）。Bypass 模式既不执行也不统计调用上限，但令牌上限仍然执行。

## 派生链上的账本

`ToolCallLedger` 持有三个由 `Interlocked` 更新的 `int` 计数器和一条指向父级的链（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/ToolCallLedger.cs:31-89`）。`Root` 是递归属性，`Spend` 向上走：

```csharp
public void Spend(bool isQuery)
{
    Interlocked.Increment(ref _total);
    if (isQuery)
        Interlocked.Increment(ref _read);
    else
        Interlocked.Increment(ref _write);

    // Walk rather than snapshot: a scope's own total must include everything its subtree spent, or the
    // sub-limit a host granted would never be reached while a child quietly spent the tree's allowance.
    Outer?.Spend(isQuery);
}
```

因此记账代价是

$$
T_{\text{spend}} = O(d)
$$

每次调用 $O(d)$，每次重置 $O(d)$，每个账本 $O(1)$ 存储。子级的上限永远严格小于父级的剩余额度，这正是树的终止条件。

## 令牌记账与提示词稳定

令牌计数器用 `Interlocked.Add` 累加至多三个值。`UsageBand` 把四个计数折叠成 20% 一档、封顶 5 档（`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:2124-2142`），只有档位进入 `ContextKey`。把计数分档，正是让跳动的令牌数不进入每轮渲染路径的原因：提示词最多滞后一档，同一档内字节不变。

`AppendBudgetLine` 在 80% 档位以下不打印用量，以上才打印百分比（`WorkflowAgentScope.cs:2306-2327`）。渲染代价是每行 $O(1)$ 加追加字符数。

## 结果长度上限

`TrackedAIFunction.CapResult` 对字符串用 `Length` 测量，但对 `AIFunctionFactory` 的结果调用 `JsonElement.GetRawText().Length` —— 为了测量而重新物化整段负载（`Src/Core/VeloxDev.Core.Extension/Agent/TrackedAIFunction.cs:135-148`）。

$$
T_{\text{cap}} = \begin{cases} O(1) & \text{字符串结果} \\ O(c) & \text{JSON 结果} \end{cases}
$$

负载此时已经生成，所以上限约束的是令牌而非内存。`CapText` 同理：它在文档完整之后才分配预览用的 `Substring`。

## 交互闸门

`ResolveConfirmationAsync` 用会话级 `HashSet` 检查已批准的操作键，$O(1)$；没有处理器时答案为否，`AllowAlways` 把键插入集合（`WorkflowAgentScope.cs:991-1004`）。`ResetToolCallLimit` 是唯一能重开预算的路径，它同时豁免闸门与记账（`WorkflowAgentToolkit.cs:500-531`）。

## 相关

- [工作流智能体工具](../17_工作流智能体工具/index.md) —— 被闸门放行的工具。
- [子智能体](../21_子智能体/index.md) —— 账本向上走过的链。
