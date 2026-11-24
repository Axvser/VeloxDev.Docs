# Setup

## Prerequisites

- **Supported targets:** `netstandard2.0` and `net8.0`, from `Src/Core/VeloxDev.Core.Extension/VeloxDev.Core.Extension.csproj`.
- **SDK:** .NET SDK 8.0 or newer; the tests run on .NET 10.
- **Package:** `VeloxDev.Core.Extension` 12.3.0.
- **No model is required** to build a transcript or a dashboard. Media input needs a model that accepts the media type.

## Install

```powershell
dotnet new console -n AgentDashboardQuickStart
cd AgentDashboardQuickStart
dotnet add package VeloxDev.Core.Extension --version 12.3.0
```

**Expected result:** `dotnet list package` shows `VeloxDev.Core.Extension`.

## Create the transcript

```csharp
using VeloxDev.AI.Pipelines;

var transcript = new AgentTranscript();

transcript.AddUser("List the nodes.");
transcript.AppendReasoning("I should call ListNodes first.");
transcript.AddToolCall("ListNodes", """{"status":"ok","nodes":[]}""", AgentToolOutcome.Succeeded);
transcript.AppendAnswer("The graph has no nodes.");

Console.WriteLine(transcript.Entries.Count); // 4
```

`AddUser` and `AddToolCall` close any open answer. `AppendAnswer` and `AppendReasoning` extend the open entry of the same role, and resume in a new entry after a tool call rather than losing text.

**Expected result:** four entries; the answer is one `Assistant` entry, the reasoning one `Reasoning` entry.

## Attach it to a scope

```csharp
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var tree = new TreeDefaultViewModel();
var scope = tree.AsAgentScope()
    .WithTranscript(transcript);

var pipeline = scope.Pipeline;
```

`WithTranscript` composes the stage chain the pipeline uses for both `RunAsync` and `RunStreamingAsync`. Attach it **before** the agent is built: the agent is wrapped with that chain, so the host does not have to loop the stream itself.

**Expected result:** `scope.Transcript` is the same instance as `transcript`.

## Create the dashboard

```csharp
using VeloxDev.AI.Dashboard;

var dashboard = AgentDashboardViewModel.Create(scope);
Console.WriteLine(dashboard.SystemToolSummary); // enabled/offered
Console.WriteLine(dashboard.SkillSummary);      // switched on/discovered
Console.WriteLine(dashboard.McpSummary);        // connected/configured
Console.WriteLine(dashboard.SubAgentSummary);   // running/dispatched
```

`Create` reads the scope directly, so the scope need not be configured first. Later `With*` calls reach the panel through `scope.Changed`, and rebuilds are coalesced into one posted pass.

**Expected result:** `SystemToolSummary` is non-zero (the built-ins are always offered); the other three are `0/0` until the matching subsystem is attached.

## Prepare media

```csharp
using VeloxDev.AI;

var options = AgentMediaOptions.CreateVisionDefault(); // images up to 1280×720
var image = await AgentMedia.FromFileAsync("preview/frame.png");

Console.WriteLine($"{image.Kind} {image.MediaType} {image.Width}x{image.Height} {image.ByteCount} B");
```

`FromFileAsync` sniffs the bytes rather than trusting the extension, corrects an alias such as `image/jpg`, and rejects a payload that exceeds the kind's limits. A format the package cannot read without a codec needs `options.Transcoder`.

**Expected result:** prints `Image image/png 1280x720 <bytes> B` for a PNG frame that fits the vision defaults.
