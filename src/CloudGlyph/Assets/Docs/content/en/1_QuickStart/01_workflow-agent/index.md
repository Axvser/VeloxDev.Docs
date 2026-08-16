# Workflow Agent — Quick Start

## Workflow Agent

The workflow-agent feature is the AI control layer of VeloxDev. It turns a running workflow tree into an agent-controllable surface:

- `tree.AsAgentScope()` returns a fluent `WorkflowAgentScope` builder that collects prompt-language, output-language, type discovery, interaction safety, callbacks and custom tools.
- `scope.ProvideProgressiveContextPrompt()` / `ProvideAllContexts()` produce the system prompt (progressive disclosure keeps the prompt small).
- `scope.ProvideTools()` / `CreateToolkit()` produce a `WorkflowAgentToolkit` with about 60 function-calling `AITool`s (Microsoft.Extensions.AI) that let the model inspect, mutate, execute and lay out the graph.
- `WorkflowStateTracker` keeps JSON snapshots of the tree and reports `added/removed/modified` diffs so the agent can observe change with minimal context.
- `McpScope` loads Model Context Protocol servers (stdio local + remote HTTP) and merges their tools into the session.
- The `VeloxDev.AI` reflection utilities (`AgentContextAttribute`, `AgentLanguages`, `AgentContextReader`, `AgentCommandDiscoverer`, `AgentMethodInvoker`, `AgentPropertyAccessor`, `AgentTypeResolver`, event-args types, `SlotSelectorsAttribute`) back the tools.

### Quick Start

#### 1. Prerequisites

