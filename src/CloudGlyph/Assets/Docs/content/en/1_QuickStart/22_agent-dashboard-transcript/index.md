# Agent Dashboard and Transcript

A host that lets a model drive a workflow has to show what happened. This module provides the two halves of that:

- **`AgentTranscript`** — an ordered record of every turn, its answer, the model's reasoning and each tool call, maintained by the pipeline rather than by the host.
- **`AgentDashboardViewModel`** — a bindable projection of one scope: its tools, skills, MCP servers and sub-agents, with a switch per member.

It also carries the **media** path for attaching images, audio, video, documents and text to a user turn.

## What you will build

- an `AgentTranscript` filled from a pipeline and exported as Markdown and JSON;
- an `AgentDashboardViewModel` over a scope, reporting each subsystem's summary;
- a validated media message for a model that accepts it.

## Pages

- [Setup](00_setup/index.md) — prerequisites, the package, and the transcript and dashboard objects.
- [Usage](01_usage/index.md) — the transcript API, the event pipeline, the dashboard rows, media, verification, and the complete program.

## Evidence note

The transcript is exercised by the demo chat panels and by `TranscriptWiringTests`. The dashboard layer (`Agent/Dashboard/`) is covered by `AgentDashboardViewModelTests` but is **not bound by any demo** — the demos bind `McpScope.Status` directly. Treat the dashboard as a tested projection, not as a shipped UI.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the scope the dashboard projects.
- [MCP Integration](../20_mcp-integration/index.md) — the status view-model the demos bind instead.
