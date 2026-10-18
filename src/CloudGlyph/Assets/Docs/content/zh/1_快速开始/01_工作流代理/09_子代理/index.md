# 09 · 派发子代理

子代理子系统让一个 agent 派发**后台子代理**，并给每个子代理一份自己能力的收窄切片。它和 MCP、技能一样是子系统：一次 `With*` 调用挂载，每轮贡献自己的工具与提示文本。

```csharp
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient).WithSubAgentDepth(3);

scope.WithSubAgents(subAgents);   // 在 CreateContextProviders() 之前挂载
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

必须在 `CreateContextProviders()` **之前**挂载。五个派发工具作为子系统的上下文提供器贡献到达，晚挂载会让模型一个都拿不到 —— 无论子系统配置得多完整都不可达。深度限制与 `WithMaxToolCalls` 并不重复：预算让树终止，但允许 200 次调用的根也允许 199 层深的链，那是有界却无用的。三层是示例想要的。

**预期结果：** 未调用 `WithSubAgents` 时作用域只有一个提供器、没有子代理工具；调用后模型恰好拿到 `SpawnSubAgent`、`WaitSubAgents`、`GetSubAgentResult`、`ListSubAgents`、`CancelSubAgent`。

## 1. `SubAgentScope` —— 子系统

| 成员 | 签名 | 说明 |
|---|---|---|
| `ForClient` | `static SubAgentScope ForClient(IChatClient client, string? instructions = null)` | 从 chat client 构建工厂 —— 客户端归宿主所有，子系统从不拥有它。 |
| `SubAgentScope` | `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` | 自定义工厂形式。 |
| `WithSubAgentDepth` | `WithSubAgentDepth(int depth)` | 最大嵌套深度（默认 `int.MaxValue`）；下限裁剪到 `>= 0`；由子代理继承。 |
| `WithSpawnBudget` | `WithSpawnBudget(int budget)` | 当父作用域没有 `WithMaxToolCalls` 时的额度假设（默认 64），让向下授予保持有限。 |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | 名册/UI 线程。 |
| `Children` | `ObservableCollection<SubAgentStatusViewModel> { get; }` | 直接子代理，最旧在前，作为可绑定行（仅 UI 线程）。 |
| `Snapshot` | `IReadOnlyList<SubAgentSummary> { get; }` | 名册的不可变、线程安全副本 —— 在 UI 线程之外读它。 |
| `Version` | `long { get; }` | 单调名册版本；提供器据此缓存渲染。 |
| `Changed` | `event EventHandler?` | `Version` 前进时触发。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | 作用域组合的提供器。 |
| `DisposeAsync` | `ValueTask DisposeAsync()` | 取消并**等待**每个运行中的子代理，然后清空名册。幂等。 |

## 2. 五个工具

| 工具 | 必需参数 | 用途 |
|---|---|---|
| `SpawnSubAgent` | `task` | 派发后台子代理；立即返回其 `id`。 |
| `WaitSubAgents` | —（`ids?`、`timeoutMs?` 默认 60000） | 等待指定/全部运行中的子代理；返回带 `state`、`callCount`、截断的 `result`（上限 4000，`"truncated":true`）、`error`、`dropped` 的行。 |
| `GetSubAgentResult` | `id` | 完整、未截断的报告。 |
| `ListSubAgents` | — | 列出**本作用域自己的**子代理（任务预览截断到 120 字符）；`count` + `running`。 |
| `CancelSubAgent` | `id` | 取消子代理；读作 `Cancelled`，不是失败。 |

派发是**派发后轮询，绝不是调用后等待** —— spawn 发生在宿主 UI 线程上的工具调用内，因此它返回 id，由父代理轮询。`SpawnSubAgent` 是唯一以 `task` 为必需参数的工具；其余能力都是可选的。来源：`SubAgentToolSchemaTests`。

成功载荷：

```text
{"status":"ok","id":"...","name":"...","depth":1,"maxToolCalls":19,
 "grantedToolCount":67,"grantedSkillCount":7,"grantedMcpServerCount":1,
 "dropped":[],"message":"..."}
