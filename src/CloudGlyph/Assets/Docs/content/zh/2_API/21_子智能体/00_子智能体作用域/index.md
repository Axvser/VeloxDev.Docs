# SubAgentScope

`VeloxDev.AI.SubAgents.SubAgentScope : IAsyncDisposable` 是一个作用域派出的子代理注册表、管理它们的工具，以及让子级保持在父级能力内的收窄规则。

## 挂载到工作流作用域

| 成员 | 签名 | 说明 |
|---|---|---|
| `WithSubAgents` | `WorkflowAgentScope WithSubAgents(SubAgentScope subAgents)` | 注册子系统的上下文 provider。**必须在 `CreateContextProviders()` 之前挂载**；之后挂载会让模型拿不到五个派发工具。 |
| `SubAgents` | `SubAgentScope? SubAgents { get; }` | 已挂载的子系统，或 `null`。 |

## 创建子系统

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` | 工厂接收子级作用域并返回在其上的可运行智能体。 |
| 构造函数 | `SubAgentScope(Func<WorkflowAgentScope, string?, AIAgent> agentFactory, string? instructions = null)` | 工厂还接收 spawn 请求的模型名，或 `null`。 |
| `ForClient` | `static SubAgentScope ForClient(IChatClient client, string? instructions = null)` | 子代理是在一个客户端上的智能体，共享宿主模型。 |
| `ForClientFactory` | `static SubAgentScope ForClientFactory(Func<string?, IChatClient> clientFactory, string? instructions = null)` | 按请求的模型为每次 spawn 选择客户端。工厂抛出即拒绝该 spawn，拒绝作为子级失败回到派发方。 |

库自己不持有聊天客户端。子代理用哪个模型是宿主的决定，因此工厂是构造函数的核心。

## 名册与版本

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `Children` | `ObservableCollection<SubAgentStatusViewModel>` | 已派出的子代理，最旧在前，作为可绑定行。 |
| `Snapshot` | `IReadOnlyList<SubAgentSummary>` | 不可变副本，在子代理变化时于名册线程重新发布。绑定线程外读它。 |
| `Version` | `long` | 名册及其行的单调版本号；provider 基于它缓存渲染。 |
| `Changed` | `event EventHandler` | `Version` 推进时触发。 |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | 每轮贡献派发工具与名册的 provider。 |

## 限制

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `SpawnBudget` | `int SpawnBudget { get; }` | 父级未设置 `WithMaxToolCalls` 时假定的额度。没有它，未设上限的父级「剩余额度」就没有定义。 |
| `WithSpawnBudget` | `SubAgentScope WithSpawnBudget(int budget)` | 设置 `SpawnBudget`。被其下派生的每个作用域继承。 |
| `MaxDepth` | `int MaxDepth { get; }` | 子代理可坐的最深位置：直接子级深度为 1。达到或超过限制的作用域不能再派生。 |
| `WithSubAgentDepth` | `SubAgentScope WithSubAgentDepth(int depth)` | 限制树深。在此作用域之下继承。 |
| `WithSynchronizationContext` | `SubAgentScope WithSynchronizationContext(SynchronizationContext? context)` | 名册绑定的 UI 线程。 |

预算已经让树终止。深度限制让它*可用*：根允许 200 次调用时允许 199 层链，有界但无意义。两者都应设置。

## 释放

| 成员 | 签名 | 说明 |
|---|---|---|
| `DisposeAsync` | `ValueTask DisposeAsync()` | 取消每个运行中的子代理并等待其安定。等待使释放成为边界而非竞态。 |

## 预算契约

子级作用域接收父级账本作为其**外层账本**，因此树中任何位置的每次调用都在根处记账。

1. 根的 `WithMaxToolCalls` 是整棵树的总上限，不是逐智能体上限。
2. 派生三个子代理不会分割额度；每个子代理获得一个子限额，额度在调用时强制。
3. 授权被钳制为至多父级剩余额度减一，因此沿任意根到叶路径授权严格递减且每个授权至少为一。即使没有深度限制，深度也因此终止。

## 子代理继承什么

不请求任何东西的 spawn 获得父级当前提供的一切：相同工具、技能与 MCP 服务器，包括继续派发的能力。请求更小集合的 spawn 获得**交集**——绝不会多于父级拥有。超出部分的请求被丢弃并在 spawn 结果中回报。`AutoEdit` 父级的子级继承 `AutoEdit`；它不会误以为自己持有父级被拒绝的能力。

## 示例

```csharp
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient)
    .WithSubAgentDepth(3)
    .WithSpawnBudget(40);

scope.WithSubAgents(subAgents);
var providers = scope.CreateContextProviders();
```

## 相关

- [派发工具](../01_派发工具/index.md) —— 子代理可以被要求做什么。
- [名册](../02_名册/index.md) —— 观察子代理。
