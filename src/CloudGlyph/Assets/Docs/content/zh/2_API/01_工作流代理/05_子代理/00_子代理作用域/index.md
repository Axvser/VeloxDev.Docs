# 工作流代理 — 子代理：`SubAgentScope`

`public sealed class SubAgentScope : IAsyncDisposable` —— 子代理子系统：一个作用域派发过的代理的注册表、管理它们的工具，以及把孩子约束在父能力之内的收窄规则。声明于 `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentScope.cs`。

| 成员 | 签名 | 备注 |
|---|---|---|
| `SubAgentScope` | `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` | 用 `agentFactory` 构建每个子代理。为 `null` 时抛 `ArgumentNullException`。`instructions` 是孩子的常驻前言；省略时用一段精简默认值。 |
| `ForClient` | `static SubAgentScope ForClient(IChatClient client, string? instructions = null)` | 子代理跑在 `client` 上、与宿主共用模型的子系统。`client` 为 `null` 时抛 `ArgumentNullException`。 |
| `SpawnBudget` | `int { get; }` | 父作用域未调用 `WithMaxToolCalls` 时，一次 spawn 假定的额度。**默认 64。** 会被其下每个被派发的作用域继承。 |
| `WithSpawnBudget` | `SubAgentScope WithSpawnBudget(int budget)` | 设置 `SpawnBudget`，下限夹到 1。返回 `this`。 |
| `MaxDepth` | `int { get; }` | 被派发的代理最多能坐多深；所挂作用域的孩子是深度 1。**默认 `int.MaxValue`。** |
| `WithSubAgentDepth` | `SubAgentScope WithSubAgentDepth(int depth)` | 界定树最多能有多深，下限夹到 0。返回 `this`。 |
| `WithSynchronizationContext` | `SubAgentScope WithSynchronizationContext(SynchronizationContext? context)` | 名册所绑的线程；`null` 表示在 spawn 或完成所在的任意线程上写。返回 `this`。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | 构建每轮贡献管理工具与名册的提供器。独立使用时省略 `tools` —— 提供器会从父作用域的上下文推导出一份只管线程的策略。 |
| `Children` | `ObservableCollection<SubAgentStatusViewModel> { get; }` | 本作用域派发的子代理，最旧在前，作为可绑定的行。**绑在名册线程上。** |
| `Snapshot` | `IReadOnlyList<SubAgentSummary> { get; }` | `Children` 的不可变副本，任何一个孩子变化时在名册线程上重发。在别处读**这个**，不要读 `Children`。 |
| `Version` | `long { get; }` | 名册及其行的单调版本号；上下文提供器据此缓存渲染结果。 |
| `Changed` | `event EventHandler?` | `Version` 前进时触发。 |
| `DisposeAsync` | `ValueTask DisposeAsync()` | 取消每个在跑的孩子并等待它们落定，然后退订所有行。幂等。 |

## 构造

`ForClient` 是库提供的工厂；它的实现就是那份被记录下来的自定义工厂形状，所以想让子代理跑在别的模型上的宿主照写同一个 lambda 即可：

```csharp
// ForClient 的形状，逐字对照 —— SubAgentScope.cs 第 160-166 行
scope => client
    .AsAIAgent(scope.CreateContextProviders(), instructions ?? DefaultInstructions)
    .WithPipeline(scope.Pipeline)
```

默认前言是 `SubAgentScope.DefaultInstructions`（**internal**）：几百个字节，告诉孩子它是被另一个代理派到后台去做一件具体的事、应当自己判断并推进而不是发问、手上的工具就是它可用的全部。它刻意**不是**那份工作流骨架 —— 那是一份按作用域算兆字节的东西。

> `SubAgentScope.DefaultInstructions` 是 `internal const string` —— 已对照 `SubAgentScope.cs` 第 173-179 行核实。宿主读不到它，只能依赖 `ForClient`。**没有任何测试断言过它的文字或长度** —— 上面那段描述是读那个常量*推断*出来的（*推断所得*），不是某个测试钉住的行为。被钉住的是「默认前言在场时 spawn 依然能跑通」（`SubAgentToolSchemaTests.ASpawnThatNamesOnlyItsTask_IsAccepted` 用 `ForClient` 的默认值走了一次真实 spawn）。

## 挂载与身份

`Attach(WorkflowAgentScope parent)` 是 **internal**，由 `WorkflowAgentScope.WithSubAgents` 调用。宿主对它无事可做；效果是 `SubAgentScope.Parent`（internal）不再为 null，`CreateContextProvider()` 开始有内容。先建提供器、后挂载是被容忍的：`SubAgentAgentContextProvider.BuildContext()` 返回空的 `AIContext`（`Instructions` 与 `Tools` 均为 null）而不是抛异常 —— `SubAgentHierarchyTests.AnUnattachedSubsystem_ContributesNothing` 钉住这条。

