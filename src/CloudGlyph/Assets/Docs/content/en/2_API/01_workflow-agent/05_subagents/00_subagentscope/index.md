# Workflow Agent — Sub-Agents: `SubAgentScope`

`public sealed class SubAgentScope : IAsyncDisposable` — the sub-agent subsystem: the registry of the agents a scope spawned, the tools that manage them, and the narrowing rules that keep a child inside its parent's capabilities. Declared in `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentScope.cs`.

| Member | Signature | Notes |
|---|---|---|
| `SubAgentScope` | `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` | Builds each child agent with `agentFactory`. Throws `ArgumentNullException` when it is null. `instructions` is the child's standing preamble; omitted, a compact default is used. |
| `ForClient` | `static SubAgentScope ForClient(IChatClient client, string? instructions = null)` | A subsystem whose children are agents over `client`, sharing the host's model. Throws `ArgumentNullException` when `client` is null. |
| `SpawnBudget` | `int { get; }` | The allowance assumed for a spawn when the parent scope set no `WithMaxToolCalls`. **Default 64.** Inherited by every scope spawned below this one. |
| `WithSpawnBudget` | `SubAgentScope WithSpawnBudget(int budget)` | Sets `SpawnBudget`, clamped to at least 1. Returns `this`. |
| `MaxDepth` | `int { get; }` | Deepest a spawned agent may sit; a child of the attached scope is depth 1. **Default `int.MaxValue`.** |
| `WithSubAgentDepth` | `SubAgentScope WithSubAgentDepth(int depth)` | Bounds how deep the tree may go, clamped to at least 0. Returns `this`. |
| `WithSynchronizationContext` | `SubAgentScope WithSynchronizationContext(SynchronizationContext? context)` | The thread the roster is bound to; `null` writes it on whatever thread the spawn or completion runs on. Returns `this`. |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | Builds the provider that contributes the management tools and the roster each turn. Omit `tools` for standalone use — the provider then derives a thread-only policy from the parent scope's context. |
| `Children` | `ObservableCollection<SubAgentStatusViewModel> { get; }` | The child agents this scope spawned, oldest first, as bindable rows. **Bound to the roster thread.** |
| `Snapshot` | `IReadOnlyList<SubAgentSummary> { get; }` | Immutable copy of `Children`, republished on the roster's thread whenever a child changes. Read this — not `Children` — from anywhere else. |
| `Version` | `long { get; }` | Monotonic version of the roster and its rows; a context provider caches its render on it. |
| `Changed` | `event EventHandler?` | Raised whenever `Version` advances. |
| `DisposeAsync` | `ValueTask DisposeAsync()` | Cancels every running child and waits for them to settle, then detaches the rows. Idempotent. |

## Construction

`ForClient` is the factory the library supplies; its body is exactly the documented custom-factory shape, so a host that wants children on a different model writes the same lambda:

```csharp
// ForClient, verbatim in shape — SubAgentScope.cs lines 160-166
scope => client
    .AsAIAgent(scope.CreateContextProviders(), instructions ?? DefaultInstructions)
    .WithPipeline(scope.Pipeline)
```

The default preamble is `SubAgentScope.DefaultInstructions` (**internal**): a few hundred bytes telling the child it was dispatched in the background to carry out one task, that it should decide and proceed rather than ask, and that the tools it holds are the whole of what it may use. It is deliberately *not* the workflow skeleton, which is a per-scope megabyte.

