# Transcript

`VeloxDev.AI.Pipelines.AgentTranscript` is the conversation a host binds: what the user said, what the model thought, what it answered, and which tools it used — in one ordered collection. It owns the two rules demo hosts used to implement themselves and get wrong: fragments continue only the open entry of the same role, and tool calls are entries rather than separators.

## Attachment to a workflow scope

| Member | Signature | Description |
|---|---|---|
| `WithTranscript` | `WorkflowAgentScope WithTranscript(AgentTranscript transcript)` | Attaches a conversation and wires the stages that maintain it. One call replaces the run loop a host would otherwise write. |
| `Transcript` | `AgentTranscript? Transcript { get; }` | The attached conversation, once `WithTranscript` ran. |

Attach it **before** the agent is built: the agent is wrapped with that stage chain, so the host does not loop the stream itself.

## Enum: AgentTranscriptRole

| Member | Meaning |
|---|---|
| `User` | A message from the user. |
| `Assistant` | The model's answer. |
| `Reasoning` | The model's thinking. |
| `ToolCall` | One completed tool call. |
| `Error` | A failure rendered to the user. |

## Class: AgentTranscriptEntry

One entry. A single type carrying a role rather than a class per role, so a template binds and picks its own presentation.

| Member | Type / Signature | Description |
|---|---|---|
| `Text` | `string` | The entry's accumulated text (generated MVVM property). |
| `Role` | `AgentTranscriptRole` | What this entry is. |
| `Timestamp` | `DateTimeOffset` | When it was first created. Settable only by a restore. |
| `ToolName` | `string` | Tool name, for `ToolCall`. |
| `Outcome` | `AgentToolOutcome?` | How the tool ended, for `ToolCall`. |
| `Detail` | `string` | The tool's raw result payload. |
| `Attachments` | `IReadOnlyList<AgentAttachment>` | What a user turn attached besides text; a display record, not the bytes. |
| `IsStreaming` | `bool` | Whether more fragments may be appended. Answer and reasoning entries stay open; every other kind is complete at creation. |
| `Summary` | `string` | One collapsed line. |
| `HasDetail` | `bool` | Whether there is a payload worth expanding. |
| `User(string text)` | `static AgentTranscriptEntry` | A text message. |
| `User(string text, IReadOnlyList<AgentAttachment>? attachments)` | `static AgentTranscriptEntry` | A message with attachments. |
| `Assistant()` | `static AgentTranscriptEntry` | A new, empty answer. |
| `Reasoning()` | `static AgentTranscriptEntry` | A new, empty reasoning block. |
| `Error(string text)` | `static AgentTranscriptEntry` | An error. |
| `ToolCall(string toolName, string result, AgentToolOutcome outcome)` | `static AgentTranscriptEntry` | A completed tool call. |

## Class: AgentTranscript

| Member | Type / Signature | Description |
|---|---|---|
| `Entries` | `ObservableCollection<AgentTranscriptEntry>` | The conversation, oldest first (generated MVVM property). |
| `Open` | `AgentTranscriptEntry?` | The entry fragments are currently appended to, or `null`. |
| `CloseOpen()` | `void CloseOpen()` | Closes the open entry without starting another; called when a turn ends. |
| `Clear()` | `void Clear()` | Drops the whole conversation. |
| `AddUser(string text)` | `AgentTranscriptEntry AddUser(string text)` | Records a user message, closing any open answer. |
| `AddUser(string text, IReadOnlyList<AgentAttachment>? attachments)` | `AgentTranscriptEntry AddUser(string text, IReadOnlyList<AgentAttachment>? attachments)` | The same, with attachments. |
| `AddError(string text)` | `AgentTranscriptEntry AddError(string text)` | Records a failure, closing any open answer. |
| `AppendAnswer(string fragment)` | `AgentTranscriptEntry AppendAnswer(string fragment)` | Extends the open answer; a tool call, reasoning block or user message closes it and the answer resumes in a new entry. |
| `AppendReasoning(string fragment)` | `AgentTranscriptEntry AppendReasoning(string fragment)` | Extends the open reasoning block, same rule. |
| `AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | `AgentTranscriptEntry AddToolCall(string toolName, string result, AgentToolOutcome outcome)` | Records a completed tool call, closing any open answer first. |
| `ToMarkdown(AgentMarkdownOptions? options = null)` | `string ToMarkdown(AgentMarkdownOptions? options = null)` | Renders the conversation as Markdown. Consecutive tool calls form one block, or one folded panel each when `ChatFences` is on. |
| `ToPlainTextLines()` | `IReadOnlyList<string> ToPlainTextLines()` | One line per entry, with role prefixes. Tool calls appear here too. |
| `ToJson()` | `string ToJson()` | The display record as a JSON array. |
| `Restore(string json)` | `void Restore(string json)` | Replaces every entry with the document `ToJson` produced. Throws when it is not a JSON array. |

`ToJson` persists the **display** record, not the model's side of the conversation. To resume a conversation, persist the agent session with the framework as well.

The type is not thread-safe by design: one pipeline stage feeds it, on whatever thread that stage is marshalled to.

## Class: AgentMarkdownOptions

| Member | Type | Default | Description |
|---|---|---|---|
| `ReasoningFence` | `string` | `"thinking"` | The info string on the fence wrapping reasoning. Empty drops the fence. |
| `ReasoningHeading` | `string?` | `"**思考：**"` | The label above the fence, or `null` for none. |
| `ChatFences` | `bool` | `false` | Render reasoning and tool calls as collapsible chat panels instead of a code fence and a bullet list. |
| `ToolDetailLimit` | `int` | `4000` | Longest tool payload a panel carries; `0` carries all. |

## Example

```csharp
using VeloxDev.AI.Pipelines;

var transcript = new AgentTranscript();
transcript.AddUser("List the nodes.");
transcript.AppendReasoning("I should call ListNodes first.");
transcript.AddToolCall("ListNodes", """{"status":"ok","nodes":[]}""", AgentToolOutcome.Succeeded);
transcript.AppendAnswer("The graph has no nodes.");

Console.WriteLine(transcript.ToMarkdown());
```

## Related

- [Event pipeline](../01_event-pipeline/index.md) — the stages that fill the transcript.
- [Dashboard](../02_dashboard/index.md) — the panel beside the conversation.
