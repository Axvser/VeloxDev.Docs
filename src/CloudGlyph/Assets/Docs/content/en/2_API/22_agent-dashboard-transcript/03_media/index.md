# Media

Multimodal input belongs in a **user message**, not in a tool result. On OpenAI-compatible chat completions a tool message has a text channel only, so media returned by a tool arrives as a base64 JSON string, not as pixels or sound. This layer validates media against its actual bytes, then builds the user message.

## Pages

- [AgentMedia and message building](00_AgentMedia/index.md) — the validated payload, the attachment record, URL references and the message builder.
- [Limits and transcoding](01_media-options/index.md) — accepted kinds and types, size and dimension limits, and the host codec seam.
- [Running with media](02_media-run/index.md) — validated `RunWithMediaAsync` / `RunStreamingWithMediaAsync` extensions.

## Type map

| Type | Role |
|---|---|
| `AgentMedia` | A payload validated from its bytes. |
| `AgentAttachment` | The display record (name, type, size) a transcript carries. |
| `AgentMediaReference` | A remote HTTP(S) payload the provider fetches. |
| `AgentMessage` | Builds the user `ChatMessage`. |
| `AgentMediaOptions` | Limits and transcode policy. |
| `IAgentMediaTranscoder` / `DelegateAgentMediaTranscoder` | The host codec seam. |
| `AgentMediaAgentExtensions` | Run helpers that validate first. |

## Related

- [Transcript](../00_transcript/index.md) — where attachments are shown.
- [Event pipeline](../01_event-pipeline/index.md) — `AgentTurnStarted` and `AgentMediaReceived` carry them.
