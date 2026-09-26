# 工作流代理 — 派发子代理

子代理子系统（`VeloxDev.AI.SubAgents`，源码位于 `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/`）让代理能够**在后台派发子代理**。一个子代理是一棵同一棵树上的新 `WorkflowAgentScope`，持有派发者能力的一份**收窄切片**。它的工具调用与推理过程都不会进入派发者的上下文 —— 只有它最终的汇报会 —— 而且它在派发者继续干活的同时运行。

它的形状是**派发 + 轮询**，不是「调用即等待」：`SpawnSubAgent` 立刻返回一个句柄，由 `WaitSubAgents` 收敛结果。这是被运行位置逼出来的 —— 一次 spawn 发生在一次工具调用内部，而工具被编组到**宿主 UI 所拥有的那个线程**上；同步的子代理会按住那个线程走完子代理整段对话。

## 1. 前置条件

本子系统随 `VeloxDev.Core.Extension` 一起提供 —— 除[安装依赖页](../01_安装依赖/index.md)已添加的包之外不需要任何新包。你只需要本快速入门其余部分也需要的那两样东西：一棵运行中的工作流树与一个 `IChatClient`。库自身从不持有聊天客户端，所以子代理跑在哪个模型上是宿主的决定，表现为一个工厂委托。

**预期结果：** 只要包引用已在，下面的代码可对 `VeloxDev.AI.SubAgents` 编译通过。

## 2. 构建子系统

```csharp
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient)  // 子代理与宿主共用同一个模型
    .WithSubAgentDepth(3)                            // 树最多能有多深
    .WithSpawnBudget(64)                             // 未设上限的父所顶替用的额度
    .WithSynchronizationContext(SynchronizationContext.Current);
```

- `SubAgentScope.ForClient(IChatClient, string? instructions = null)` 是库自带的工厂：它把每个子代理构造成 `scope => client.AsAIAgent(scope.CreateContextProviders(), instructions ?? DefaultInstructions).WithPipeline(scope.Pipeline)`。默认前言只有几百字节 —— 刻意不是那份兆字节级的工作流骨架，因为一个后台子代理每轮都从自己的上下文提供器得知它手上有什么。
- `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` 是它背后的公开构造器。当子代理该跑在与派发者不同的模型上时，传入自己的工厂。
- `WithSubAgentDepth(int depth)` 界定树最多能有多深：挂上它的那个作用域的孩子是深度 1，孙代理是深度 2。到达或超过上限的作用域不再有派发能力，并且会**说出来**，而不是静默失败。
- `WithSpawnBudget(int budget)` 设定「宿主从未调用 `WithMaxToolCalls` 时，一次 spawn 假定可用多少」。其默认值是 64。没有它，「父的剩余额度」对不设上限的父就没有定义，而那个保证终止的递减授予也就不存在了 —— 请显式设置，不要依赖默认值。
- `WithSynchronizationContext(SynchronizationContext)` 把名册绑到宿主的 UI 线程；`WithSubAgents` 本来就会从工作流作用域设一次，所以只有当你先配置子系统、后配置作用域时才需要自己调。

**预期结果：** `subAgents.SpawnBudget == 64`、`subAgents.MaxDepth == 3`、`subAgents.Children` 为空。

## 3. 挂到宿主作用域上

```csharp
scope.WithSubAgents(subAgents);
```

最后挂：技能（`WithSkills`）与 MCP 服务器（`WithMcps`）必须在这次调用**之前**配置好，因为收窄在 spawn 那一刻要从父身上读取它们。`WithSubAgents` 是把工作流作用域交给子系统，而不是反过来 —— 它需要父真实的能力去做收窄、需要父的账本去计费，而这两样都要等作用域存在之后才有。

这五个管理工具随后会加入代理每一轮的工具面，并被像内置工具那样包装，所以每一次 spawn 都与其他调用一样被计数、被门禁、被上报：

