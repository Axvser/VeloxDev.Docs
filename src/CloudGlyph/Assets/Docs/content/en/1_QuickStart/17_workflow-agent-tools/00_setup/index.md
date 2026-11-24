# Setup

## Prerequisites

- **Supported targets:** `netstandard2.0` and `net8.0`, from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`.
- **SDK:** .NET SDK 8.0 or newer. The repository's test project targets `net10.0`, so .NET 10 is the tested configuration.
- **Package:** `VeloxDev.Core.Extension` 12.3.0 (it pulls `VeloxDev.Core` 12.3.0).
- **Agent Framework:** `Microsoft.Agents.AI` 1.22.0 and `Microsoft.Extensions.AI` 10.10.0 or newer.
- **Model endpoint (conversation step only):** the repository demo uses `Microsoft.Agents.AI.OpenAI` 1.22.0 against DeepSeek at `https://api.deepseek.com`, with the key in the `API_KEY_DEEPSEEK` environment variable. Any `IChatClient` works for the same wiring.

## Install

```powershell
dotnet new console -n WorkflowAgentQuickStart
cd WorkflowAgentQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
dotnet add package Microsoft.Agents.AI.OpenAI --version 1.22.0
```

**Expected result:** `dotnet list package` shows `VeloxDev.Core.Extension`, `Microsoft.Agents.AI` and `Microsoft.Agents.AI.OpenAI`.

## Create the scope

`AsAgentScope()` is the extension `AgentEx.AsAgentScope(this ITreeComponent)` in `Src/Core/VeloxDev.Core.Extension/AgentEx.cs`.

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope();

Console.WriteLine(ReferenceEquals(scope.Tree, tree)); // True
```

**Expected result:** prints `True`. The scope wraps the tree without replacing it.

## Configure the surface

```csharp
scope
    .WithAutoDiscovery()                 // discover the component context the generator compiled
    .WithAllowNodeExecution(false)       // execution tools stay refused until the host opts in
    .WithMaxToolCalls(120)
    .WithMaxToolResultChars(48 * 1024)
    .WithToolCallCallback(args =>
    {
        Console.WriteLine($"[tool] {args.ToolName} (call #{args.CallCount})");
        return Task.CompletedTask;
    });
```

`WithToolCallCallback` receives `AgentToolCallEventArgs` (`ToolName`, `Result`, `CallCount`). It fires after a **successful** call; refused and failed calls travel as `AgentToolCallCompleted` events instead.

**Expected result:** the chain returns the same `scope`; `scope.MaxToolCalls` is `120`.

## Choose what the model may run

Two independent controls exist and are easy to confuse:

| Control | Type | Decides |
|---|---|---|
| `WorkflowToolCategory` | surface filter | which tool groups are sent to the model at all |
| `AgentPermissionMode` | call-time policy | which of the sent tools may actually run |

Registering only `WorkflowToolCategory.Query` means the model never sees a mutation tool. Leaving the session in `Plan` means it sees them and is refused at call time. The next page shows both.

**Expected result:** you can state, for one tool, whether it is visible and whether it is allowed — the two answers need not match.
