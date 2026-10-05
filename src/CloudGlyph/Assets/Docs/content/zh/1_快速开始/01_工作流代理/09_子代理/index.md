# 09 · 派发子代理

子代理子系统让一个 agent 派发**后台子代理**，并给每个子代理一份收窄后的自身能力切片。它像 MCP 或技能一样是一个子系统：一次 `With*` 调用挂载它，它便每轮贡献自己的工具与提示文本。

```csharp
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient).WithSubAgentDepth(3);

scope.WithSubAgents(subAgents);   // 必须在 CreateContextProviders() 之前
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

要在 `CreateContextProviders()` **之前**挂载。五个派发工具是作为子系统的上下文提供器的贡献到达模型的，之后挂载会让模型一个都拿不到 —— 子系统无论怎么配置都到不了。深度上限与 `WithMaxToolCalls` 并不重复：预算让树终止，但根允许 200 次调用也允许一条 199 层深的链，有界却无用。三层是 demo 想要的。

**预期结果：** `WithSubAgents` 之前作用域只有一个提供器、没有子代理工具；之后向模型恰好提供 `SpawnSubAgent`、`WaitSubAgents`、`GetSubAgentResult`、`ListSubAgents`、`CancelSubAgent`。

## 1. `SubAgentScope` —— 子系统

| 成员 | 签名 | 说明 |
|---|---|---|
| `ForClient` | `static SubAgentScope ForClient(IChatClient client, string? instructions = null)` | 由 chat client 构建工厂 —— 客户端由宿主拥有，子系统从不拥有。 |
| `SubAgentScope` | `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` | 自定义工厂形式。 |
| `WithSubAgentDepth` | `WithSubAgentDepth(int depth)` | 最大嵌套深度（默认 `int.MaxValue`），钳制 `>= 0`，被子代继承。 |
| `WithSpawnBudget` | `WithSpawnBudget(int budget)` | 未设上限的父级所用的替身额度（默认 64），使递减授予保持有限。 |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | 名册/UI 线程。 |
| `Children` | `ObservableCollection<SubAgentStatusViewModel> { get; }` | 直接子代，最早的在前，作为可绑定行（仅 UI 线程）。 |
| `Snapshot` | `IReadOnlyList<SubAgentSummary> { get; }` | 不可变、线程安全的名册副本 —— 在 UI 线程之外的任何地方读它。 |
| `Version` | `long { get; }` | 单调名册版本；提供器据此缓存渲染。 |
| `Changed` | `event EventHandler?` | `Version` 前进时触发。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | 作用域组合出的提供器。 |
| `DisposeAsync` | `ValueTask DisposeAsync()` | 取消并**等待**每个运行中的子代理，然后清空名册。幂等。 |

## 2. 五个工具

| 工具 | 必需参数 | 用途 |
|---|---|---|
| `SpawnSubAgent` | `task` | 派发一个后台子代理；立即返回其 `id`。 |
| `WaitSubAgents` | —（`ids?`、`timeoutMs?` 默认 60000） | 等待指定/全部运行中的子代理；返回含 `state`、`callCount`、被截断的 `result`（上限 4000，置 `"truncated":true`）、`error`、`dropped` 的行。 |
| `GetSubAgentResult` | `id` | 完整、未截断的报告。 |
| `ListSubAgents` | — | 列出**本作用域自己的**子代理（任务预览截断到 120 字符）；`count` + `running`。 |
| `CancelSubAgent` | `id` | 取消一个子代理；读作 `Cancelled`，而非失败。 |

派发是**派发并轮询，绝非调用并等待** —— 派发发生在宿主 UI 线程的一次工具调用内，因此返回 id，由父级轮询。`SpawnSubAgent` 是唯一必须提供 `task` 的工具；其余能力都可选。来源：`SubAgentToolSchemaTests`。

成功载荷：

```text
{"status":"ok","id":"...","name":"...","depth":1,"maxToolCalls":19,
 "grantedToolCount":67,"grantedSkillCount":7,"grantedMcpServerCount":1,
 "dropped":[],"message":"..."}
