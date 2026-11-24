# 上下文提供器

`VeloxDev.AI.SubAgents.SubAgentAgentContextProvider : AIContextProvider` 把子系统贡献给智能体调用：告诉模型如何派发子代理、五个派发工具，以及——对于本身是被派生的智能体——它自己派发的事实。

## 类：SubAgentAgentContextProvider

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `SubAgentAgentContextProvider(SubAgentScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | 为子系统创建 provider。独立使用可省略 `tools`；此时从父作用域的同步上下文派生线程策略。 |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | provider 的状态键。 |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | 渲染并贡献子智能体状态。 |

渲染基于作用域 `Version` 缓存；名册或任一行变化时它都会推进，因此子代理完成会在下一轮到达模型而无需重建智能体。

## 说明

- **没有语言维度。** 子系统自己的文本用两种语言各写一份，而不跟随工作流提示语言，因为子代理简报由模型读取，而非用户。
- **在创建 provider 之前挂载。** `scope.WithSubAgents(...)` 必须在 `CreateContextProviders()` 之前执行。之后挂载会让模型拿不到五个工具。
- **传入宿主的工具策略。** 组合宿主传入与其他来源相同的 `ToolPipeline`，因此 spawn 计入同一预算。仅在手工组装 provider 时省略。

## 示例

```csharp
scope.WithSubAgents(subAgents)
     .WithSynchronizationContext(SynchronizationContext.Current);

var providers = scope.CreateContextProviders();
```

## 相关

- [SubAgentScope](../00_子智能体作用域/index.md) —— 此 provider 渲染的子系统。
- [派发工具](../01_派发工具/index.md) —— 它贡献的工具。
- [技能工具](../../19_智能体上下文与技能/04_技能工具/index.md) —— 另一个子系统的同一 provider 模式。
