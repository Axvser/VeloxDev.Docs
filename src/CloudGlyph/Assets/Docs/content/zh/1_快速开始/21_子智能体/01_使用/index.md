# 使用

## 五个派发工具

| 工具 | 作用 |
|---|---|
| `SpawnSubAgent` | 启动子代理并立刻返回句柄 |
| `WaitSubAgents` | 等待指定子代理或全部；超时是信息，不是失败 |
| `GetSubAgentResult` | 读取一个子代理的结果，受 `maxChars` 限制 |
| `ListSubAgents` | 列出名册与每个子代理的状态 |
| `CancelSubAgent` | 停止正在运行的子代理 |

等待超时时报告 `timedOut: true`，子代理继续运行，模型可以再等或取消。`GetSubAgentResult` 只在子代理完成后才返回答案。

**预期结果：** 子代理仍是 `Running` 时 `SpawnSubAgent` 已返回句柄；短超时的 `WaitSubAgents` 返回 `timedOut: true` 与 `state: "Running"`。

## 一次 spawn 可以要求什么

每个收窄字段都是可选的，**省略表示继承，而不是「没有」**。空数组才表示「一个都不要」，与省略不同。

| 字段 | 效果 |
|---|---|
| `task` | 子代理的用户消息；必填 |
| `name` | 名册标签（省略时用编号代替） |
| `allowedTools` | 子代理可用的精确工具集 |
| `allowedSkills` | 子代理可读的技能；一个都不给时它的技能工具也一并移除 |
| `allowedMcpServers` | 子代理可访问的 MCP 服务器 |
| `maxToolCalls` / `maxReadToolCalls` / `maxWriteToolCalls` | 子代理的子上限 |
| `allowNodeExecution` | 子代理能否运行节点业务代码 |
| `allowedGenericCommands` | 子代理可调用的白名单命令名 |
| `model` | 本库不解释，交给宿主的工厂 |
| `notes` | 写进子代理简报的自由文本 |

**预期结果：** 点名七个技能中的两个，子代理就只拿到那两个，简报里也点名它们；其余五个不存在，若 spawn 索要了超出父级的能力，会在结果里被列为 dropped。

## 预算约定

子代理的 scope 会拿到父级的账本作为**外层账本**，因此树中任何位置的调用都在根上记账。由此有三条结论：

1. 根的 `WithMaxToolCalls` 是整棵树的总上限，不是每个智能体的上限。
2. 派发三个子代理不会把额度分成三份；每个子代理得到的是一个子上限，额度本身在调用期执行。
3. 授权会被夹到「父级剩余额度减一」以内，因此任何根到叶路径上的授权严格递减，且每个至少为一。**即使没有深度限制，深度也必然终止。**

`WithSpawnBudget` 是父级没设调用上限时假定的额度。`WithSubAgentDepth` 才让这棵树好用：根允许 200 次调用时，一条 199 层深的链虽然有界，但没有意义。

**预期结果：** 根上 `WithMaxToolCalls(10)`，父子合计十次成功调用就耗尽整棵树；第十一次被拒绝，消息点名上限与 `ResetToolCallLimit`。

## 查看名册

`Children` 是绑定到 UI 线程的 `ObservableCollection<SubAgentStatusViewModel>`。其他线程读 `Snapshot`，一个不可变的 `IReadOnlyList<SubAgentSummary>`。

| 属性 | 含义 |
|---|---|
| `Id`、`ParentId`、`Depth` | 在树中的位置 |
| `State` | `Queued`、`Running`、`Completed`、`Failed`、`Cancelled` |
| `Result`、`Error` | 答案，或出错原因 |
| `CallCount`、`TokensUsed`、`Duration` | 子代理的消耗 |
| `GrantedSummary` | spawn 要求更少时，收窄后的能力集 |

`SubAgentTreeViewModel` 把名册搭成面板用的树：一个 scope 根、逐节点子级，以及 `TotalCount`、`RunningCount`、`CompletedCount`、`FailedCount`、`CancelledCount`、`SubtreeTokens` 等聚合。

**预期结果：** 两次 spawn 后 `subAgents.Snapshot.Count` 为 `2`；两者都在跑时 `SubAgentTreeViewModel` 的 `RunningCount == 2`。

## 验证

1. 不带模型运行完整程序。它打印深度、spawn 预算、五个工具名与一份空闲名册。
2. 接上真实客户端并提问：「派两个子代理分别列出节点和链接，然后等它们都完成。」预期得到两个句柄、一次等待与两个结果。
3. 在某个子代理完成前取消它；状态变为 `Cancelled`，这不是错误。

## 完整代码

```csharp
using Microsoft.Extensions.AI;
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClientFactory(
        model => throw new NotSupportedException($"Wire a chat client for '{model ?? "(default)"}'."))
    .WithSubAgentDepth(3)
    .WithSpawnBudget(40);

Console.WriteLine($"max depth:    {subAgents.MaxDepth}");
Console.WriteLine($"spawn budget: {subAgents.SpawnBudget}");
Console.WriteLine($"children:     {subAgents.Snapshot.Count}");

foreach (var name in SubAgentAgentToolkit.ToolNames)
    Console.WriteLine($"tool: {name}");

using var roster = new SubAgentTreeViewModel(subAgents);
Console.WriteLine($"idle: {roster.IsIdle}, total: {roster.TotalCount}");
```

## 运行声明

- ⚠️ 未实际运行 —— 仅对照 `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentScope.cs`、`SubAgentAgentToolkit.cs`、`SubAgentStatus.cs`、`SubAgentStatusViewModel.cs`、`SubAgentTreeViewModel.cs`，以及 `Src/Test/Unit/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/` 下的派发与预算测试做了静态核对。派发子代理需要可用的模型，因此没有记录运行输出。
