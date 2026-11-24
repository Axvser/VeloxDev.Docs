# Setup

## Prerequisites

- **Supported targets:** `netstandard2.0` and `net8.0`, from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`.
- **SDK:** .NET SDK 8.0 or newer; the repository's tests run on .NET 10.
- **Package:** `VeloxDev.Core.Extension` 12.3.0.
- **No model is required** for the policy itself. Evaluating a call is a pure in-memory decision; only a live agent needs a chat client.

## Install

```powershell
dotnet new console -n AgentSafetyQuickStart
cd AgentSafetyQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**Expected result:** `dotnet list package` shows `VeloxDev.Core.Extension`.

## Build the first policy

`AgentPermissionPolicy` is immutable; every `With*` call returns a new policy, so a reader holds one consistent rule set for a whole call.

```csharp
using VeloxDev.AI.Safety;

var policy = AgentPermissionPolicy.For(AgentPermissionMode.AutoEdit)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask, "DeleteNode"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"));

Console.WriteLine(policy.Mode);       // AutoEdit
Console.WriteLine(policy.Rules.Count); // 2
```

**Expected result:** prints `AutoEdit` and `2`. The original policy is unchanged; each call produced a new one.

## Evaluate one call

```csharp
var call = new ToolInvocation(
    Name: "DeleteNode",
    Category: AgentActionCategory.Edit,
    Source: null,
    Arguments: new Dictionary<string, object?>());

Console.WriteLine(policy.Evaluate(call)); // Ask
```

`ToolInvocation` carries the tool name, its category, its origin (`mcp:<server>` for an MCP tool, otherwise `null`) and the model-supplied arguments. Arguments are present because some policies are about **what the call would do**, not only which tool it is — adding an MCP server from a local package installs software, while an HTTP endpoint does not.

**Expected result:** prints `Ask`. The rule matched the tool name and overrode the mode's `Allow` for `Edit`.

## Attach the policy to a scope

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithPermissionMode(AgentPermissionMode.AutoEdit)
    .WithPermissionRule(PermissionDecision.Ask, "DeleteNode", "DeleteSlot", "DisconnectSlots")
    .WithMaxToolCalls(200)
    .WithMaxReadToolCalls(150)
    .WithMaxWriteToolCalls(50);
```

`WithPermissionRule` takes one decision and one or more patterns. `WithPermissionMode` is for construction; `SetPermissionMode` is the runtime switch.

**Expected result:** calling `scope.SetPermissionMode(AgentPermissionMode.Plan)` returns `true`, and the next tool call is judged by `Plan`.
