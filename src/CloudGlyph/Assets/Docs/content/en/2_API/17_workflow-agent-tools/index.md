# Workflow Agent Tools

`WorkflowAgentScope` turns one workflow tree into a Microsoft Agent Framework tool surface. The built-in tools cover inspection, structural edits, execution, layout, analytics and state; every call is wrapped so it is counted, gated and reported through the scope's own pipeline.

The scope is the entry point for every other agent feature. This page documents its tool-facing members and the workflow toolkit; the safety gate, prompt context, skills, MCP, sub-agents and transcript each own the members they introduce.

## Namespaces

| Namespace | Types |
|---|---|
| `VeloxDev.AI.Workflow` | `WorkflowAgentScope`, `WorkflowAgentToolkit` (via `CreateToolkit`), `WorkflowAgentSelectionExtensions`, `WorkflowStateTracker`, `WorkflowValidation`, `IWorkflowTreeValidator`, `WorkflowValidationIssue`, `AgentContextCollector` |
| `VeloxDev.AI.Workflow.Functions` | `WorkflowAgentToolkit`, `WorkflowToolCategory`, `CommandInvoker`, `CommandDescriptor`, `ComponentPatcher`, `TypeIntrospector` |
| `VeloxDev.AI` | `AgentToolCallEventArgs`, `IAgentToolCallNotifier`, `AgentClientExtensions`, `AgentObjectToolkit`, `AgentTelemetryExtensions` |

## Pages

- [WorkflowAgentScope](00_workflow-agent-scope/index.md) — the scope's identity, tool registration, session wiring and providers.
- [WorkflowAgentToolkit](01_workflow-agent-toolkit/index.md) — the toolkit and the complete built-in tool catalogue by category.
- [Selection and state](02_selection-and-state/index.md) — prompt-side node selection and the snapshot/diff tracker.
- [Validation and support](03_validation-and-support/index.md) — domain validators, command discovery, JSON patching and type schemas.
- [General agent extensions](04_general-agent-extensions/index.md) — provider mounting, the generic object toolkit and OpenTelemetry wiring.

## Related

- [Agent Safety and Budgets](../18_agent-safety-budgets/index.md) — the permission gate and call budgets every tool call passes through.
- [Agent Context and Skills](../19_agent-context-skills/index.md) — the prompt text that describes these tools and their types.
- [MCP Integration](../20_mcp-integration/index.md) — external tools joining the same per-turn set.
- [Sub-Agents](../21_sub-agents/index.md) — dispatch tools that inherit this toolkit.
- [Agent Dashboard and Transcript](../22_agent-dashboard-transcript/index.md) — observing what the tools did.
