# Running with media

`VeloxDev.AI.AgentMediaAgentExtensions` runs an agent with multimodal content attached to the user message, validating it first. The overloads exist so a host does not hand-build the message and forget the kind/media-type check, the size limits or the transcoder. A rejected payload fails before any request is made.

## Methods

| Method | Signature | Description |
|---|---|---|
| `RunWithMediaAsync` | `Task<AgentResponse> RunWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<AgentMedia> media, AgentMediaOptions? options = null, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | Validates the payloads (converting when needed) and runs non-streaming. The prompt may be empty when at least one payload is present. |
| `RunWithMediaAsync` | `Task<AgentResponse> RunWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<IAgentMediaContent> media, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | Runs with already-validated payloads or URL references. |
| `RunStreamingWithMediaAsync` | `IAsyncEnumerable<AgentResponseUpdate> RunStreamingWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<AgentMedia> media, AgentMediaOptions? options = null, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | Validates and streams the answer. |
| `RunStreamingWithMediaAsync` | `IAsyncEnumerable<AgentResponseUpdate> RunStreamingWithMediaAsync(this AIAgent agent, string prompt, IEnumerable<IAgentMediaContent> media, AgentSession? session = null, AgentRunOptions? runOptions = null, CancellationToken cancellationToken = default)` | Streams with already-validated payloads or references. |

## Parameters

| Parameter | Type | Description |
|---|---|---|
| `agent` | `AIAgent` | The agent to run. |
| `prompt` | `string` | The text; empty allowed when at least one payload is present. |
| `media` | `IEnumerable<AgentMedia>` or `IEnumerable<IAgentMediaContent>` | Payloads in display order. |
| `options` | `AgentMediaOptions?` | Limits and transcoder; shipped defaults when null. |
| `session` | `AgentSession?` | The session to continue, or `null` for a fresh run. |
| `runOptions` | `AgentRunOptions?` | Framework run options. |
| `cancellationToken` | `CancellationToken` | Cancels the run or conversion. |

## Exceptions

| Exception | Condition |
|---|---|
| `AgentMediaException` | A payload cannot be made acceptable; `Error` names why. |

## Example

```csharp
using VeloxDev.AI;

var image = await AgentMedia.FromFileAsync("preview/frame.png");
var note = await AgentMedia.FromFileAsync("audio/note.mp3");
var options = AgentMediaOptions.CreateVisionDefault();

await foreach (var update in agent.RunStreamingWithMediaAsync(
    "Check the frame and the voice note.", new[] { image, note }, options, session))
{
    // each payload travels as its own image_url / input_audio / file block
}
```

A model that does not accept a media kind rejects the part, so keep a text-only fallback for such endpoints.

## Related

- [AgentMedia and message building](../00_AgentMedia/index.md) — building the message by hand.
- [Limits and transcoding](../01_media-options/index.md) — the `options` argument.