每个实例带一个 internal 的 `InstanceId`（一个 `Guid`，**不是**工作流作用域那个 `StateDiscriminator`）。后者派生自树，而父与子坐在**同一棵**树上，于是它恰好会在唯一一对绝对不能撞的提供器上撞。`SubAgentHierarchyTests.TwoScopes_NeverShareAStateKey` 与 `TwoProvidersOverOneScope_DoShareAKey` 把两个方向都钉住。

## spawn 与额度

`TrySpawn(SubAgentRequest request, out string? refusal)` 是 **internal** —— 模型只经 `SpawnSubAgent` 触达它。它的算术：

| 步骤 | 规则 | 行 |
|---|---|---|
| 销毁闸 | `DisposeAsync` 跑过之后一律拒绝 | 394-397 |
| 深度闸 | `Depth >= MaxDepth` 时拒绝；拒绝文案点名这个上限 | 399-404 |
| 剩余 | `min((parent.MaxToolCalls ?? SpawnBudget) - ledger.Usage.ToolCalls, rootCap - rootUsage)` | 694-706 |
| 授予 | `min(request.MaxToolCalls ?? remaining, remaining - 1)`；小于 1 时这次 spawn **被拒绝**，而不是授予 0 | 409-417 |
| 夹取上报 | 请求的额度高于授予值时，向 `dropped` 加一行 `maxToolCalls` | 418-419 |

`SubAgentRequest`（internal）与 `SpawnSubAgent` 的参数一一对应。每个收窄字段都是**可空的，而可空意味着继承**：`null` 继承，空数组什么也不给，点名是唯一的减法。`AllowedSkills` 与 `AllowedMcpServers` 共用同一个默认值 —— 父已开启的那一套。

由于授予永远比父的剩余至少少一，沿任意根到叶路径授予严格递减，于是任意深度的树都会终止，且深度不可能超过根的额度。`SubAgentBudgetTests` 与 `SubAgentHierarchyTests` 把它写成算术断言（`10 → 9`；`40 → 39 → 38 → 37`）。终止不等于可用：根允许 200 次调用就允许一条 199 层深的链 —— 这正是 `WithSubAgentDepth` 存在的理由。

## 工具背后的操作

| 成员 | 签名 | 行为 |
|---|---|---|
| `List` | `IReadOnlyList<SubAgentSummary> List()` —— internal | 先按每个孩子的账本刷新调用次数，再重发名册并返回快照。 |
| `GetResult` | `SubAgentSummary? GetResult(string id)` —— internal | 一个孩子的当前状态；本作用域从未发出过该句柄时返回 `null`。 |
| `WaitAsync` | `Task<(IReadOnlyList<SubAgentSummary> Rows, bool TimedOut)> WaitAsync(string[]? ids, int timeoutMs)` —— internal | 对点名孩子做 `Task.WhenAll` 并与一个延迟赛跑；是否超时靠**引用比较**判定，因为两个任务都会成功完成。 |
| `Cancel` | `SubAgentSummary? Cancel(string id)` —— internal | 取消一个在跑的孩子；由孩子自己的 catch 落定那一行。 |
| `SubAgentsOf` | `SubAgentScope? SubAgentsOf(string id)` —— internal | 一行所代表的孩子的子系统 —— 树走的那条边。 |

句柄表是**按作用域私有**的：`Select`/`Find` 只看本作用域自己的条目，所以一个本作用域从未发出过的 id 会被**跳过**而不是拒绝。模型点名了兄弟的孩子，会拿到空名册而不是窥进另一条分支 —— `SubAgentDispatchTests.AChildSeesItsOwnChildren_AndNobodyElses` 钉住这条。

`SubAgentsOf` 就是把扁平名册接到树上的那条线：记录按作用域各持一份 —— 这正是让孩子看不到兄弟的原因，因为它只读自己那一份 —— 所以一行无法靠查找来指认自己的父。创建子作用域的那次 spawn 把自己的行 id 写进子作用域的 internal `SelfId`，此后该作用域的每个孩子都指向它。于是树**只凭行**就能建起来。

## 销毁

`DisposeAsync` 取消每个在跑的孩子并**等待**每次运行，然后退订所有行并清空 `Children`。之所以等待而不是发出去就算：孩子的工具调用被编组到宿主的 UI 线程上，一个在子代理还在飞的时候就拆掉调度器的宿主，会让它们投进一个已经不存在的泵里。销毁之后不再接受新的 spawn（`SubAgentDispatchTests.AfterDisposal_NothingMoreCanBeSpawned`），第二次调用无害（`DisposingTwice_IsHarmless`）。

> 源码：`SubAgentScope.cs`。测试：`Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/` 下的 `SubAgentDispatchTests`、`SubAgentBudgetTests`、`SubAgentHierarchyTests`、`SubAgentNarrowingTests`。
