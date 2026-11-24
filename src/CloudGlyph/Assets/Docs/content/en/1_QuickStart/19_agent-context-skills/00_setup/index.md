# Setup

## Prerequisites

- **Supported targets:** `netstandard2.0` and `net8.0`, from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`.
- **SDK:** .NET SDK 8.0 or newer; the tests run on .NET 10.
- **Package:** `VeloxDev.Core.Extension` 12.3.0.
- **Generator (for `[AgentContext]` on your own types):** `VeloxDev.Core.Generator` 12.3.0 as an analyzer. The embedded workflow skills work without it.
- **No model is required** to render context or enumerate skills.

## Install

```powershell
dotnet new console -n AgentContextQuickStart
cd AgentContextQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**Expected result:** `dotnet list package` shows `VeloxDev.Core.Extension`.

## Create the scope

```csharp
using VeloxDev.AI;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithPromptLanguage(AgentLanguages.English)
    .WithOutputLanguage(AgentLanguages.Chinese)
    .WithAutoDiscovery();

Console.WriteLine(scope.PromptLanguage); // English
```

`WithAutoDiscovery()` reads the agent-context tree the generator compiled into the referenced assemblies. `WithPromptLanguage` selects the language of the instruction text; `WithOutputLanguage` selects the language of the model's answer.

**Expected result:** prints `English`. The scope is ready to render context without a chat client.

## Describe a type declaratively

`AgentContextAttribute` attaches a natural-language description to a type or member. It is repeatable, one entry per language.

```csharp
using VeloxDev.AI;

[AgentContext(AgentLanguages.English, "A node that runs a Python script and exposes one output slot per declared port.")]
[AgentContext(AgentLanguages.Chinese, "运行 Python 脚本的节点，按声明的端口各暴露一个输出槽。")]
public sealed class ScriptNodeViewModel
{
    public string Script { get; set; } = string.Empty;
}
```

**Expected result:** once the generator runs, `AgentContextCollector.GetClassContext(typeof(ScriptNodeViewModel), AgentLanguages.English)` returns a Markdown block containing the English sentence.

## Register types by hand

Automatic discovery is not the only route. A host can name the types it wants:

```csharp
scope.WithComponents(new[] { typeof(ScriptNodeViewModel) }, AgentLanguages.English)
     .WithEnums(new[] { typeof(SlotState) }, AgentLanguages.English)
     .WithInterfaces(new[] { typeof(INodeComponent) }, AgentLanguages.English)
     .WithData(new[] { typeof(Anchor) }, AgentLanguages.English);
```

| Method | Renders |
|---|---|
| `WithComponents` | commands, slots, promoted properties |
| `WithEnums` | enum members and their meanings |
| `WithInterfaces` | interface contract |
| `WithData` | a value object's properties and annotated fields |

**Expected result:** `scope.ProvideCustomerContext()` now includes the framework enum, interface and data blocks. The component block appears once the generator has compiled the context entry for `ScriptNodeViewModel`.

## Choose a prompt shape

```csharp
var progressive = scope.ProvideProgressiveContextPrompt(); // static skeleton
var full        = scope.ProvideAllContexts();              // skeleton + every context block, one shot
var framework   = scope.ProvideFrameworkContext();         // framework types only
var customer    = scope.ProvideCustomerContext();          // host-registered types only
```

**Expected result:** `progressive` is much shorter than `full`, and `framework` is non-empty for the default tree.
