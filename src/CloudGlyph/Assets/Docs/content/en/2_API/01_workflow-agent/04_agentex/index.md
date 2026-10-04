# Workflow Agent — Entry Point: `AgentEx` and `AgentClientExtensions`

Two entry points bind the agent to the host: `AgentEx.AsAgentScope` (tree → scope) and `AgentClientExtensions.AsAIAgent` (chat client + providers → agent).

## AgentEx

`public static class AgentEx` — namespace `VeloxDev.AI.Workflow`; source `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/`.

| Member | Signature | Notes |
|---|---|---|
| `AsAgentScope` | `WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` | Creates a `WorkflowAgentScope` bound to the tree. The only entry point — the scope is not usable without a tree. |

## AgentClientExtensions

`public static class AgentClientExtensions` — namespace `VeloxDev.AI`.

| Member | Signature | Notes |
|---|---|---|
| `AsAIAgent` | `ChatClientAgent AsAIAgent(this IChatClient chatClient, IReadOnlyList<AIContextProvider> providers, string? instructions = null)` | Builds a `ChatClientAgent` with the providers attached. Throws `ArgumentNullException` when `chatClient` is null. |

There is **deliberately no `tools` parameter**: the context providers are the only tool source, so the same tool is never registered through both `ChatOptions.Tools` and a provider (the framework unions those without deduplicating). The providers-first parameter order is what avoids an overload clash with the framework's own `AsAIAgent`. An `instructions`-only call binds to the framework overload — tested by `AgentClientExtensionsTests.AsAIAgent_WithASingleString_BindsToTheFrameworkOverload`.

## Wiring

```csharp
using VeloxDev.AI.Workflow;

// 1. tree -> scope
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithAllowNodeExecution(true)
    .WithMaxToolCalls(200)
    .WithTranscript(transcript);

// 2. scope -> agent — the convenience overload:
var agent = chatClient.AsAIAgent(scope.CreateContextProviders(), scope.ProvideProgressiveContextPrompt());

// ...or spelled out with the pipeline attached, which is what the demo does:
var agent2 = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);
```

Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` (`ProvideAgent`).

> **`WithPipeline` / `AsAIAgent(new ChatClientAgentOptions{...})` are from `Microsoft.Agents.AI`, not VeloxDev** — except `WithPipeline` (from `VeloxDev.AI.Pipelines.AgentPipelineExtensions`) and `AsAIAgent(client, providers, instructions)` (from `AgentClientExtensions`). VeloxDev contributes the scope, the tools and the providers; the session itself is hosted by `Microsoft.Agents.AI` over `Microsoft.Extensions.AI`.

**Expected result:** `scope.CreateContextProviders()` yields at least the workflow provider; passing it to `AsAIAgent` produces an `AIAgent` whose instructions are the scope's prompt and whose tool list is rendered per turn.
