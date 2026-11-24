# Context provider

`VeloxDev.AI.SubAgents.SubAgentAgentContextProvider : AIContextProvider` contributes the subsystem to an agent invocation: what the model is told about dispatching children, the five dispatch tools, and — for an agent that was itself spawned — the facts of its own dispatch.

## Class: SubAgentAgentContextProvider

| Member | Signature | Description |
|---|---|---|
| Constructor | `SubAgentAgentContextProvider(SubAgentScope scope, ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | Creates a provider over a subsystem. Omit `tools` for standalone use; then a thread-only policy is derived from the parent scope's synchronization context. |
| `StateKeys` | `override IReadOnlyList<string> StateKeys` | The provider's state keys. |
| `ProvideAIContextAsync` | `protected override ValueTask<AIContext> ProvideAIContextAsync(InvokingContext context, CancellationToken cancellationToken)` | Renders and contributes the sub-agent state. |

The render is cached on the scope's `Version`, which advances whenever the roster or any row changes, so a child finishing reaches the model on the next turn without rebuilding the agent.

## Notes

- **No language dimension.** The subsystem's own text is written once in both languages rather than following the workflow prompt language, because a sub-agent's briefing is read by the model, not by the user.
- **Attach before creating providers.** `scope.WithSubAgents(...)` must run before `CreateContextProviders()`. Attaching later leaves the model with none of the five tools.
- **Pass the host's tool policy.** A composing host passes the same `ToolPipeline` it gives every other source, so the spawn is charged to the same budget. Omit it only when assembling providers by hand.

## Example

```csharp
scope.WithSubAgents(subAgents)
     .WithSynchronizationContext(SynchronizationContext.Current);

var providers = scope.CreateContextProviders();
```

## Related

- [SubAgentScope](../00_sub-agent-scope/index.md) — the subsystem this provider renders.
- [Dispatch tools](../01_dispatch-tools/index.md) — the tools it contributes.
- [Skill tools](../../19_agent-context-skills/04_skill-tools/index.md) — the same provider pattern for another subsystem.