```

**预期结果：** 一次派发返回 `status:"ok"`、`id` 与 `depth:1`；稍后对该 id 调用 `WaitSubAgents` 返回 `state:"Completed"` 与子代理的 `result`。

## 3. 能力收窄 —— 父级即天花板

派发携带的每个请求都与父级实际拥有的东西求交，被丢弃的都在派发自身的结果 `dropped` 数组中回报 —— 子代理因此无法相信自己拥有被拒之物。

| 派发参数 | 收窄规则 |
|---|---|
| `allowedTools` | 与父级当前表面求交。省略 ⇒ 继承全部；空数组 ⇒ 一个不给。父级每个**未**授予的工具都在子代理上被关闭。 |
| `allowedSkills` | 与父级已启用技能求交。省略 ⇒ 继承；空数组 ⇒ 一个不给，**且**技能工具也一并移除。父级关闭的技能不可授予。 |
| `allowedMcpServers` | 与父级已加载服务器求交；被授予的服务器到达时**不带**会改变它的加载/卸载/新增开关。 |
| `maxToolCalls` | 钳到父级剩余额度**减一**，授予因此沿每条根到叶路径严格递减（保证终止）。超出剩余的请求会被钳制并回报。 |
| `maxReadToolCalls` / `maxWriteToolCalls` | 请求与父级上限的 `Math.Min`；父级没有的上限不能向下授予。 |
| `allowNodeExecution` | 双方**都**需开启：父级没有时请求被丢弃，而非授予。 |
| `allowedGenericCommands` | 按父级白名单过滤。 |
| `autoMarkDirty` | 从父级继承，绝不超出父级授予。 |

交互配置（安全级别、逐级提示、两个处理器）经 `GrantInteractionTo` 整体传递，因此子代理的 `RequestSelection` / `RequestConfirmation` / `ResetToolCallLimit` 可用，而非只宣称却无效。自定义工具按**仅含子代理实际持有工具的指引**的**子集**复制。来源：`SubAgentNarrowingTests`、`SubAgentCapabilityGrantTests`。

**预期结果：** 点名一个父级已关闭工具的派发把它记入 `dropped`，子代理不持有它；静默派发持有父级的一切。

## 4. 一锅，而非每个 agent 一锅

子代理的额度是父级额度的**一份**，不是它旁边的第二个预算。工具包的 `ToolCallLedger` 是链式的：在子代理的工具包存在之前 `child.ParentLedger = parentLedger`，且 `Spend` 沿链上行，因此最外层账本的总数就是整棵树任意处的调用数。派发三个子代理不会分割这一锅 —— 它约束每一个。§3 中的钳制正是深度有界的来源：根允许 N 会终止一条 N-1 层深的链，故用 `WithSubAgentDepth` 提升可用性。

子代理撞墙时，拒绝把它送往 `ResetToolCallLimit`，**并**告诉它向上报告（有调度器在等它的结果）。重置与父级的一样能到达用户，重开会清零整条链。来源：`SubAgentBudgetTests`（如 `AChildsCalls_AreCountedOnTheRootsLedger`、`AChildsReset_ReachesTheUser_AndReopensTheWholeTree`）。

**预期结果：** 根上限为 6、两个子代理分别授予 3 与 2 时，第二个子代理的拒绝提到**会话的**工具调用预算；总支出保持 6。

## 5. 状态、token 与树面板

`SubAgentState` 为 `Queued`、`Running`、`Completed`、`Failed`、`Cancelled` —— `Cancelled` 是独立取值，不是 `Failed` 的变体。`SubAgentSummary` 是不可变行；`SubAgentStatusViewModel` 是可绑定的（中文 `StateText`、`DurationText`、`TokensText`）。

两个独立的消耗数字：

- **调用向上聚合。** `CallCount` 包含子代理派发的一切。
- **token 向下聚合。** `TokensUsed` / `InputTokens` / `OutputTokens` 是子代理**自身**的消耗；`SubAgentTreeNodeViewModel.SubtreeTokens` 自底向上求和。提供器未报告用量时该数字为 `null` —— 「未测量」，绝不是伪造的 `0`。

`SubAgentTreeViewModel(scope)` 把每个作用域的平坦名册投影成一棵可绑定树（`Roots`、`TotalCount`、`RunningCount`、`FailedCount`、`SubtreeTokens`），就地协调，使展开状态在重建中存活。`TickElapsed()` 刷新耗时 —— 本库不自带计时器，由宿主驱动。

**预期结果：** 树的 `ScopeRoot.SubtreeTokens` 等于所有后代 `TokensUsed` 之和；未报告用量的子代理不显示 token 文本，而非 `0`。

## 运行声明

- ✅ 实际构建并运行 —— 确定性 agent 测试套件（2026-10-01，`已通过! 失败: 0，通过: 387`）包含 `SubAgents/**` 中除 `SubAgentLiveTests` 外的全部。它覆盖收窄规则、一锅账本、深度钳制、派发/轮询契约、取消、token 指标与树视图模型。
- ⚠️ `SubAgentLiveTests`（真实模型派发真实子代理）需要 `API_KEY_DEEPSEEK` 且非确定性；它被**排除**，此处无任何断言依赖它。
