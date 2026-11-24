# SubAgentScope

`VeloxDev.AI.SubAgents.SubAgentScope : IAsyncDisposable` is the registry of children a scope spawned, the tools that manage them, and the narrowing rules that keep a child inside its parent's capabilities.

## Attachment to a workflow scope

| Member | Signature | Description |
|---|---|---|
| `WithSubAgents` | `WorkflowAgentScope WithSubAgents(SubAgentScope subAgents)` | Registers the subsystem's context provider. **Attach it before `CreateContextProviders()`**; attaching later leaves the model with none of the five dispatch tools. |
| `SubAgents` | `SubAgentScope? SubAgents { get; }` | The attached subsystem, or `null`. |

## Creating a subsystem

| Member | Signature | Description |
|---|---|---|
| Constructor | `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` | A factory receives the child's scope and returns a runnable agent over it. |
| Constructor | `SubAgentScope(Func<WorkflowAgentScope, string?, AIAgent> agentFactory, string? instructions = null)` | A factory that also receives the model a spawn asked for, or `null`. |
| `ForClient` | `static SubAgentScope ForClient(IChatClient client, string? instructions = null)` | Children are agents over one client, sharing the host's model. |
| `ForClientFactory` | `static SubAgentScope ForClientFactory(Func<string?, IChatClient> clientFactory, string? instructions = null)` | Picks a client per spawn from the requested model. Throwing from the factory refuses the spawn, and the refusal reaches the spawning agent as the child's failure. |

The library never holds a chat client of its own. Which model a child runs on is the host's decision, which is why the factory is the constructor's core.

## Roster and version

| Member | Type / Signature | Description |
|---|---|---|
| `Children` | `ObservableCollection<SubAgentStatusViewModel>` | The children spawned, oldest first, as bindable rows. |
| `Snapshot` | `IReadOnlyList<SubAgentSummary>` | Immutable copy, republished on the roster's thread when a child changes. Read this off the bound thread. |
| `Version` | `long` | Monotonic version of the roster and its rows; a provider caches its render on it. |
| `Changed` | `event EventHandler` | Raised whenever `Version` advances. |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | The provider that contributes the dispatch tools and roster per turn. |

## Limits

| Member | Type / Signature | Description |
|---|---|---|
| `SpawnBudget` | `int SpawnBudget { get; }` | The allowance assumed when the parent set no `WithMaxToolCalls`. Without it, "the parent's remaining allowance" would be undefined for an uncapped parent. |
| `WithSpawnBudget` | `SubAgentScope WithSpawnBudget(int budget)` | Sets `SpawnBudget`. Inherited by every scope spawned below this one. |
| `MaxDepth` | `int MaxDepth { get; }` | The deepest a spawned agent may sit: a direct child is depth 1. A scope at or past the limit cannot spawn. |
| `WithSubAgentDepth` | `SubAgentScope WithSubAgentDepth(int depth)` | Bounds tree depth. Inherited below this scope. |
| `WithSynchronizationContext` | `SubAgentScope WithSynchronizationContext(SynchronizationContext? context)` | The UI thread the roster is bound to. |

The budget already makes the tree terminate. A depth limit is what makes it *usable*: a root allowing 200 calls permits a 199-deep chain, which is bounded but pointless. Set both.

## Disposal

| Member | Signature | Description |
|---|---|---|
| `DisposeAsync` | `ValueTask DisposeAsync()` | Cancels every running child and waits for them to settle. The wait makes disposal a boundary rather than a race. |

## Budget contract

A child's scope is given the parent's ledger as its **outer ledger**, so every call anywhere in the tree is charged at the root.

1. The root's `WithMaxToolCalls` is the tree's total cap, not a per-agent cap.
2. Spawning three children does not divide the pot; each child receives a sub-limit, and the pot is enforced at call time.
3. A grant is clamped to at most one less than the parent's remaining allowance, so grants strictly decrease along any root-to-leaf path and every grant is at least one. Depth therefore terminates even without a depth limit.

## What a child inherits

A spawn that asks for nothing gets everything the parent currently offers: the same tools, skills and MCP servers, including the ability to dispatch in turn. A spawn that names a smaller set gets the **intersection** — never more than the parent has. Anything asked for beyond that is dropped and reported back in the spawn result. A child of an `AutoEdit` parent inherits `AutoEdit`; it cannot come away believing it holds a capability the parent was refused.

## Example

```csharp
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient)
    .WithSubAgentDepth(3)
    .WithSpawnBudget(40);

scope.WithSubAgents(subAgents);
var providers = scope.CreateContextProviders();
```

## Related

- [Dispatch tools](../01_dispatch-tools/index.md) — what the child can be asked to do.
- [Roster](../02_roster/index.md) — observing children.
