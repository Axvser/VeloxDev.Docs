# Setup

## Prerequisites

- **Supported targets:** `netstandard2.0` and `net8.0`, from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`.
- **SDK:** .NET SDK 8.0 or newer; the tests run on .NET 10.
- **Package:** `VeloxDev.Core.Extension` 12.3.0.
- **A model:** spawning a child runs a conversation, so a live `IChatClient` is required for dispatch. Configuring the subsystem and reading its roster needs none.

## Install

```powershell
dotnet new console -n SubAgentsQuickStart
cd SubAgentsQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
dotnet add package Microsoft.Agents.AI.OpenAI --version 1.22.0
```

**Expected result:** `dotnet list package` shows `VeloxDev.Core.Extension` and `Microsoft.Agents.AI.OpenAI`.

## Create the subsystem

```csharp
using Microsoft.Extensions.AI;
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient)
    .WithSubAgentDepth(3)      // the root may dispatch 3 levels down
    .WithSpawnBudget(40);      // used when the parent set no call cap
```

`ForClient` gives every child an agent over the host's client. `ForClientFactory` picks a client per spawn from the `model` name the spawn carries:

```csharp
var byModel = SubAgentScope.ForClientFactory(
    model => model switch
    {
        null => chatClient,
        "fast" => fastChatClient,
        _ => throw new NotSupportedException($"Unknown model '{model}'."),
    });
```

A factory that throws refuses the spawn; the refusal reaches the spawning agent as the child's failure.

**Expected result:** `subAgents.MaxDepth` is `3`, `subAgents.SpawnBudget` is `40`, and `subAgents.Snapshot` is empty.

## Attach it before creating the providers

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithSynchronizationContext(SynchronizationContext.Current)
    .WithSubAgents(subAgents);

var providers = scope.CreateContextProviders();
```

Order matters: `WithSubAgents` registers the subsystem's context provider. Attaching after `CreateContextProviders()` leaves the model with none of the five dispatch tools, and the subsystem is unreachable however it was configured.

**Expected result:** `scope.SubAgents` is the same instance as `subAgents`, and `providers` contains the sub-agent provider.

## What a child inherits

A spawn that asks for nothing gets everything the parent currently offers: the same tools, skills and MCP servers, including the ability to dispatch in turn. A spawn that names a smaller set gets the intersection — never more than the parent has, and anything it asked for beyond that is dropped and reported back in the spawn result.

**Expected result:** a child of an `AutoEdit` parent inherits `AutoEdit`; it cannot come away believing it holds a capability the parent was refused.
