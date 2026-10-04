# 工作流代理 —— 入口：`AgentEx` 与 `AgentClientExtensions`

两个入口把 agent 接到宿主：`AgentEx.AsAgentScope`（树 → 作用域）与 `AgentClientExtensions.AsAIAgent`（chat client + 提供器 → agent）。

## AgentEx

`public static class AgentEx` —— 命名空间 `VeloxDev.AI.Workflow`；源 `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `AsAgentScope` | `WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` | 创建绑定该树的 `WorkflowAgentScope`。唯一入口 —— 没有树就无法使用作用域。 |

## AgentClientExtensions

`public static class AgentClientExtensions` —— 命名空间 `VeloxDev.AI`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `AsAIAgent` | `ChatClientAgent AsAIAgent(this IChatClient chatClient, IReadOnlyList<AIContextProvider> providers, string? instructions = null)` | 构建挂载了提供器的 `ChatClientAgent`。`chatClient` 为 null 时抛 `ArgumentNullException`。 |

**刻意没有 `tools` 参数**：上下文提供器是唯一的工具来源，因此同一工具绝不会同时经 `ChatOptions.Tools` 与提供器注册（框架对二者做并集且不去重）。提供器在前的参数顺序正是用来避免与框架自带 `AsAIAgent` 重载冲突的。只传 `instructions` 的调用绑定到框架重载 —— 由 `AgentClientExtensionsTests.AsAIAgent_WithASingleString_BindsToTheFrameworkOverload` 测试。

## 接线

```csharp
using VeloxDev.AI.Workflow;

// 1. 树 -> 作用域
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithAllowNodeExecution(true)
    .WithMaxToolCalls(200)
    .WithTranscript(transcript);

// 2. 作用域 -> agent —— 便捷重载：
var agent = chatClient.AsAIAgent(scope.CreateContextProviders(), scope.ProvideProgressiveContextPrompt());

// ...或写全并挂上管线，这是 demo 的做法：
var agent2 = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);
```

来源：`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`（`ProvideAgent`）。

> **`AsAIAgent(new ChatClientAgentOptions{...})` 来自 `Microsoft.Agents.AI`，不是 VeloxDev** —— 但 `WithPipeline`（来自 `VeloxDev.AI.Pipelines.AgentPipelineExtensions`）与 `AsAIAgent(client, providers, instructions)`（来自 `AgentClientExtensions`）是。VeloxDev 贡献作用域、工具与提供器；会话本身由 `Microsoft.Agents.AI` 在 `Microsoft.Extensions.AI` 之上托管。

**预期结果：** `scope.CreateContextProviders()` 至少产出 workflow 提供器；把它传给 `AsAIAgent` 得到一个 `AIAgent`，其指令是作用域的提示、其工具列表逐轮渲染。
