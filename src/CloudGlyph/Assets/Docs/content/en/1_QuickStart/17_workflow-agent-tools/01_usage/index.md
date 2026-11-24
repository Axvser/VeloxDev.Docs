# Usage

## List the categories

`WorkflowToolCategory` is a flags enum in `VeloxDev.AI.Workflow.Functions`. The workflow toolkit registers tools per category, and `CreateTools` returns only the selected groups.

```csharp
using VeloxDev.AI.Workflow.Functions;

var toolkit = scope.CreateToolkit();
foreach (var tool in toolkit.CreateTools(WorkflowToolCategory.Query))
    Console.WriteLine(tool.Name);
```

**Expected result:** the query names appear, starting with `ListNodes`, `GetNodeDetail`, `GetWorkflowSummary`, `FindNodes`, `ValidateWorkflow`, `GetFullTopology`, `CompileWorkflow`, `SerializeWorkflow`, `ListCompiledRuns`.

| Category | Representative tools |
|---|---|
| `Query` | `ListNodes`, `GetNodeDetail`, `GetFullTopology`, `GetTypeSchema`, `ValidateWorkflow`, `CompileWorkflow`, `GetExecutionLog` |
| `Mutation` | `CreateNode`, `DeleteNode`, `CreateSlotOnNode`, `ConnectSlots`, `PatchNodeProperties`, `SetEnumSlotCollection`, `Undo`, `Redo` |
| `Execution` | `ExecuteNode`, `ExecuteNodes`, `RunCompiledWorkflow`, `StartCompiledWorkflow`, `PauseCompiledRun`, `GetCompiledRunStatus` |
| `Command` | `ExecuteCommandOnNode`, `ExecuteCommandById` |
| `Graph` | `SearchForward`, `SearchReverse`, `IsConnected`, `FindPath` |
| `Layout` | `GetLayoutInfo`, `PreviewLayout`, `ArrangeLayout` |
| `Analytics` | `GetNodeStatistics` |
| `State` | `TakeSnapshot`, `GetChangesSinceSnapshot`, `MarkDirty` |
| `Interaction` | `RequestSelection`, `RequestConfirmation` (only when handlers are configured) |

`Composite` exists as a reserved flag and registers no tools: every operation is one component command, so the Core undo stack is never bypassed.

## Switch a single tool off

```csharp
using System.Linq;

scope.WithToolEnabled("DeleteNode", false);

var mutation = scope.CreateToolkit().CreateTools(WorkflowToolCategory.Mutation);
Console.WriteLine(mutation.Any(t => t.Name == "DeleteNode")); // False
```

**Expected result:** prints `False`. The switch reaches tools from every source — built-in, custom, skills, MCP — because it is checked inside the shared call wrapper, not only in the workflow toolkit's own filter.

## Wire a chat client

The provider is the only source of tools. The agent gets the static instructions from `ProvideProgressiveContextPrompt()` and the per-turn tool surface from `CreateContextProviders()`.

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using OpenAI;
using System.ClientModel;

var apiKey = Environment.GetEnvironmentVariable("API_KEY_DEEPSEEK")
    ?? throw new InvalidOperationException("Set API_KEY_DEEPSEEK before running.");

var chatClient = new OpenAIClient(
        new ApiKeyCredential(apiKey),
        new OpenAIClientOptions { Endpoint = new Uri("https://api.deepseek.com") })
    .GetChatClient("deepseek-v4-flash")
    .AsIChatClient();

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);

var session = await agent.CreateSessionAsync();
var response = await agent.RunAsync("List the node indexes in this graph.", session);
Console.WriteLine(response.Text);
```

**Expected result:** the tool callback prints `ListNodes`, and the answer names the node indexes in the tree.

## Verification

1. Run the program and ask for the node list. The callback prints `[tool] ListNodes (call #1)` and the answer contains the node count.
2. Ask it to add a node at `(200, 120)`. At the default `Auto` mode the edit runs; `tree.Nodes.Count` grows by one.
3. Delete a slot or call `ValidateWorkflow`; the callback names the tool and the answer reflects the result.

A refusal is different from a missing tool: `Plan` keeps the tool visible and refuses the call with a message naming the mode. That behaviour belongs to [Agent Safety and Budgets](../../18_agent-safety-budgets/index.md).

## Complete code

The program below lists the query tools, disables one mutation tool, and then runs one conversation. `ImplicitUsings` is enabled by the console template, so `System`, `System.Linq` and `System.Threading.Tasks` are in scope.

```csharp
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using OpenAI;
using System.ClientModel;
using VeloxDev.AI.Workflow;
using VeloxDev.AI.Workflow.Functions;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithAutoDiscovery()
    .WithMaxToolCalls(120)
    .WithToolCallCallback(args =>
    {
        Console.WriteLine($"[tool] {args.ToolName} (call #{args.CallCount})");
        return Task.CompletedTask;
    });

Console.WriteLine("Query tools:");
foreach (var tool in scope.CreateToolkit().CreateTools(WorkflowToolCategory.Query))
    Console.WriteLine($"  {tool.Name}");

scope.WithToolEnabled("DeleteNode", false);

var apiKey = Environment.GetEnvironmentVariable("API_KEY_DEEPSEEK")
    ?? throw new InvalidOperationException("Set API_KEY_DEEPSEEK before running.");

var chatClient = new OpenAIClient(
        new ApiKeyCredential(apiKey),
        new OpenAIClientOptions { Endpoint = new Uri("https://api.deepseek.com") })
    .GetChatClient("deepseek-v4-flash")
    .AsIChatClient();

var agent = chatClient.AsAIAgent(new ChatClientAgentOptions
{
    ChatOptions = new ChatOptions { Instructions = scope.ProvideProgressiveContextPrompt() },
    AIContextProviders = scope.CreateContextProviders(),
}).WithPipeline(scope.Pipeline);

var session = await agent.CreateSessionAsync();
var response = await agent.RunAsync("List the node indexes in this graph.", session);
Console.WriteLine(response.Text);
```

## Run declaration

- ⚠️ Not actually run — statically verified against `Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs`, `Agent/Workflow/Functions/WorkflowAgentToolkit.cs`, `Agent/Workflow/Functions/WorkflowToolCategory.cs`, and the demo wiring in `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs`. The conversation step needs a live model endpoint, so no output is recorded.
