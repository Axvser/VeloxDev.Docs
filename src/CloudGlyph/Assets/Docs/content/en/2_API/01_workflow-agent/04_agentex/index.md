# Workflow Agent — Entry Point: `AgentEx`

The single entry point that binds a `WorkflowAgentScope` to a workflow tree. Namespace `VeloxDev.AI.Workflow`; source `Src/Core/VeloxDev.Core.Extension/AgentEx.cs`.

## AgentEx

`public static class AgentEx`

| Member | Signature | Notes |
|---|---|---|
| `AsAgentScope` | `WorkflowAgentScope AsAgentScope(this IWorkflowTreeViewModel tree)` | Creates a new `WorkflowAgentScope` bound to the tree. The only entry point — the scope is not usable without a tree. |

**Example** — `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`, line 155:

```csharp
using VeloxDev.AI.Workflow;

var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithAutoDiscovery(assemblyName: "Lib")
    .WithAllowNodeExecution(true)
    .WithMaxToolCalls(200);
```

After configuration the host builds the tool set and context prompt, then hands both to an AI chat client:

```csharp
var contextPrompt = scope.ProvideProgressiveContextPrompt();   // or scope.ProvideAllContexts()
var tools = scope.ProvideTools();                              // all tools (all categories)

// 'tools' can also be fed to Microsoft.Extensions.AI ChatOptions.Tools, or —
// as in the demo — through Microsoft.Agents.AI on the chat client:
var agent = chatClient.AsAIAgent(instructions: contextPrompt);
```

> **`AsAIAgent` is not defined by VeloxDev.** It is the `Microsoft.Agents.AI` extension on `IChatClient` (`chatClient.AsAIAgent(instructions: ..., tools: ...)`), evidenced in `AgentHelper.ProvideAgent` (line 223). VeloxDev contributes the scope (`AsAgentScope`), the tools (`ProvideTools`) and the context prompts (`ProvideProgressiveContextPrompt` / `ProvideAllContexts`); the agent session itself is hosted by `Microsoft.Agents.AI` over `Microsoft.Extensions.AI`.

For the full chain — scope construction, MCP tool registration, context prompt and run options — see `AgentHelper.ProvideAgent` in `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`.
