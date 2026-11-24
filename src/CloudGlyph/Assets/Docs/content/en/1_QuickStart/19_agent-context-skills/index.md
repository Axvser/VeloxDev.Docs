# Agent Context and Skills

An agent editing a workflow needs two kinds of knowledge: what the framework is (types, commands, defaults), and how to carry out a multi-step job (create a node, wire a slot enumerator, lay out a graph). VeloxDev supplies both through **context providers** and a **skills subsystem**.

Context is rendered in layers so the prompt stays stable. Skills are switchable documents — embedded in the package or discovered on disk — that the model loads only when it needs them.

## What you will build

- a scope configured with a prompt language and automatic discovery;
- a `[AgentContext]` description rendered for one component type;
- a `SkillScope` that discovers the seven embedded workflow skills, disables one, and rebuilds the prompt block.

## Pages

- [Setup](00_setup/index.md) — prerequisites, the package, discovery, and context annotations.
- [Usage](01_usage/index.md) — the prompt layers, the skills subsystem, verification, and the complete program.

## Context versus skills

| Source | Carries | Changes |
|---|---|---|
| Static skeleton | behavioral constraints, references, type catalogue | never after construction |
| Capability envelope | gates, switched-off tools, budgets, drift | per configuration change |
| Skills | one procedure per document, plus bundled resources | whenever a skill is switched |
| MCP | server inventory and tools | whenever a server is loaded |

The skeleton is rendered once; the other three are contributed per turn. Putting a per-turn source into the skeleton would either rebuild a large prompt every turn or freeze text that must change.

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the tools the context describes.
- [MCP Integration](../20_mcp-integration/index.md) — the fourth per-turn source.