```

**预期结果：** spawn 返回带 `id` 与 `depth:1` 的 `status:"ok"`；之后对该 id 调 `WaitSubAgents` 返回 `state:"Completed"` 与子代理的 `result`。

## 3. 能力收窄 —— 父作用域是天花板

spawn 携带的每个请求都与父代理**实际拥有的东西求交**，被丢弃的项在 spawn 自己的 `dropped` 数组里报告 —— 子代理不能相信自己持有被拒绝的能力。

| Spawn 参数 | 收窄规则 |
|---|---|
| `allowedTools` | 与父代理当前表面对交。省略 ⇒ 全部继承；空数组 ⇒ 一个都不授予。父代理**未**授予的每个工具都会在子代理上关闭。 |
| `allowedSkills` | 与父代理已启用的技能求交。省略 ⇒ 继承；空数组 ⇒ 一个都不授予，**并且**连技能工具一起去掉。父代理关闭的技能不可授予。 |
| `allowedMcpServers` | 与父代理已加载服务器求交；被授予的服务器**不带**会改变它的 load/unload/add 开关。 |
| `maxToolCalls` | 裁剪到父代理剩余额度**减一**，因此授予沿每条根到叶路径严格递减（保证终止）。超出剩余额度的请求会被裁剪并报告。 |
| `maxReadToolCalls` / `maxWriteToolCalls` | 请求与父代理上限的 `Math.Min`；父代理没有的上限不能下传。 |
| `allowNodeExecution` | **两侧**都要选择加入：父代理没有时请求会被丢弃，而不是授予。 |
| `allowedGenericCommands` | 按父代理白名单过滤。 |
| `autoMarkDirty` | 从父代理继承，绝不授予超出它的能力。 |

交互配置（权限模式、规则、judge、模式提示与两个处理器）整份经 `GrantInteractionTo` 传递，因此子代理的 `RequestSelection` / `RequestConfirmation` / `ResetToolCallLimit` 可用，而不是只被宣传却无法调用。自定义工具以**子集**复制，且只带子代理实际持有工具的指引。来源：`SubAgentNarrowingTests`、`SubAgentCapabilityGrantTests`。

**预期结果：** 点名一个被父代理关闭的工具时，spawn 在 `dropped` 中报告它，且子代理不持有它；不点名任何能力的 spawn 持有父代理的一切。

## 4. 一锅账本，不是每个 agent 一份

子代理的额度是**父代理额度的一份**，而不是它旁边另开的预算。工具包的 `ToolCallLedger` 是链式的：子工具包存在之前先设 `child.ParentLedger = parentLedger`，`Spend` 沿链行走，因此最外层账本的总数就是整棵树任何位置发生的调用数。派发三个子代理不会分割这锅预算 —— 它给每个子代理设界。§3 的裁剪正是深度有界的原因：允许 N 次的根终结 N-1 层深的链，因此才有 `WithSubAgentDepth` 来保证可用性。

当子代理撞墙时，拒绝会把它引向 `ResetToolCallLimit` **并且**告诉它向上报告（有派发者正挂起等待它的结果）。重置对用户的触达与父代理完全一样，重新打开会清零整条链。来源：`SubAgentBudgetTests`（如 `AChildsCalls_AreCountedOnTheRootsLedger`、`AChildsReset_ReachesTheUser_AndReopensTheWholeTree`）。

**预期结果：** 根上限为 6、两个子代理分别授予 3 与 2 时，第二个子代理的拒绝提到**会话**的工具调用预算；总消耗保持 6。

## 5. 状态、token 与树面板

`SubAgentState` 为 `Queued`、`Running`、`Completed`、`Failed`、`Cancelled` —— `Cancelled` 是独立取值，不是 `Failed` 的一种。`SubAgentSummary` 是不可变行；`SubAgentStatusViewModel` 是可绑定行（`StateText` 为中文、`DurationText`、`TokensText`）。

两个不同的消耗数字：

- **调用向上汇总。** `CallCount` 包含子代理派发的一切。
- **Token 向下汇总。** `TokensUsed` / `InputTokens` / `OutputTokens` 是子代理**自己**的花费；`SubAgentTreeNodeViewModel.SubtreeTokens` 自底向上求和。不报告用量的提供器让数字保持 `null` —— “未测量”，绝不是伪造的 `0`。

`SubAgentTreeViewModel(scope)` 把各作用域的扁平名册投影成一棵可绑定树（`Roots`、`TotalCount`、`RunningCount`、`FailedCount`、`SubtreeTokens`），就地协调，展开状态在重建后保留。`TickElapsed()` 刷新耗时 —— 库不拥有计时器，由宿主驱动。

**预期结果：** 树的 `ScopeRoot.SubtreeTokens` 等于每个后代 `TokensUsed` 之和；不报告用量的子代理不显示 token 文本，而不是 `0`。

## 运行声明

- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。`SubAgents/**` 测试存在且在 2026-10-01 的一次记录运行（387 项）中通过，但该运行早于权限模式重构，不作为当前证据。
- ⚠️ `SubAgentLiveTests`（真实模型派发真实子代理）需要 `API_KEY_DEEPSEEK` 且非确定性；它被**排除**，本页没有任何结论依赖它。
