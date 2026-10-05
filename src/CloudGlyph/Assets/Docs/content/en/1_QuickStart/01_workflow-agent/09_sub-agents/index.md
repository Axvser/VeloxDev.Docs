# 09 · Dispatch Sub-Agents

The sub-agent subsystem lets one agent dispatch **background children** and hand each a narrowed slice of its own capabilities. It is a subsystem like MCP or Skills: one `With*` call attaches it, and it contributes its own tools and prompt text every turn.

```csharp
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient).WithSubAgentDepth(3);

scope.WithSubAgents(subAgents);   // attach BEFORE CreateContextProviders()
```

Source: `Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/AgentHelper.cs` (`ProvideAgent`).

Attach it **before** `CreateContextProviders()`. The five dispatch tools arrive as the subsystem's context-provider contribution, so attaching later leaves the model with none of them — the subsystem is unreachable however it was configured. The depth limit is not redundant with `WithMaxToolCalls`: the budget makes the tree terminate, but a root allowing 200 calls also permits a 199-deep chain, which is bounded and useless. Three levels is what the demo wants.

**Expected result:** before `WithSubAgents` the scope has one provider and no sub-agent tools; after it, the model is offered exactly `SpawnSubAgent`, `WaitSubAgents`, `GetSubAgentResult`, `ListSubAgents`, `CancelSubAgent`.

## 1. `SubAgentScope` — the subsystem

| Member | Signature | Notes |
|---|---|---|
| `ForClient` | `static SubAgentScope ForClient(IChatClient client, string? instructions = null)` | Builds the factory from a chat client — the host owns that client, the subsystem never does. |
| `SubAgentScope` | `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` | Custom factory form. |
| `WithSubAgentDepth` | `WithSubAgentDepth(int depth)` | Maximum nesting depth (default `int.MaxValue`); clamped `>= 0`; inherited by children. |
| `WithSpawnBudget` | `WithSpawnBudget(int budget)` | Stand-in allowance for an **uncapped** parent (default 64) so a descending grant stays finite. |
| `WithSynchronizationContext` | `WithSynchronizationContext(SynchronizationContext? context)` | Roster/UI thread. |
| `Children` | `ObservableCollection<SubAgentStatusViewModel> { get; }` | Direct children, oldest first, as bindable rows (UI thread only). |
| `Snapshot` | `IReadOnlyList<SubAgentSummary> { get; }` | Immutable, thread-safe copy of the roster — read this from anywhere but the UI thread. |
| `Version` | `long { get; }` | Monotonic roster version; the provider caches its render on it. |
| `Changed` | `event EventHandler?` | Raised whenever `Version` advances. |
| `CreateContextProvider` | `AIContextProvider CreateContextProvider(ToolPipeline? tools = null, AgentPipeline? pipeline = null)` | The provider the scope composes. |
| `DisposeAsync` | `ValueTask DisposeAsync()` | Cancels and **awaits** every running child, then clears the roster. Idempotent. |

## 2. The five tools

| Tool | Required parameter | Purpose |
|---|---|---|
| `SpawnSubAgent` | `task` | Dispatch a background child; returns immediately with its `id`. |
| `WaitSubAgents` | — (`ids?`, `timeoutMs?` default 60000) | Wait for named/all-running children; returns rows with `state`, `callCount`, a truncated `result` (limit 4000, `"truncated":true`), `error`, `dropped`. |
| `GetSubAgentResult` | `id` | The full, untruncated report. |
| `ListSubAgents` | — | Lists **this scope's own** children (task preview truncated to 120 chars); `count` + `running`. |
| `CancelSubAgent` | `id` | Cancels a child; reads as `Cancelled`, not a failure. |

Dispatch is **dispatch-and-poll, never call-and-wait** — a spawn happens inside a tool call on the host's UI thread, so it returns an id and the parent polls. `SpawnSubAgent` is the only tool whose `task` is required; every capability is optional. Source: `SubAgentToolSchemaTests`.

The success payload:

```text
{"status":"ok","id":"...","name":"...","depth":1,"maxToolCalls":19,
 "grantedToolCount":67,"grantedSkillCount":7,"grantedMcpServerCount":1,
 "dropped":[],"message":"..."}
```

**Expected result:** a spawn returns `status:"ok"` with an `id` and `depth:1`; `WaitSubAgents` on that id later returns `state:"Completed"` with the child's `result`.

## 3. Capability narrowing — the parent is the ceiling

Every request a spawn carries is **intersected with what the parent actually has**, and whatever is dropped is reported back in the spawn's own `dropped` array — so the child cannot believe it holds something it was refused.