| 工具 | 必填参数 | 作用 |
|---|---|---|
| `SpawnSubAgent` | `task` | 派发一个子代理，立刻返回其 `id` |
| `WaitSubAgents` | — | 等待点名的 id（或不点名＝等所有在跑的），最长 `timeoutMs`（默认 60000） |
| `GetSubAgentResult` | `id` | 读一个子代理的状态，完成后给出**未截断**的完整汇报 |
| `ListSubAgents` | — | 本作用域发出过的名册，含状态、深度与调用次数 |
| `CancelSubAgent` | `id` | 停止一个在跑的子代理；它以 `Cancelled` 收尾，而不是失败 |

**预期结果：** `scope.SubAgents` 就是你传入的那个实例；这五个名字由 `SubAgentAgentContextProvider` 贡献，**不在** `WorkflowAgentToolkit` 里 —— 没挂子系统的代理一个都不会有。

## 4. 收窄一个子代理能拿到什么

每个能力参数都是可选的，而且**省略意味着继承，不是「什么都不给」**：

| 参数 | 省略 | 传空数组 |
|---|---|---|
| `allowedTools` | 父**当前提供的全部**工具 | 一个工具都不给 |
| `allowedSkills` | 父已开启的全部技能 | 一个都不给，**且技能工具随之一起收走** |
| `allowedMcpServers` | 父已连接且已开启的全部服务器 | 一个都不给 |
| `maxToolCalls` | 父剩余额度里能授予的那么多 | — |
| `maxReadToolCalls` / `maxWriteToolCalls` | 从父继承 | — |
| `allowNodeExecution` | `false` | — |
| `allowedGenericCommands` | 无 | — |
| `autoMarkDirty` | 跟随父的设置 | — |
| `name` | 回退成编号占位（`子代理 N`） | — |
| `notes` | 不加任何东西 | — |

点名（白名单）是**唯一**的收窄手段，也是本子系统核心不变式所在：一个子代理的能力等于其父的能力，或者更少，绝不会更多。spawn 提出而没拿到的，一律**既拒绝、又上报**在回复的 `dropped` 数组里 —— 去读它，因为除此之外没有东西会告诉你。

```jsonc
// SpawnSubAgent("统计节点数", allowedTools: ["ListNodes", "DeleteNode"])
{
  "status": "ok",
  "id": "9f2c…",
  "name": "子代理 1",
  "depth": 1,
  "maxToolCalls": 199,
  "grantedToolCount": 1,
  "grantedSkillCount": 0,
  "grantedMcpServerCount": 0,
  "dropped": ["DeleteNode: not available to this agent, or switched off by the host"],
  "message": "Dispatched, but not with everything you asked for — read \"dropped\". Call WaitSubAgents to collect its report."
}
```

被授予**零个**技能的子代理，会连技能工具（`ListSkills`、`load_skill`、`UnloadSkill`、`read_skill_resource`）一起丢掉 —— 一把背后没有技能可读的 `load_skill` 只会失败。自定义工具按**注册时的分组**随行，于是子代理拿到的用法说明恰好覆盖它持有的工具，而不会包括它没有的。

**预期结果：** 点一个被宿主关掉的工具、或一个根本不存在的工具，都会在 `dropped` 里留下一行；子代理真实持有的面恰好等于回复列出的那份名字。

## 5. 额度是整棵树一口锅

子代理的预算是其父的**份额**，而不是旁边另开的一口锅：子代理的作用域拿父的账本当作自己的外层账本，所以树里任何一处的调用都记在根上，根的上限就是整棵树的上限。授予设定的是**子代理自己子树上的一道子限额**，从不是预留 —— 派三个子代理不会把锅分成三份，而是给每一个各设一道界。

```text
有效上限 = MaxToolCalls ?? SpawnBudget           // 恒为有限值
授予     = min(请求值 ?? 剩余, 剩余 − 1)
剩余     = min(有效上限 − 本层已用, 根上限 − 根已用)
授予 < 1 ⇒ 这次 spawn 被拒绝（不会留下任何行）
```

