# Agent Dashboard and Transcript

A host that lets a model drive a workflow has to show what happened. This module provides the two halves of that:

- **`AgentTranscript`** — an ordered record of every turn, its answer, the model's reasoning and each tool call, maintained by the pipeline rather than by the host.
- **`AgentDashboardViewModel`** — a bindable projection of one scope: its tools, skills, MCP servers and sub-agents, with a switch per member.

It also carries the **media** path for attaching images, audio, video, documents and text to a user turn.

## Namespaces

| Namespace | Types |
|---|---|
| `VeloxDev.AI.Pipelines` | `AgentTranscript`, `AgentTranscriptEntry`, `AgentTranscriptRole`, `AgentMarkdownOptions`, `AgentEvent` family, `AgentPipeline`, `AgentPipelineAgent`, `IAgentPipelineStage`, `DelegateAgentPipelineStage`, `TextPipeline`, `ToolPipeline` |
| `VeloxDev.AI.Dashboard` | `AgentDashboardViewModel`, `AgentMemberViewModel`, `ToolMemberViewModel`, `SkillMemberViewModel`, `McpServerMemberViewModel`, `McpToolMemberViewModel` |
| `VeloxDev.AI` | `AgentMedia`, `AgentAttachment`, `AgentMediaReference`, `AgentMessage`, `AgentMediaOptions`, `IAgentMediaContent`, `IAgentMediaTranscoder`, `AgentMediaAgentExtensions` |

## Pages

- [Transcript](00_transcript/index.md) — the conversation record and its Markdown and JSON forms.
- [Event pipeline](01_event-pipeline/index.md) — the event vocabulary, the stage chain and the built-in stages.
- [Dashboard](02_dashboard/index.md) — the per-scope panel and its member rows.
- [Media](03_media/index.md) — validated multimodal input and the host transcoder seam.

## Evidence note

The transcript is exercised by the demo chat panels and by `TranscriptWiringTests`. The dashboard layer (`Agent/Dashboard/`) is covered by `AgentDashboardViewModelTests` but is **not bound by any demo** — the demos bind `McpScope.Status` directly. Treat the dashboard as a tested projection, not a shipped UI.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the scope the dashboard projects.
- [MCP Integration](../20_mcp-integration/index.md) — the status view-model the demos bind instead.