| Spawn parameter | Narrowing rule |
|---|---|
| `allowedTools` | Intersect with the parent's current surface. Omitted ⇒ inherit all; an empty array ⇒ grant none. Every parent tool **not** granted is switched off on the child. |
| `allowedSkills` | Intersect with the parent's enabled skills. Omitted ⇒ inherit; an empty array ⇒ grant none **and** drop the skill tools too. A skill the parent switched off is not grantable. |
| `allowedMcpServers` | Intersect with the parent's loaded servers; the granted server arrives **without** the load/unload/add switches that would change it. |
| `maxToolCalls` | Clamped to the parent's remaining allowance **minus one**, so grants strictly decrease along every root-to-leaf path (guaranteeing termination). Asking beyond the remainder is clamped and reported. |
| `maxReadToolCalls` / `maxWriteToolCalls` | `Math.Min` of the request and the parent's cap; a cap the parent does not have cannot be handed down. |
| `allowNodeExecution` | Opt-in on **both** sides: asking when the parent lacks it is dropped, not granted. |
| `allowedGenericCommands` | Filtered by the parent's allowlist. |
| `autoMarkDirty` | Inherited from the parent, never granted beyond it. |

Interaction configuration (safety level, per-level prompts, both handlers) travels whole via `GrantInteractionTo`, so the child's `RequestSelection` / `RequestConfirmation` / `ResetToolCallLimit` are usable rather than advertised-but-dead. Custom tools are copied as a **subset with only the guidance for the tools the child actually holds**. Source: `SubAgentNarrowingTests`, `SubAgentCapabilityGrantTests`.

**Expected result:** a spawn naming a tool the parent switched off reports it in `dropped` and the child does not hold it; a silent spawn holds everything the parent has.

## 4. One pot, not one per agent

A child's allowance is a **share of its parent's**, not a second budget beside it. The toolkit's `ToolCallLedger` is chained: `child.ParentLedger = parentLedger` before the child's toolkit exists, and `Spend` walks the chain, so the outermost ledger's total is the number of calls made anywhere in the tree. Spawning three children does not divide the pot — it bounds each. The clamp in §3 is what makes depth bounded: a root allowing N terminates an N-1-deep chain, hence `WithSubAgentDepth` for usability.

When a child hits a wall, the refusal sends it to `ResetToolCallLimit` **and** tells it to report upward (a dispatcher is suspended on its result). The reset reaches the user exactly as the parent's does, and reopening zeroes the whole chain. Source: `SubAgentBudgetTests` (e.g. `AChildsCalls_AreCountedOnTheRootsLedger`, `AChildsReset_ReachesTheUser_AndReopensTheWholeTree`).

**Expected result:** with a root cap of 6 and two children granted 3 and 2, the second child's refusal mentions the *session's* tool-call budget; total spend stays 6.

## 5. State, tokens and the tree panel

`SubAgentState` is `Queued`, `Running`, `Completed`, `Failed`, `Cancelled` — `Cancelled` is its own value, not a flavour of `Failed`. `SubAgentSummary` is the immutable row; `SubAgentStatusViewModel` is the bindable one (`StateText` in Chinese, `DurationText`, `TokensText`).

Two separate consumption figures:

- **Calls aggregate up.** `CallCount` includes everything the child spawned.
- **Tokens aggregate down.** `TokensUsed` / `InputTokens` / `OutputTokens` are the child's **own** spend; `SubAgentTreeNodeViewModel.SubtreeTokens` sums them bottom-up. A provider that reports no usage leaves the figure `null` — "not measured", never a fake `0`.

`SubAgentTreeViewModel(scope)` projects the flat per-scope rosters into one bindable tree (`Roots`, `TotalCount`, `RunningCount`, `FailedCount`, `SubtreeTokens`), reconciling in place so expanded state survives rebuilds. `TickElapsed()` refreshes elapsed times — the library owns no timer, the host drives it.

**Expected result:** the tree's `ScopeRoot.SubtreeTokens` equals the sum of every descendant's `TokensUsed`; a child that reports no usage shows no token text rather than `0`.

## Run declaration

- ✅ Actually built and ran — the deterministic agent test suite (2026-10-01, `已通过! 失败: 0，通过: 387`) includes all `SubAgents/**` except `SubAgentLiveTests`. It covers the narrowing rules, the one-pot ledger, depth clamping, the dispatch/poll contract, cancellation, token metrics and the tree view-models.
- ⚠️ `SubAgentLiveTests` (a real model dispatching a real child) needs `API_KEY_DEEPSEEK` and is non-deterministic; it is **excluded** and no claim here rests on it.