那个 `− 1` 就是**任意深度仍然终止**的原因：沿任意一条根到叶的路径，授予严格递减且每个都 ≥ 1，所以树的深度不可能超过根的额度。它买到的是终止而不是实用 —— 根允许 200 次调用就允许一条 199 层深的链 —— 这正是 `WithSubAgentDepth` 存在的理由，也是宿主应当把两者都设上的理由：预算是保证，深度上限才是让它可用的东西。

测试里钉住的算术（`SubAgentBudgetTests`、`SubAgentNarrowingTests`、`SubAgentHierarchyTests`）：上限 10 的父对一个索要 20 的子代理授予 9 并上报这次夹取；上限 40 的父沿链授予 39 / 38 / 37；兄弟各自拿到**剩余**，而不是分到锅的一半。

**预期结果：** 当请求的 `maxToolCalls` 超出父的剩余时，回复的 `maxToolCalls` 是实际授予的数，且 `dropped` 里有一行说明这次夹取。

## 6. 收敛、取消、销毁

```csharp
// 模型那一侧 —— 这些就是它调用的工具，顺序与标准文本要求的一致
// SpawnSubAgent(task: "…")             → {"status":"ok","id":"9f2c…", …}
// WaitSubAgents(ids: ["9f2c…"], timeoutMs: 60000)
//   → {"status":"ok","timedOut":false,"agents":[{"id":"9f2c…","state":"Completed","result":"…"}]}
// ListSubAgents()                      → {"status":"ok","count":1,"running":0,"agents":[…]}
// CancelSubAgent(id: "9f2c…")          → {"state":"Cancelled", …}
```

- 超时是信息而不是失败：它返回 `"timedOut": true`，并把仍在跑的子代理标成 `Running`，于是模型可以自己在「再等一次」与「取消」之间决定。优先一次长等待而不是轮询 —— 每次 `WaitSubAgents` 都要花掉模型一次工具调用，而子代理在运行期间一次都不花它的。
- `WaitSubAgents` 每份汇报截断到 4000 字符；`GetSubAgentResult` 给出完整、未截断的那一份。截断标记既写在正文里也写在 `truncated` 字段里，所以只读正文的模型也能分辨完整汇报与被切过的汇报。
- 取消一个已经完成的子代理不改变任何东西。取消自成一档状态 —— 被宿主、被父、或被销毁停掉的子代理并没有出错，一个把它涂成红色的面板会教用户怀疑那个本来工作正常的控件。
- `await subAgents.DisposeAsync()` 取消每一个在跑的子代理并**等待**它们落定。那个等待才是把销毁变成一条边界而不是一场竞态的东西：子代理的工具调用被编组到宿主的 UI 线程上，所以一个在子代理还在飞的时候就拆掉调度器的宿主，会让它们投进一个已经不存在的泵里。销毁之后不再接受新的 spawn。

**预期结果：** 没有任何子代理在跑时调用等待，会立刻返回 `{"count":0,"timedOut":false}` 而不是把超时耗完；对一个已完成的子代理调用 `CancelSubAgent`，返回的仍是 `"state":"Completed"`。

## 7. 把它看起来 —— 树面板

名册是**扁平的、按作用域各持一份**的：它只装该作用域自己发出的孩子，而这恰是让一条分支读不到另一条分支工作的原因。`SubAgentTreeViewModel` 把这些名册投影成一棵可绑定的树：

```csharp
using VeloxDev.AI.SubAgents;

var tree = new SubAgentTreeViewModel(subAgents);  // 绑 Tree（只有一个节点：作用域自身）
// 之后，由你自己的时钟驱动：
tree.TickElapsed();                               // 库自己不持有计时器
```