> `SubAgentScope.DefaultInstructions` is `internal const string` — verified against `SubAgentScope.cs` lines 173-179. A host cannot read it, only rely on `ForClient`. **No test asserts its text or its length** — the description above is *inferred* from reading the constant, not from a behavior a test pins. What *is* pinned is that a spawn works with the default in place (`SubAgentToolSchemaTests.ASpawnThatNamesOnlyItsTask_IsAccepted` drives `ForClient`'s default through a real spawn).

## Attach and identity

`Attach(WorkflowAgentScope parent)` is **internal**, called by `WorkflowAgentScope.WithSubAgents`. There is nothing for a host to do with it; the effect is that `SubAgentScope.Parent` (internal) stops being null and `CreateContextProvider()` starts contributing. Building the provider before attaching is tolerated: `SubAgentAgentContextProvider.BuildContext()` returns an empty `AIContext` (both `Instructions` and `Tools` null) rather than throwing — pinned by `SubAgentHierarchyTests.AnUnattachedSubsystem_ContributesNothing`.

Each instance carries an internal `InstanceId` (a `Guid`, **not** the workflow scope's `StateDiscriminator`). The discriminator is derived from the tree, and a parent and its child sit on the *same* tree, so it would collide on exactly the pair that must not. `SubAgentHierarchyTests.TwoScopes_NeverShareAStateKey` and `TwoProvidersOverOneScope_DoShareAKey` pin both directions.

## Spawning and the allowance

`TrySpawn(SubAgentRequest request, out string? refusal)` is **internal** — the model reaches it only through `SpawnSubAgent`. Its arithmetic:

| Step | Rule | Line |
|---|---|---|
| Disposal gate | refused once `DisposeAsync` has run | 394-397 |
| Depth gate | refused when `Depth >= MaxDepth`; the refusal names the limit | 399-404 |
| Remaining | `min((parent.MaxToolCalls ?? SpawnBudget) - ledger.Usage.ToolCalls, rootCap - rootUsage)` | 694-706 |
| Grant | `min(request.MaxToolCalls ?? remaining, remaining - 1)`; below 1 the spawn is **refused** rather than granted zero | 409-417 |
| Clamp report | a requested budget above the grant adds a `maxToolCalls` line to `dropped` | 418-419 |

`SubAgentRequest` (internal) mirrors the `SpawnSubAgent` parameters one-for-one. Every narrowing field is **nullable, and nullable means inherit**: `null` inherits, an empty array grants nothing, and naming is the only subtraction. `AllowedSkills` and `AllowedMcpServers` share that default — the parent's switched-on set.

Because the grant is always at most one less than what the parent has left, grants strictly decrease down every root-to-leaf path, so an arbitrarily deep tree terminates and cannot be deeper than the root's allowance. `SubAgentBudgetTests` and `SubAgentHierarchyTests` state that as arithmetic (`10 → 9`; `40 → 39 → 38 → 37`). Termination is not usability: a root allowing 200 calls permits a 199-deep chain, which is why `WithSubAgentDepth` exists.

## Operations behind the toolkit

| Member | Signature | Behavior |
|---|---|---|
| `List` | `IReadOnlyList<SubAgentSummary> List()` — internal | Refreshes call counts from every child's ledger, republishes, returns the snapshot. |
| `GetResult` | `SubAgentSummary? GetResult(string id)` — internal | One child's current state, or `null` when this scope never issued that handle. |
| `WaitAsync` | `Task<(IReadOnlyList<SubAgentSummary> Rows, bool TimedOut)> WaitAsync(string[]? ids, int timeoutMs)` — internal | `Task.WhenAll` over the named children against a delay; whether it timed out is decided by **reference** comparison, since both tasks complete successfully. |
| `Cancel` | `SubAgentSummary? Cancel(string id)` — internal | Cancels a running child; the child's own catch settles the row. |
| `SubAgentsOf` | `SubAgentScope? SubAgentsOf(string id)` — internal | The subsystem of the child a row stands for — the edge the tree walks. |

A handle table is **per scope**: `Select`/`Find` look only at this scope's entries, so a named id this scope never issued is *skipped*, not refused. A model that names a sibling's child gets an empty roster rather than a peek at another branch — pinned by `SubAgentDispatchTests.AChildSeesItsOwnChildren_AndNobodyElses`.

`SubAgentsOf` is what links a flat roster to a tree: the records are held per scope — which is what makes a child unable to see its siblings, since it only reads its own — so a row cannot name its parent by looking one up. The spawn that creates a child's scope writes its own row's id into the child scope's internal `SelfId`, and every child of that scope points at it. The tree is therefore built from rows alone.

## Disposal

`DisposeAsync` cancels every running child and **awaits** each run, then unsubscribes the rows and clears `Children`. Awaited rather than fired off: a child's tool calls are marshalled onto the host's UI thread, so a host that tore its dispatcher down while children were in flight would have them post into a pump that no longer exists. After disposal no further spawn is accepted (`SubAgentDispatchTests.AfterDisposal_NothingMoreCanBeSpawned`) and a second call is harmless (`DisposingTwice_IsHarmless`).

> Source: `SubAgentScope.cs`. Tests: `SubAgentDispatchTests`, `SubAgentBudgetTests`, `SubAgentHierarchyTests`, `SubAgentNarrowingTests` under `Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/`.
