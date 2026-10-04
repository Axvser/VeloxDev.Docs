# 10 · Skills & Pipelines

Two subsystems that sit beside MCP and sub-agents:

- **Skills** (`VeloxDev.AI.Skills`) — a library of Agent Skills the model can discover, load, switch off and read resources from. `scope.WithSkills(...)` attaches it; the four skill tools and the skill corpus arrive per turn.
- **Pipelines** (`VeloxDev.AI.Pipelines`) — the observability chain every agent run flows through. `scope.Pipeline` is composed for you and feeds an `AgentTranscript`; `scope.WithTranscript(...)` attaches the conversation.

## Sub-pages

- [Skills](00_skills/index.md) — `SkillScope`, `SkillAgentToolkit`, embedded vs file skills, the descriptor/state model, the four tools.
- [Pipelines](01_pipelines/index.md) — `AgentPipeline`, the `AgentEvent` hierarchy, `ToolPipeline`, `AgentTranscript` and the overloads that wire them.

**Expected result:** with both attached, the turn's tool list carries the four skill tools and each call lands in the transcript as a `ToolCall` entry.
