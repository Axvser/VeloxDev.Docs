# Workflow Agent — Verify & Complete Code

This page shows how the feature is verified (demos and automated tests), then gives the single runnable program the whole Quick Start has been building toward.

## 1. Verify with the demos

Every full (non-trimmed) desktop demo under `Examples/Workflow/*/Demo` (Avalonia, Blazor, Jalium, MAUI, WPF, WinForms, WinUI) exposes an agent chat panel. They share one builder — `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` — which constructs the scope exactly as this Quick Start does:

- `WithPromptLanguage(English)` + `WithOutputLanguage(Chinese)`, two `WithAutoDiscovery` passes (`VeloxDev.Core`, `Lib`), `WithAutoMarkDirty(false)`, `WithMaxToolCalls(200)`, `WithAllowNodeExecution(true)`, `WithSynchronizationContext(SynchronizationContext.Current)`, `WithToolCallCallback` (raises a virtualization refresh event), selection/confirmation handlers, and interaction safety driven from a host property (default 3).
- MCP management tools (`ListMcpServers`, `DescribeMcpServer`, `LoadMcpServers`, `UnloadMcpServer`) are registered through `scope.WithTools(...)` over a shared `McpScope`; servers are host pre-registered (`McpServerRunMode.Http` remote + `Npx` local) and loaded via `helper.Mcp.LoadAsync`.
- Each demo View registers the real dialogs — WinForms (`Form1.cs` + `Dialogs/AgentConfirmationDialog.cs`, `Dialogs/AgentSelectionDialog.cs`) is one example; the chat command `AskAsync` on `TreeViewModel` runs `agent.RunAsync(message, session, helper.BuildRunOptions())` (or the streaming variant).

To run one, set the `API_KEY_DEEPSEEK` environment variable to an OpenAI-compatible key and launch a demo project (e.g. `Examples/Workflow/WinForms/Demo`).

## 2. Verify with the automated tests

- `VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowLifecycleFidelityTests.cs` drives the public tools through `ProvideTools()` and asserts lifecycle fidelity: `AddSlotToCollection` registers a slot and is undoable/redoable with the same instance; `ExecuteNode` reports actual completion; `CompileNodeResult` on a single-node tree produces a Terminal-role plan (`graphCount == 1`); `GetNodeResult` is rejected by host policy without `WithAllowNodeExecution(true)` and runs to completion with `targetReached == true` when allowed; `MoveNode` replays GUI drag semantics and is non-undoable; `WithSynchronizationContext` marshals every tool call through the UI context.
- `WorkflowSerializationTests.cs` pins whole-tree JSON round-trips (a `SlotEnumerator`-driven enum node keeps its selector type and `CurrentValue`; a zoomed tree stores raw/world coordinates and collapses exactly once after load).
- `DeepZoomSpatialRefreshProbeTests.cs` is a pure-data GUI probe asserting a scale-only change must re-index spatial providers synchronously so a node stays visible after `Virtualize`.
- `VeloxDev.Core.Extension.Test/Agent/MCP/McpAgentToolkitTests.cs` and `McpRemoteTests.cs` cover the four management tools and `McpScope`: Http transport options (headers, OAuth via `WithOAuthAuthorizationRedirect`, timeout, `transportMode`), stdio (`Npx`) env/working-directory options, status tracking, and error reporting without throwing.
- `VeloxDev.Core.Test/AI/*` covers the reflection bridge (`AgentContextReader`, `AgentLanguages`, `AgentCommandDiscoverer`, `AgentMethodInvoker`, `AgentPropertyAccessor`, `AgentTypeResolver`, `AgentToolCallEventArgs`).
- Engine fidelity (linear chains, dynamic router branch selection, fan-out payload restore, `IGroupData` joins, terminal branches, error handling) is pinned by `VeloxDev.Core.Test/WorkflowSystem/CompilerEx/RuntimeEngineRunTests.cs`.

## 3. Complete code

One self-contained program: given a running workflow tree and an `IChatClient`, build a hardened scope, produce the progressive prompt, create the agent and run one turn. `ShowSelectionDialog` / `ShowConfirmationDialog` are the host-UI dialogs that set the event-args results shown. `tree` is an `IWorkflowTreeViewModel` created per the Workflow System Quick Start; `chatClient` is any `IChatClient` (an OpenAI-compatible one via `AsIChatClient()`, as the demo does).

```csharp
using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using VeloxDev.AI;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

public static class WorkflowAgentQuickStart
{
    public static async Task RunAsync(IWorkflowTreeViewModel tree, IChatClient chatClient)
    {
        var scope = tree.AsAgentScope()
            .WithPromptLanguage(AgentLanguages.English)
            .WithOutputLanguage(AgentLanguages.Chinese)
            .WithAutoDiscovery(assemblyName: "VeloxDev.Core")
            .WithAutoDiscovery(assemblyName: "Lib")
            .WithAutoMarkDirty(false)
            .WithMaxToolCalls(200)
            .WithAllowNodeExecution(true)
            .WithSynchronizationContext(SynchronizationContext.Current)
            .WithInteractionSafety(3)
            .WithSelectionHandler(async args =>
            {
                args.SelectedOption = args.Options.FirstOrDefault();
                await Task.CompletedTask;
            })
            .WithConfirmationHandler(async args =>
            {
                args.Result = AgentConfirmationResult.AllowOnce;
                await Task.CompletedTask;
            });

        var prompt = scope.ProvideProgressiveContextPrompt();
        var baseTools = scope.ProvideTools().ToArray();

        var agent = chatClient.AsAIAgent(instructions: prompt);
        var session = await agent.CreateSessionAsync();
        var runOptions = new ChatClientAgentRunOptions
        {
            ChatOptions = new ChatOptions { Tools = baseTools },
        };

        var response = await agent.RunAsync(
            "List all nodes and report how many are connected.",
            session,
            runOptions);
        if (response is not null)
        {
            Console.WriteLine(response.Text);
        }
    }
}
```

No `...` — every identifier is defined in this block, declared in an earlier page, or traceable to a real file (`tree` and `chatClient` as described above). To add MCP server tools, build an `McpScope`, `LoadAsync(servers)` and merge `[.. baseTools, .. mcp.LoadedTools]` into `ChatOptions.Tools` as shown on the Custom Tools & MCP page.

## 4. Run declaration

- ⚠️ Not actually run — statically verified only. The complete-code program mirrors the real `AgentHelper.ProvideAgent` flow (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`) and the `ChatClientAgent`/`AgentSession` call pattern from `TreeViewModel.AskAsync`; it was not compiled or executed in this documentation pass. Handler bodies are placeholder host-UI logic; the prerequisite key/endpoint was not exercised.
