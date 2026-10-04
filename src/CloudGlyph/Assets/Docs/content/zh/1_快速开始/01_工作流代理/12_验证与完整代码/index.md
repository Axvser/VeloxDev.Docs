# 12 · 验证与完整代码

## 1. 证据覆盖清单

| 领域 | Demo | 测试 |
|---|---|---|
| 作用域流式表面 + 上下文提示 | `AgentHelper.ProvideAgent` | `WorkflowAgentContextProviderTests`、`ComposedProvidersTests`、`CapabilityEnvelopeTests`、`AgentCapabilityProvidersTests` |
| 68 个工具、类别、开关 | — | `ToolSwitchTests`、`WorkflowLifecycleFidelityTests`、`NodeGeometryToolTests`、`WorkflowSerializationTests` |
| 预算 + `ResetToolCallLimit` | `WithMaxToolCalls(200)` | `BudgetResetTests`、`SubAgentBudgetTests`、`ComposedProvidersTests` |
| 工具审批 | — | `ToolApprovalTests` |
| 线程亲和 | `WithSynchronizationContext` | `ToolThreadAffinityTests` |
| 编译运行 + 运行句柄 | — | `CompiledRunControlTests` |
| MCP | `Mcp` / `McpServers` / `OAuthOptions` | `MCP/**`（上下文提供器、工具包、远程、自助、开关） |
| 技能 | `.WithSkills("skills")` | `Skills/**` |
| 子代理 | `SubAgentScope.ForClient(...).WithSubAgentDepth(3)` | `SubAgents/**`（除 live 文件外的全部） |
| 管线 + 对话记录 | `Transcript`、`WithPipeline` | `Pipelines/**` |
| 仪表盘 | — | `Dashboard/AgentDashboardViewModelTests` |
| `VeloxDev.AI` 反射辅助 | — | `VeloxDev.Core.Test/AI/*`（7 个文件） |

刻意**不**计入的唯一文件是 `Agent/SubAgents/SubAgentLiveTests.cs`：它需要真实模型密钥（`API_KEY_DEEPSEEK`）且非确定性（其中一个测试采样至多三次），因此没有密钥时报 `Inconclusive`，从不作为证据。

## 2. 完整代码

一个宿主：构建作用域、挂载子系统、运行一轮。每个标识符都在本块中定义或可追溯到真实文件；没有省略号。`tree` 是来自「工作流系统」特性的 workflow 树；`chatClient` 是任意 `IChatClient`。

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
using VeloxDev.AI.SubAgents;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

public static class AgentHost
{
    // 'tree' 由「工作流系统」特性构建；本宿主只拥有其上的 agent。
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
            .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
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
            .WithInteractionSafety(3)
            .WithToolApproval(false)
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
        var reply = await agent.RunAsync("列出现有节点，然后添加一个 Demo.ViewModels.NetworkRequest 类型的节点。", session, cancellationToken: cancellationToken);

        Console.WriteLine(reply.Text);
        Console.WriteLine(transcript.ToMarkdown());
    }
}
```

标识符可追溯：`AsAgentScope`（`Agent/Workflow/AgentEx`）、`With*` 链（`WorkflowAgentScope.cs`）、`SubAgentScope.ForClient`（`SubAgentScope.cs` 第 160 行）、`McpServerConfiguration` / `McpServerRunMode`（`Agent/MCP/`）、`WithPipeline`（`AgentPipelineExtensions`）、`AgentTranscript`，以及 OpenAI 客户端构造（`AgentHelper.cs`，`ProvideAgent`）。

## 3. 构建与运行

```bash
dotnet build
dotnet run
```

**预期结果：** 进程无错构建。持有有效 `API_KEY_DEEPSEEK` 时模型作答并打印其回复与对话记录（含工具调用）；没有密钥时宿主在任何网络调用之前抛出点名该变量的 `InvalidOperationException`。`skills` 文件夹允许不存在 —— 内嵌技能语料仍会到达。

## 运行声明

- ⚠️ **未做端到端运行** —— 对话需要真实的 `IChatClient` 与 API 密钥，当前不可用。本页的程序**未**按所写编译或执行。
- ✅ **库及其确定性测试**于 2026-10-01 构建并运行：

```text
dotnet test Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj --filter "FullyQualifiedName~Agent&FullyQualifiedName!~SubAgentLiveTests"
已通过! - 失败: 0，通过: 387，已跳过: 0，总计: 387，持续时间: 920 ms
```

`SubAgentLiveTests` 被刻意排除（需要 `API_KEY_DEEPSEEK`，非确定性）。不要把该运行读作上面样例可运行的证明 —— 它证明的是样例所用的 **API** 行为如文档所述，而非某个模型作出了回答。
