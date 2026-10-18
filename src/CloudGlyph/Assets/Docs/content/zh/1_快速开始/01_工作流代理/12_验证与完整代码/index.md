# 12 · 验证与完整代码

## 1. 按证据覆盖

| 领域 | Demo | 测试 |
|---|---|---|
| 作用域流式表面 + 上下文提示 | `AgentHelper.ProvideAgent` | `WorkflowAgentContextProviderTests`、`ComposedProvidersTests`、`CapabilityEnvelopeTests`、`AgentCapabilityProvidersTests` |
| 66 个分类工具、类别、开关 | — | `ToolSwitchTests`、`WorkflowLifecycleFidelityTests`、`NodeGeometryToolTests`、`WorkflowSerializationTests` |
| 预算 + `ResetToolCallLimit` | `WithMaxToolCalls(200)` | `BudgetResetTests`、`SubAgentBudgetTests`、`ComposedProvidersTests` |
| 权限模式与规则 | `WithPermissionMode` / `WithPermissionRule` | `AgentPermissionPolicyTests` |
| 线程亲和 | `WithSynchronizationContext` | `ToolThreadAffinityTests` |
| 编译运行 + 运行句柄 | — | `CompiledRunControlTests` |
| MCP | `Mcp` / `McpServers` / `Options` | `MCP/**`（上下文提供器、工具包、远程、开关） |
| 技能 | `.WithSkills("skills")` | `Skills/**` |
| 子代理 | `SubAgentScope.ForClient(...).WithSubAgentDepth(3)` | `SubAgents/**`（除 live 文件） |
| 管线 + 对话记录 | `Transcript`、`WithPipeline` | `Pipelines/**` |
| 仪表盘 | — | `Dashboard/AgentDashboardViewModelTests` |
| `VeloxDev.AI` 反射辅助 | — | `VeloxDev.Core.Test/AI/*`（7 个文件） |

刻意**不**计入的一个文件是 `Agent/SubAgents/SubAgentLiveTests.cs`：它需要真实模型密钥（`API_KEY_DEEPSEEK`）且非确定性（一个测试最多采样三次），无密钥时报告 `Inconclusive`，本页从不把它当证据。

## 2. 完整代码

一个宿主：构建作用域、挂载子系统、运行一轮。每个标识符都在本块中定义或可追溯到真实文件；没有省略号。`tree` 是「工作流系统」特性构建的 workflow 树；`chatClient` 是任意 `IChatClient`。

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using OpenAI;
using System;
using System.ClientModel;
using System.Threading;
using VeloxDev.AI;
using VeloxDev.AI.MCP;
using VeloxDev.AI.Pipelines;
using VeloxDev.AI.Safety;
using VeloxDev.AI.SubAgents;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

public static class AgentHost
{
    // 'tree' 由「工作流系统」特性构建；本宿主只拥有它上面的 agent。
    public static async Task RunAsync(IWorkflowTreeViewModel tree, CancellationToken cancellationToken = default)
    {
        var apiKey = Environment.GetEnvironmentVariable("API_KEY_DEEPSEEK");
        if (string.IsNullOrWhiteSpace(apiKey))
            throw new InvalidOperationException("Environment variable 'API_KEY_DEEPSEEK' is not configured.");

        var chatClient = new OpenAIClient(
            new ApiKeyCredential(apiKey),
            new OpenAIClientOptions { Endpoint = new Uri("https://api.deepseek.com") })
            .GetChatClient("deepseek-v4-flash")
            .AsIChatClient();

        var transcript = new AgentTranscript();
        var mcp = new McpScope();
        mcp.WithServers(new McpServerConfiguration
        {
            Name = "Filesystem",
            RunMode = McpServerRunMode.Npx,
            Package = "@modelcontextprotocol/server-filesystem",
            Arguments = [AppContext.BaseDirectory],
        });

        var subAgents = SubAgentScope.ForClient(chatClient).WithSubAgentDepth(3);

        var scope = tree.AsAgentScope()
            .WithPromptLanguage(AgentLanguages.English)
            .WithOutputLanguage(AgentLanguages.Chinese)
            .WithAutoDiscovery()
            .WithAutoMarkDirty(false)
            .WithMaxToolCalls(200)
            .WithMaxReadToolCalls(120)
            .WithMaxWriteToolCalls(80)
            .WithAllowNodeExecution(true)
            .WithSynchronizationContext(SynchronizationContext.Current)
            .WithToolCallCallback(args =>
            {
                Console.WriteLine($"tool {args.ToolName} (count {args.CallCount})");
                return Task.CompletedTask;
            })
            .WithSelectionHandler(args =>
            {
                args.SelectedOption = args.Options.Count > 0 ? args.Options[0] : null;
                return Task.CompletedTask;
            })
            .WithConfirmationHandler(args =>
            {
                args.Result = AgentConfirmationResult.AllowOnce;
                return Task.CompletedTask;
            })
            .WithPermissionMode(AgentPermissionMode.AutoEdit)
            .WithSkills("skills")
            .WithMcps(mcp)
            .WithSubAgents(subAgents)
            .WithTranscript(transcript);

        var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
        {
            ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
            AIContextProviders = scope.CreateContextProviders(),
        }).WithPipeline(scope.Pipeline);

        var session = await agent.CreateSessionAsync();
        var reply = await agent.RunAsync("List the nodes in the workflow, then add one node of type Demo.ViewModels.NetworkRequest.", session, cancellationToken: cancellationToken);

        Console.WriteLine(reply.Text);
        Console.WriteLine(transcript.ToMarkdown());
    }
}
```

符号追溯：`AsAgentScope`（`Src/Core/VeloxDev.Core.Extension/AgentEx.cs`）、`With*` 链（`WorkflowAgentScope.cs`）、`SubAgentScope.ForClient`（`SubAgentScope.cs`）、`McpServerConfiguration` / `McpServerRunMode`（`Agent/MCP/`）、`WithPipeline`（`AgentPipelineExtensions`）、`AgentTranscript`，以及 OpenAI 客户端构造（`AgentHelper.cs`，`ProvideAgent`）。

## 3. 构建与运行

```bash
dotnet build
dotnet run
```

**预期结果：** 进程无错误构建。有有效 `API_KEY_DEEPSEEK` 时模型作答，并打印回复与对话记录（含工具调用）；没有密钥时宿主在任何网络调用前抛出点名该变量的 `InvalidOperationException`。`skills` 文件夹允许不存在 —— 内嵌技能语料仍会到达。

## 运行声明

- ⚠️ **未端到端运行** —— 对话需要真实 `IChatClient` 与 API key，当前不可用。本页程序**未**按原样编译或执行。
- ⚠️ **本次修订未运行** —— 2026-10-18 对照当前源码静态核验。曾有一次 2026-10-01 的确定性测试记录（`失败: 0，通过: 387`），但它早于权限模式 / 上下文树重构；本页 API 是读源码核验的，不是执行程序验证的。

`SubAgentLiveTests` 在早先那次运行中被刻意排除（需要 `API_KEY_DEEPSEEK`，非确定性）。不要把那次运行当作上面示例可运行的证明。
