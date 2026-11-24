# 使用

## 模式矩阵

`AgentPermissionPolicy.ModeDefault(mode, category)` 就是一个模式的全部约定，是五个模式乘五个分类：

| 模式 | Read | Edit | Execute | Curate | Interact |
|---|---|---|---|---|---|
| `Plan` | Allow | Deny | Deny | Deny | Allow |
| `Manual` | Allow | Ask | Ask | Ask | Allow |
| `AutoEdit` | Allow | Allow | Ask | Ask | Allow |
| `Auto` | Allow | Allow | Allow | Ask | Allow |
| `Bypass` | Allow | Allow | Allow | Allow | Allow |

任何模式下 `Read` 与 `Interact` 都不会问用户。`Interact` 就是「提问」这个机制本身——把提问挡掉的模式只会让智能体能够拒绝，却不能询问。

**预期结果：** 在 `AutoEdit` 下，`DeleteNode`（`Edit`）按矩阵是允许的；安装准备里加的规则把它变成 `Ask`。

## 判定顺序

`Evaluate` 从最强到最弱，这个顺序就是约定：

1. `Deny` 规则——无条件，这正是 `Bypass` 不等于「关掉安全系统」的原因；
2. `Plan` 的拒绝——同样无条件，所以 `Allow` 规则无法在规划期间打开图编辑；
3. `Ask` 规则；
4. `Allow` 规则；
5. judge，**仅在 `Auto` 下**；
6. `ModeDefault(mode, category)`。

judge 抛异常时回答 `Deny`，绝不回答 `Allow`。

## 规则写法

`AgentPermissionRule` 按前缀指定选择轴：

```csharp
var policy = AgentPermissionPolicy.For(AgentPermissionMode.Auto)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask,  "Get*"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask,  "source:mcp:filesystem"));
```

| 模式 | 命中 |
|---|---|
| `DeleteNode`、`Get*` | 工具名，`*` 匹配任意字符序列 |
| `category:Edit` | 某个 `AgentActionCategory` 下的全部工具 |
| `source:mcp:filesystem` | 来源为该 MCP 服务器的工具；`source:mcp:management` 是 MCP 管理 toolkit |

匹配不区分大小写，也没有转义。名字里含 `*` 的工具无法精确匹配；工具名都是 C# 标识符，所以没有代价。

**预期结果：** `GetNodeDetail` 为 `Ask`，`AddMcpServer` 为 `Deny`，来自 `mcp:other` 的 `read_file` 不受 `mcp:filesystem` 规则影响。

## 判定器

judge 是宿主对「规则与模式都没有定论」的调用的回答。它只在 `Auto` 下运行；在 `AutoEdit` 里矩阵已经对 `Edit` 作出决定，judge 根本不会被问到。

```csharp
var judged = AgentPermissionPolicy.For(AgentPermissionMode.Auto)
    .WithJudge(call => call.Name == "RunCompiledWorkflow"
        ? PermissionDecision.Deny
        : PermissionDecision.Allow);

Console.WriteLine(judged.Evaluate(new ToolInvocation(
    "RunCompiledWorkflow", AgentActionCategory.Execute, null,
    new Dictionary<string, object?>()))); // Deny
```

**预期结果：** 输出 `Deny`。把 judge 改成抛异常，同一调用仍然输出 `Deny`，只是理由不同：答不出来的闸门不能答「是」。

## 预算

| 设置方法 | 约束 |
|---|---|
| `WithMaxToolCalls` | 会话内全部调用 |
| `WithMaxReadToolCalls` | toolkit 判定为查询的调用 |
| `WithMaxWriteToolCalls` | 修改图的调用 |
| `WithMaxTokens` | `InputTokens` / `OutputTokens` / `TotalTokens` |
| `WithMaxToolResultChars` | 单个工具结果的大小（默认 64 KiB） |

三个细节决定真实行为：

- **`Bypass` 跳过三道调用数上限，也不记账。** 它不跳过 `MaxTokens`，也不跳过 `Deny` 规则。提示词由同一个模式生成，所以模型不会围着一堵不会执行的墙规划。
- **`ResetToolCallLimit` 永远注册、永远放行。** 它是宿主唯一的预算出口；在最需要它的时候把它藏起来毫无意义。
- **子代理共用同一本账。** 子代理的额度是父级额度的子上限，不是另一口锅；见[子智能体](../../21_子智能体/index.md)。

**预期结果：** 设置 `WithMaxToolCalls(2)` 后，第三次成功调用被拒绝；拒绝文案点名上限与 `ResetToolCallLimit`，而不只是「宿主设置」。

## 执行与通用命令

两个开关位于工具体内，而不是共享包装器里：

```csharp
scope.WithAllowNodeExecution(true)                       // ExecuteNode / RunCompiledWorkflow
     .WithAllowedGenericCommands("SendEmail", "ExportCsv"); // ExecuteCommandOnNode / ExecuteCommandById
```

两者默认关闭。`WithAllowNodeExecution` 是 demo 运行节点业务代码所需的开关；图不可信时保持关闭。

**预期结果：** 在 `WithAllowNodeExecution(true)` 之前，`ExecuteNode` 返回拒绝。

## 验证

1. 运行完整程序。它逐条打印每个调用的决策，以及 `Bypass` 交叉检查。
2. 把 `AutoEdit` 改成 `Plan` 再跑：`MoveNode` 从 `Allow` 变成 `Deny`，而 `category:Edit` 的 `Allow` 规则无法把它打开。
3. 加一条写错模式的规则，确认它什么都不改——未命中的规则是静默的，所以要看打印出来的决策，不要靠假设。

## 完整代码

```csharp
using VeloxDev.AI.Safety;

var empty = new Dictionary<string, object?>();

var calls = new[]
{
    new ToolInvocation("MoveNode",            AgentActionCategory.Edit,    null, empty),
    new ToolInvocation("RunCompiledWorkflow", AgentActionCategory.Execute, null, empty),
    new ToolInvocation("AddMcpServer",        AgentActionCategory.Curate,  "mcp:management", empty),
    new ToolInvocation("DeleteNode",          AgentActionCategory.Edit,    null, empty),
};

var policy = AgentPermissionPolicy.For(AgentPermissionMode.AutoEdit)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask,  "DeleteNode"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"));

foreach (var call in calls)
    Console.WriteLine($"{call.Name,-22} {policy.Evaluate(call)}");

var bypass = AgentPermissionPolicy.For(AgentPermissionMode.Bypass)
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "DeleteNode"));
Console.WriteLine($"Bypass still denies: {bypass.Evaluate(calls[3])}");

var judged = AgentPermissionPolicy.For(AgentPermissionMode.Auto)
    .WithJudge(call => call.Name == "RunCompiledWorkflow"
        ? PermissionDecision.Deny
        : PermissionDecision.Allow);
Console.WriteLine($"Judge on Execute: {judged.Evaluate(calls[1])}");
```

**预期输出：**

```text
MoveNode               Allow
RunCompiledWorkflow    Ask
AddMcpServer           Deny
DeleteNode             Ask
Bypass still denies:   Deny
Judge on Execute:      Deny
```

## 运行声明

- ⚠️ 未实际运行 —— 仅对照 `Src/Core/VeloxDev.Core.Extension/Agent/Safety/AgentPermissionPolicy.cs`、`AgentPermissionRule.cs`、`ToolInvocation.cs`，以及 `Src/Test/Unit/Core/VeloxDev.Core.Extension.Test/Agent/Safety/AgentPermissionPolicyTests.cs` 中逐格写出的矩阵做了静态核对。预期输出依据该测试的矩阵；没有记录运行输出。