- 读树的 `Roots`（作用域自己的那些孩子）、它的计数（`TotalCount`、`RunningCount`、`CompletedCount`、`FailedCount`、`CancelledCount`）与 `SubtreeTokens`。
- 在名册线程之外读 `Snapshot`，**不要**读 `Children`。一次 agent 调用会在框架自选的线程上渲染提示词，在那里枚举这个已绑定的 `ObservableCollection` 就是在和宿主的 UI 竞态。
- `Dispose()` 会退订所有作用域，且**不取消任何子代理**。关掉一个面板不是对面板所展示的工作作出的决定。
- 树节点的 `Title` 来自 spawn 的 `name` —— 它是给看面板的人读的任务标题，不是标识符。省略时回退为 `子代理 N`，**按各自的父编号**。

**预期结果：** 一次 spawn 之后 `tree.Roots` 有一个节点，其 `Row.StateText` 在该次运行落定后读到 `已完成`；由这个子代理派出的孙代理挂在它的节点下，而不是并排。

## 8. 完整代码

一个可运行的整体：一棵树上的作用域、一个与宿主共用模型的子代理子系统，以及一轮「让模型去委派」的对话。`tree` 与 `chatClient` 就是前面各页描述的那两个对象。

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using VeloxDev.AI.SubAgents;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

public static class SubAgentQuickStart
{
    public static async Task RunAsync(IWorkflowTreeViewModel tree, IChatClient chatClient)
    {
        var scope = tree.AsAgentScope()
            .WithMaxToolCalls(60)
            .WithAllowNodeExecution(true)
            .WithSynchronizationContext(SynchronizationContext.Current);

        // 挂在「收窄在 spawn 那一刻要从父身上读取的那些能力」之后。
        var subAgents = SubAgentScope.ForClient(chatClient)
            .WithSubAgentDepth(2)
            .WithSpawnBudget(64);
        scope.WithSubAgents(subAgents);

        using var panel = new SubAgentTreeViewModel(subAgents);

        var host = chatClient.AsAIAgent(new ChatClientAgentOptions
        {
            ChatOptions = new ChatOptions
            {
                Instructions = "You are an assistant working on a workflow graph. Use the tools you are given.",
            },
            AIContextProviders = scope.CreateContextProviders(),
        });

        await using (subAgents)
        {
            await host.RunAsync(
                "Work out how many nodes the graph has by dispatching a background sub-agent to count "
                + "them — do not count them yourself. Then wait for it and tell me the number.");

            // 名册是扁平的、按作用域各持一份：本作用域只持有它自己发出的那些孩子。
            foreach (var row in subAgents.Snapshot)
            {
                Console.WriteLine($"{row.Name} [depth {row.Depth}] {row.StateText} " +
                                  $"{row.CallCount} call(s), {row.GrantedToolCount} tool(s), " +
                                  $"tokens {(row.HasTokens ? row.TokensUsed!.Value.ToString() : "unmeasured")}");
                if (row.DroppedRequests.Count > 0)
                    Console.WriteLine("  dropped: " + string.Join(" | ", row.DroppedRequests));
                Console.WriteLine("  " + (row.Result ?? row.Error ?? "(no report yet)"));
            }

            Console.WriteLine($"tree total: {panel.TotalCount} sub-agent(s), {panel.SubtreeTokensText} tokens");
        }
    }
}
```

## 9. 运行声明

- ⚠️ 未实际运行 —— 仅静态核对。本页每个签名都已对照 `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/*.cs` 与 `Agent/Workflow/WorkflowAgentScope.cs` 核实；工具回复与那段算术直接抄自 `VeloxDev.Core.Extension.Test/Agent/SubAgents/` 下的真实断言（`SubAgentDispatchTests`、`SubAgentNarrowingTests`、`SubAgentBudgetTests`、`SubAgentHierarchyTests`、`SubAgentToolSchemaTests`）。组装的程序没有在本次文档撰写中编译或执行，也没有 `API_KEY_DEEPSEEK` 可供跑那几条实时测试。

- 本子系统承接母特性的快速入门顺序：[构建作用域](../02_构建作用域/index.md) → [工具预算与宿主策略](../03_工具预算与宿主策略/index.md) → 本页。
