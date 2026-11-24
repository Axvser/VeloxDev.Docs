# Usage

## The transcript API

```csharp
transcript.AddUser("Export the graph.");
transcript.AppendAnswer("I will serialise it.");
transcript.AppendReasoning("Use SerializeWorkflow in summary mode.");
transcript.AddToolCall("SerializeWorkflow", """{"status":"ok"}""", AgentToolOutcome.Succeeded);
transcript.AddError("The export failed.");
```

| Member | Result |
|---|---|
| `Entries` | ordered `AgentTranscriptEntry` list |
| `AddUser(text, attachments?)` | a `User` entry, closing the open answer |
| `AppendAnswer(fragment)` | extends or starts an `Assistant` entry |
| `AppendReasoning(fragment)` | extends or starts a `Reasoning` entry |
| `AddToolCall(name, result, outcome)` | a `ToolCall` entry |
| `AddError(text)` | an `Error` entry |
| `ToMarkdown(options?)` | a renderable document |
| `ToJson()` / `Restore(json)` | persistence of the **display** record |
| `ToPlainTextLines()` | one line per entry with role prefixes |

`ToMarkdown` takes `AgentMarkdownOptions` (`ReasoningFence`, `ReasoningHeading`, `ChatFences`, `ToolDetailLimit`). With `ChatFences` each tool call becomes its own collapsible panel; without it, a compact bulleted run.

**Expected result:** `transcript.ToMarkdown()` shows the user turn, the reasoning block, the tool row and the answer in order. `Restore(ToJson())` reproduces the same entries.

## The event pipeline

The pipeline is what fills the transcript during a run. `scope.Pipeline` already carries the accounting and transcript stages; add your own before or after.

```csharp
using VeloxDev.AI.Pipelines;

scope.Pipeline.Use((agentEvent, next, ct) =>
{
    if (agentEvent is AgentToolCallCompleted tool)
        Console.WriteLine($"{tool.ToolName}: {tool.Outcome} in {tool.Elapsed.TotalMilliseconds:F0} ms");
    return next(agentEvent);
});
```

| Event | Carries |
|---|---|
| `AgentTurnStarted` | run kind, prompt, attachments |
| `AgentTextDelta` / `AgentReasoningDelta` | one streaming fragment |
| `AgentToolCallStarted` / `AgentToolCallCompleted` | tool name, result, outcome, elapsed |
| `AgentTurnCompleted` | answer, elapsed, token usage |
| `AgentTurnFaulted` | error, or cancellation |
| `AgentUsageReported` | token usage from a streaming turn |
| `AgentMediaReceived` | an attachment and its content |

A stage that throws is reported through `AgentPipeline.StageFailed` and the run continues. `WithPipeline` installs the chain in the framework's middleware slot, so both `RunAsync` and `RunStreamingAsync` are observed.

**Expected result:** a run prints one line per completed tool call, and the transcript gains the matching entries without host code appending them.

## The dashboard

`AgentDashboardViewModel` groups one scope into five collections:

| Collection | Rows |
|---|---|
| `SystemTools` | the workflow built-ins plus host-registered tools |
| `SkillTools` | `ListSkills`, `load_skill`, `UnloadSkill`, `read_skill_resource` |
| `McpServers` | one row per configured server, expandable to its tools |
| `Skills` | every discovered skill |
| `SubAgents` | children dispatched this session |

Each row is a **projection**, not a second source of truth. Flipping `IsEnabled` calls `ApplyToScope`; a change made in the scope comes back through `SetFromScope` without echoing. That is why the panel must not write `SkillStatusViewModel.IsEnabled` directly: doing so would bypass the scope's `Version` bump and a cached prompt would keep serving text the host thought it had switched off.

`IsReachable` is `IsEnabled && Note.Length == 0` — "on but blocked by host policy" is a real state, and `Note` spells it out. `ActivityText` reports the call count.

**Expected result:** toggling `dashboard.Skills[0].IsEnabled` changes `scope.Skills` on the next turn; `dashboard.Rebuild()` re-reads everything after a direct scope change.

## Media input

Media belongs in a **user message**, not in a tool result. On OpenAI-compatible chat completions the tool message has a text channel only, so a `DataContent` returned by a tool reaches the model as a base64 JSON string, not as pixels or sound.

```csharp
var image = await AgentMedia.FromFileAsync("preview/frame.png");
var note  = await AgentMedia.FromFileAsync("audio/note.mp3");
var pdf   = await AgentMedia.FromFileAsync("docs/spec.pdf");

var options = AgentMediaOptions.CreateVisionDefault();
options.Transcoder = myHostTranscoder; // optional

await foreach (var update in agent.RunStreamingWithMediaAsync(
    "Check the frame, the voice note and the spec.", new[] { image, note, pdf }, options, session))
{
    // each payload travels as its own image_url / input_audio / file block
}
```

`AgentMessage.CreateUserAsync(prompt, media, options)` builds the message when you want to drive `RunAsync` yourself. `AgentMediaReference.FromUrl` sends a URL without fetching it. `AgentAttachment` appears in `AgentTurnStarted` with name, media type and size — not the bytes.

**Expected result:** a model that accepts images answers about the frame; one that does not rejects the part, so keep a text-only fallback.

## Verification

1. Run the complete program. It prints a Markdown transcript, the entry count before and after a JSON round trip, and the four dashboard summaries.
2. Confirm the restored transcript has the same entry count.
3. Confirm `SystemToolSummary` is non-zero and the three subsystem summaries are `0/0` — no skills, MCP servers or sub-agents were attached.

## Complete code

```csharp
using VeloxDev.AI.Dashboard;
using VeloxDev.AI.Pipelines;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

var transcript = new AgentTranscript();
transcript.AddUser("Add a node and connect its output.");
transcript.AppendReasoning("Inspect the graph before editing.");
transcript.AddToolCall("ListNodes", """{"status":"ok","nodes":[]}""", AgentToolOutcome.Succeeded);
transcript.AppendAnswer("There are no nodes yet. I will create one.");
transcript.AddToolCall("CreateNode", """{"status":"ok","nodeIndex":0}""", AgentToolOutcome.Succeeded);

Console.WriteLine(transcript.ToMarkdown());
Console.WriteLine($"entries: {transcript.Entries.Count}");

var json = transcript.ToJson();
var restored = new AgentTranscript();
restored.Restore(json);
Console.WriteLine($"restored entries: {restored.Entries.Count}");

var scope = new TreeDefaultViewModel().AsAgentScope();
using var dashboard = AgentDashboardViewModel.Create(scope);
Console.WriteLine($"system tools: {dashboard.SystemToolSummary}");
Console.WriteLine($"skills:       {dashboard.SkillSummary}");
Console.WriteLine($"mcp:          {dashboard.McpSummary}");
Console.WriteLine($"sub-agents:   {dashboard.SubAgentSummary}");
```

## Run declaration

- ⚠️ Not actually run — statically verified against `Src/Core/VeloxDev.Core.Extension/Agent/Pipelines/AgentTranscript.cs`, `AgentEvent.cs`, `AgentPipeline.cs`, `AgentPipelineAgent.cs`, `Agent/Dashboard/AgentDashboardViewModel.cs`, `Agent/Dashboard/AgentMemberViewModel.cs`, `Agent/Media/AgentMedia.cs`, and `Agent/Media/AgentMediaAgentExtensions.cs`. The dashboard is test-covered only; no demo binds it. No run output is recorded.