- **Supported targets** (from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj` and `VeloxDev.Core.csproj`): `netstandard2.0` — usable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+) for the source generators; the WinForms demo targets `net10.0-windows` — a *tested* configuration, not a requirement.
- **Package manager:** NuGet / `dotnet` CLI.
- **Required services:**
  - A running workflow tree (`IWorkflowTreeViewModel`), per the Workflow System Quick Start.
  - An AI chat client — `IChatClient` from `Microsoft.Extensions.AI` (the demo builds one via `AsIChatClient()`).
  - For MCP: a Node.js / `npx` runtime (or Python / dotnet / exe, per `McpServerRunMode`) and a model-context-protocol server package.


#### 2. Install / Add Dependency

```bash
dotnet add package VeloxDev.Core.Extension
```

`VeloxDev.Core` (the workflow core) is pulled in transitively in Debug builds; reference it explicitly when you only need the core types:

```bash
dotnet add package VeloxDev.Core
```

**Expected result:** both packages appear in the `.csproj`; `dotnet restore` exits 0. `VeloxDev.Core.Extension` brings in `Microsoft.Extensions.AI`, `Microsoft.Agents.AI`, `ModelContextProtocol` (MCP SDK), `CliWrap` and `Newtonsoft.Json` transitively.

#### 3. Basic Setup / Registration

Build an agent scope from a tree and register the components the agent may operate on:

```csharp
var scope = tree.AsAgentScope()                  // tree: IWorkflowTreeViewModel
    .WithPromptLanguage(AgentLanguages.English)  // default language for prompts/docs
    .WithOutputLanguage(AgentLanguages.Chinese)  // language the LLM must use for replies
    .WithAutoDiscovery(assemblyName: "Lib")      // auto-register workflow components/enums/interfaces/data
    .WithMaxToolCalls(200)
    .WithInteractionSafety(3)                    // 0 silent, 1 cautious, 2 balanced, 3 strict
    .WithSelectionHandler(ShowSelectionDialog)   // enables the RequestSelection tool
    .WithConfirmationHandler(ShowConfirmationDialog); // enables the RequestConfirmation tool
```

`WithAutoDiscovery` accepts either an `Assembly` or a simple assembly name (e.g. `"Lib"`, `"VeloxDev.Core"`); it scans for concrete workflow components, `[SlotSelectors]`-referenced enums, interface-typed members, `[AgentCommandParameter]` parameter types and `[AgentContext]`-annotated data types.

**Expected result:** `scope` builds without exception; `scope.ProvideProgressiveContextPrompt()` returns a non-empty prompt string; `scope.ProvideTools()` returns a non-empty `IList<AITool>` with more than 0 tools.

#### 4. Core Usage (Step by Step)

1. **Auto-discovery.** Call `WithAutoDiscovery(assembly)` / `WithAutoDiscovery(assemblyName: "...")` once per assembly containing your workflow components. **Expected result:** `ProvideProgressiveContextPrompt()` embeds a "Registered Component Types" section listing your types with their `[AgentContext]` summaries.

2. **Interaction safety.** Call `WithInteractionSafety(0..3)` — `0` silent (no interaction tools registered, fully autonomous), `1` cautious (ask when ambiguous or bulk/destructive), `2` balanced (ask on multiple plausible paths or ≥ 2 touched nodes/links), `3` strict (confirmation gate + mandatory tool-based interaction). Optionally override the prompt body per level with `WithInteractionSafetyPrompt(level, body)` for levels 1–3. **Expected result:** at level 0 the `RequestSelection`/`RequestConfirmation` tools are absent from `ProvideTools()`; at levels 1–3 they are present **only when** the corresponding handler is registered.

3. **Selection & confirmation handlers.** `WithSelectionHandler(Func<AgentSelectionEventArgs, Task>)` and `WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task>)` wire the host UI dialogs. Inside a selection handler set `args.SelectedOption` (single) or `args.SelectedOptions`/`args.FreeTextResponse` (multi); inside a confirmation handler set `args.Result = AgentConfirmationResult.AllowOnce | AllowAlways | Deny`. **Expected result:** with a handler registered and safety level > 0, `ProvideTools()` contains exactly one `RequestSelection` and one `RequestConfirmation` entry.

4. **Create the agent.** Hand the prompt and the tool list to the chat client:

   ```csharp
   var agent = chatClient.AsAIAgent(
       instructions: scope.ProvideProgressiveContextPrompt(),
       tools: scope.ProvideTools());
   ```

   **Expected result:** `agent` is an `IAIAgent` whose tool set is the workflow toolkit.

5. **Run a turn.** Create a session and run a message. Tools are passed per call via `ChatOptions` so MCP tools loaded mid-session join automatically (the in-repo demo does exactly this):

   ```csharp
   var session = await agent.CreateSessionAsync();
   var runOptions = new ChatClientAgentRunOptions
   {
       ChatOptions = new ChatOptions { Tools = [.. scope.ProvideTools(), .. mcp.LoadedTools] },
   };
   var response = await agent.RunAsync(message, session, runOptions);
   var text = response.Text;
   ```

   **Expected result:** `RunAsync` returns an `AgentResponse`; `text` is the model's reply. Structural mutations performed by the model (create/move/connect/patch nodes) are visible on `tree` afterwards and are undoable via `tree.UndoCommand`.

6. **Load MCP tools.** `new McpScope().WithMcpRoot(".evn/mcp").LoadAsync(configs)` installs the package (npm/pip) and connects over stdio, returning the server's tools as `AITool[]`. Merge them into the session:

   ```csharp
   var mcp = new McpScope().WithMcpRoot(".evn/mcp");
   var mcpTools = await mcp.LoadAsync(
   [
       new McpServerConfiguration
       {
           Name = "Filesystem",
           RunMode = McpServerRunMode.Npx,
           Package = "@modelcontextprotocol/server-filesystem",
           Arguments = [AppContext.BaseDirectory],
       },
   ]);
   var allTools = scope.ProvideTools().Concat(mcpTools).ToArray();
   ```

   **Expected result:** `mcpTools` has at least one tool for a reachable server; after merging, `allTools` contains both the workflow tools and the server's tools. Note the configuration property is `Package` (not `NpmPackage`).

#### 5. Verification

- Run the WinForms demo (`Examples/Workflow/WinForms/Demo`): it opens a ready-made graph, and its chat pane (`Form1`) lets a user send natural-language instructions. The demo's `AgentHelper` builds the scope with `WithAutoDiscovery("VeloxDev.Core")` + `WithAutoDiscovery("Lib")`, `WithAllowNodeExecution(true)`, `WithSynchronizationContext(SynchronizationContext.Current)`, interaction safety 3, and registers MCP server-management tools via `McpAgentToolkit`.
- Automated tests in `Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowAgentToolkitTests.cs` assert tool-call behavior: `MarkDirty` marks the tree dirty, query tools never dirty under `WithAutoMarkDirty(true)`, `CreateTools(WorkflowToolCategory.Query)` excludes mutation/execution tools, removed bundled tools (`AutoLayout`, `BatchExecute`, `CloneNodes`, `CreateAndConfigureNode`) never surface, and `SetEnumSlotCollection` produces no phantom undo entries.
- Reflection utilities are covered by `Src/Core/VeloxDev.Core.Test/AI/*` (`AgentContextReaderTests`, `AgentLanguagesTests`, `AgentCommandDiscovererTests`, `AgentMethodInvokerTests`, `AgentPropertyAccessorTests`, `AgentTypeResolverTests`, `AgentToolCallEventArgsTests`).
- MCP loading is covered by `Src/Core/VeloxDev.Core.Extension.Test/Agent/MCP/McpAgentToolkitTests.cs` and `McpRemoteTests.cs`.

#### 6. Complete Code

A single end-to-end sample that builds a scope, loads MCP tools, merges them and runs one turn. `tree` is an `IWorkflowTreeViewModel` created per the Workflow System QuickStart (e.g. the demo's `TreeViewModel`); `chatClient` is an `IChatClient` from `Microsoft.Extensions.AI` (e.g. an OpenAI-compatible client via `AsIChatClient()`). The `ShowSelectionDialog` / `ShowConfirmationDialog` handlers are host-UI dialogs that set the event-args results shown below.

```csharp
using Microsoft.Extensions.AI;
using VeloxDev.AI;
using VeloxDev.AI.MCP;
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
        var baseTools = scope.ProvideTools();

        var mcp = new McpScope().WithMcpRoot(".evn/mcp");
        var mcpTools = await mcp.LoadAsync(
        [
            new McpServerConfiguration
            {
                Name = "Filesystem",
                RunMode = McpServerRunMode.Npx,
                Package = "@modelcontextprotocol/server-filesystem",
                Arguments = [AppContext.BaseDirectory],
            },
        ]);

        var allTools = baseTools.Concat(mcpTools).ToArray();
        var agent = chatClient.AsAIAgent(instructions: prompt, tools: allTools);
        var session = await agent.CreateSessionAsync();
        var runOptions = new ChatClientAgentRunOptions
        {
            ChatOptions = new ChatOptions { Tools = allTools },
        };

        var response = await agent.RunAsync(
            "List all nodes and report how many are connected.", session, runOptions);
        Console.WriteLine(response.Text);
    }
}
```

#### 7. Run Declaration

- ⚠️ Not actually run — statically verified only. The sample above was assembled from the in-repo README, the `AgentHelper` demo and the `WorkflowAgentToolkit` source; it was not compiled or executed in this documentation pass. Treat the handler bodies as placeholder UI logic.
