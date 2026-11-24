# Agent Context and Skills

An agent editing a workflow needs two kinds of knowledge: what the framework is, and how to carry out a multi-step job. VeloxDev supplies the first as **context blocks** rendered from the compiled agent-context tree, and the second as **skills** — switchable documents embedded in the package or discovered on disk.

Context is layered so the prompt stays stable. Skills are loaded only when the model needs them, either injected in full (embedded) or advertised by name and fetched on demand (file).

## Namespaces

| Namespace | Types |
|---|---|
| `VeloxDev.AI` | `AgentContextAttribute`, `AgentLanguages`, `AgentLanguagesExtensions`, `AgentEmbeddedResources` |
| `VeloxDev.AI.Workflow` | context members of `WorkflowAgentScope`, `AgentContextCollector` |
| `VeloxDev.AI.Skills` | `SkillScope`, `SkillStatusViewModel`, `SkillsViewModel`, `SkillSummary`, `SkillDescriptor`, `SkillState`, `SkillSourceKind`, `ISkillSource`, `EmbeddedSkillSource`, `FileSkillSource`, `SkillAgentToolkit`, `SkillAgentContextProvider` |

## Pages

- [Context scope](00_context-scope/index.md) — prompt language, type registration, prompt shapes, and the context collector.
- [Skills scope](01_skills-scope/index.md) — discovery, enable/disable, rendering and attachment.
- [Skill status](02_skill-status/index.md) — the bindable skill rows and thread-safe summaries.
- [Skill sources](03_skill-sources/index.md) — embedded and on-disk sources and the `SKILL.md` frontmatter.
- [Skill tools](04_skill-tools/index.md) — the four model-facing skill tools, their provider, and embedded resource reading.

## Prompt layers

| Source | Carries | Changes |
|---|---|---|
| Static skeleton | behavioral constraints, references, type catalogue | never after construction |
| Capability envelope | gates, switched-off tools, budgets, drift | per configuration change |
| Skills | one procedure per document, plus bundled resources | whenever a skill is switched |
| MCP | server inventory and tools | whenever a server is loaded |

The skeleton is rendered once; the other three are contributed per turn.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the tools the context describes.
- [MCP Integration](../20_mcp-integration/index.md) — the fourth per-turn source.
