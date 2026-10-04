# 12 · Verify & Complete Code

## 1. Coverage by evidence

| Area | Demo | Test |
|---|---|---|
| scope fluent surface + context prompts | `AgentHelper.ProvideAgent` | `WorkflowAgentContextProviderTests`, `ComposedProvidersTests`, `CapabilityEnvelopeTests`, `AgentCapabilityProvidersTests` |
| 68 tools, categories, switches | — | `ToolSwitchTests`, `WorkflowLifecycleFidelityTests`, `NodeGeometryToolTests`, `WorkflowSerializationTests` |
| budgets + `ResetToolCallLimit` | `WithMaxToolCalls(200)` | `BudgetResetTests`, `SubAgentBudgetTests`, `ComposedProvidersTests` |
| tool approval | — | `ToolApprovalTests` |
| thread affinity | `WithSynchronizationContext` | `ToolThreadAffinityTests` |
| compiled runs + run handles | — | `CompiledRunControlTests` |
| MCP | `Mcp` / `McpServers` / `OAuthOptions` | `MCP/**` (context provider, toolkit, remote, self-service, switches) |
| Skills | `.WithSkills("skills")` | `Skills/**` |
| Sub-agents | `SubAgentScope.ForClient(...).WithSubAgentDepth(3)` | `SubAgents/**` (all but the live file) |
| Pipelines + transcript | `Transcript`, `WithPipeline` | `Pipelines/**` |
| Dashboard | — | `Dashboard/AgentDashboardViewModelTests` |
| `VeloxDev.AI` reflection helpers | — | `VeloxDev.Core.Test/AI/*` (7 files) |

The one file deliberately **not** counted is `Agent/SubAgents/SubAgentLiveTests.cs`: it needs a real model key (`API_KEY_DEEPSEEK`) and is non-deterministic (one test samples up to three attempts), so it reports `Inconclusive` without a key and is never used as evidence here.

## 2. Complete code

One host that builds the scope, attaches the subsystems, and runs a turn. Every identifier is defined in this block or traced to a real file; there are no ellipses. `tree` is the workflow tree from the workflow-system feature; `chatClient` is any `IChatClient`.

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
    // 'tree' is built by the workflow-system feature; this host only owns the agent over it.
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
        var reply = await agent.RunAsync("List the nodes in the workflow, then add one node of type Demo.ViewModels.NetworkRequest.", session, cancellationToken: cancellationToken);

        Console.WriteLine(reply.Text);
        Console.WriteLine(transcript.ToMarkdown());
    }
}
```

Symbols traced: `AsAgentScope` (`Agent/Workflow/AgentEx`), the `With*` chain (`WorkflowAgentScope.cs`), `SubAgentScope.ForClient` (`SubAgentScope.cs` line 160), `McpServerConfiguration` / `McpServerRunMode` (`Agent/MCP/`), `WithPipeline` (`AgentPipelineExtensions`), `AgentTranscript`, and the OpenAI client construction (`AgentHelper.cs`, `ProvideAgent`).

## 3. Build and run

```bash
dotnet build
dotnet run
```

**Expected result:** the process builds without errors. With a valid `API_KEY_DEEPSEEK` the model answers and prints its reply plus the transcript (tool calls included); without the key the host throws `InvalidOperationException` naming the variable before any network call. The `skills` folder is allowed not to exist — the embedded skill corpus still arrives.

## Run declaration

- ⚠️ **Not actually run end-to-end** — the conversation requires a real `IChatClient` and an API key that were not available. This page's program was **not** compiled or executed as written.
- ✅ The **library and its deterministic tests** were built and run on 2026-10-01:

```text
dotnet test Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj --filter "FullyQualifiedName~Agent&FullyQualifiedName!~SubAgentLiveTests"
已通过! - 失败: 0，通过: 387，已跳过: 0，总计: 387，持续时间: 920 ms
```

`SubAgentLiveTests` was excluded on purpose (needs `API_KEY_DEEPSEEK`, non-deterministic). Do not read that run as proof the sample above runs — it proves the **APIs** it uses behave as documented, not that a model answered.
