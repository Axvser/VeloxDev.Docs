# Workflow Agent — Sub-Agents: State & Roster Rows

One enum and two classes describe where a spawned child is and what it was given. They are deliberately a pair: `SubAgentStatusViewModel` is the bindable row that lives on the roster's thread, `SubAgentSummary` is the immutable copy anything else reads. All three live in `VeloxDev.AI.SubAgents` (`Agent/SubAgents/SubAgentStatus.cs`, `.../SubAgentStatusViewModel.cs`).

## Enum: `SubAgentState`

| Value | Meaning |
|---|---|
| `Queued` | Accepted, but its background run has not started yet. |
| `Running` | Running in the background. |
| `Completed` | Finished and produced a result. |
| `Failed` | Finished by throwing. |
| `Cancelled` | Stopped on request — by the host, by its parent, or because the tree is being disposed. |

`Cancelled` is deliberately its own value rather than a flavour of `Failed`: a child stopped by the host or by its parent did not go wrong, and a panel that painted it red would teach the user to distrust a control that worked. `SubAgentDispatchTests.CancellingAChild_ReadsAsCancelled_NotAsFailed` and `SubAgentTreeViewModelTests.AStoppedChild_IsNotCountedAsAFailedOne` pin that.

## Class: `SubAgentSummary`

`public sealed class SubAgentSummary` — an immutable copy of one sub-agent's state, safe to read from any thread. The same arrangement as `McpServerSummary`: a row view-model is bound to the UI thread and cannot be enumerated from elsewhere, while an agent invocation and a panel's rebuild both need to read the roster from threads the host does not control.

| Property | Type | Notes |
|---|---|---|
| `Id` | `string` | The handle a spawn returned, and what every other tool takes. |
| `Name` | `string` | The task's display title — what the spawn asked for, or a numbered stand-in. A title, not an identifier: its consumer is the person watching the panel. |
| `ParentId` | `string?` | The id of the sub-agent that spawned this one, or `null` for a child of the host's own scope. This is the whole of the parent/child relation: the roster is flat and the tree is a projection of it. |
| `Depth` | `int` | 1 for a child of the root scope, 2 for a grandchild. |
| `Task` | `string` | The task the spawn was asked to carry out. |
| `State` | `SubAgentState` | Where the run is. |
| `StateText` | `string` | Localized state text, matching `SubAgentStatusViewModel.StateText`. |
| `Result` | `string?` | What the child answered, once it has finished. |
| `Error` | `string?` | Why it failed, or `null`. |
| `CallCount` | `int` | How many tool calls the child **and everything it spawned** have made. |
| `MaxToolCalls` | `int?` | The cap granted at spawn time, or `null` for none. |
| `TokensUsed` | `long?` | The child's **own** runs' token total, or `null` when the provider reported none. A parent's total is the sum over the tree, which only the tree can compute — see `SubAgentTreeNodeViewModel.SubtreeTokens`. |
| `InputTokens` / `OutputTokens` | `long?` | The two halves of `TokensUsed`, when the provider splits them. |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | The run's span. |
| `GrantedToolCount` / `GrantedSkillCount` / `GrantedMcpServerCount` | `int` | How many of each the child was actually given. Zero skills is also what a child with no skill provider reports. |
| `DroppedRequests` | `IReadOnlyList<string>` | What the spawn asked for and did not get, one line each. Carried into the summary rather than only into the spawn's own reply, because a panel showing a child that quietly has fewer abilities than it asked for is exactly the failure this reporting exists to prevent. |

Derived helpers: `IsRunning` (state is `Queued` or `Running`), `IsFinished` (its deliberate pair, so a consumer does not have to negate by hand and get it wrong when a new state is added), `HasError`, `HasResult`, `HasTokens`, and `Duration`.

Three of these exist to keep "not measured" apart from "zero":

- `HasTokens` is `TokensUsed is not null`. False is the ordinary case for a provider that reports no usage at all — a panel must show nothing rather than a zero it did not measure. `SubAgentMetricsTests.AProviderThatReportsNothing_IsNotAZero` pins it.
- `HasError` / `HasResult` are **tested rather than compared with `null`**, because `Error` and `Result` carry the row's default of the empty string for a child that succeeded — a distinction no consumer should have to know.
- `Duration` is `(FinishedAt ?? DateTimeOffset.Now) - StartedAt`, floored at zero. Measured against the clock while the child is running, so a caller that re-reads the same summary gets a larger span — and `Snapshot` does not republish merely because time passed. Read it, do not cache it.

## Class: `SubAgentStatusViewModel`

`public sealed partial class SubAgentStatusViewModel` — one spawned sub-agent as a bindable row, MVVM source-generated (`[VeloxProperty]`). Written on whatever thread the roster is marshalled to, and read by the tree panel, which lives on that thread.

| Constructor | Signature | Notes |
|---|---|---|
| | `internal SubAgentStatusViewModel(string id, string name, string? parentId, int depth, string task)` | **Internal** — a row is created by the roster, never by a host. |

| Property | Type | Notes |
|---|---|---|
| `Id` / `ParentId` / `Depth` | `string` / `string?` / `int` | Get-only, set at construction. |
| `Transcript` | `AgentTranscript? { get; internal set; }` | The child's own conversation, once its scope has one. Held rather than copied: a second transcript would be a second source of truth. |
| `Name` | `string` | The task title. |
| `Task` | `string` | The task text. |
| `State` | `SubAgentState` | Writing it raises `StateText`, `IsRunning`, `IsFinished`. |
| `Result` / `Error` / `Notes` | `string` | Default `""`, never null. |
| `CallCount` | `int` | Refreshed from the child's ledger before a roster render and before a wait returns. |
| `MaxToolCalls` | `int?` | The granted cap. |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | Both notify `Duration` / `DurationText`, because a row re-run in place would otherwise pair a fresh start with a stale finish. |
| `TokensUsed` / `InputTokens` / `OutputTokens` | `long?` | Token figures, only ever written on a **successful** finish. |
| `GrantedTools` / `GrantedSkills` / `GrantedMcpServers` / `DroppedRequests` | `ObservableCollection<string>` | Populated at spawn time and **never revised** — rewriting what a running child was granted would be a lie about its history. |

Derived: `StateText` (`排队中` / `运行中` / `已完成` / `失败` / `已取消` / `未知`), `IsRunning`, `IsFinished`, `HasError`, `HasResult`, `HasDroppedRequests`, `GrantedSummary` (`无工具` when empty, otherwise the granted tool names joined with `、`), `Duration`, `DurationText` (`N秒` / `N分N秒` / `N小时N分`), `HasTokens`, `TokensText` (exact below 1000, then `N.Nk`, then `N.NNM`).

| Method | Signature | Notes |
|---|---|---|
| `NotifyElapsed` | `void NotifyElapsed()` | Tells a bound panel that `Duration` / `DurationText` have moved. Called by whoever drives the clock — `SubAgentTreeViewModel.TickElapsed` is the shipped caller. **The library owns no timer**: a panel that ticks and a process that hosts one are different lifetimes, and a timer started here would belong to neither cleanly. |

## Where these fields are written

The roster writes a row in three places, and the order is load-bearing in two of them:

- On spawn: `StartedAt` **before** `State`, and never the other way round. `State` is a bindable property, so assigning it publishes the row — and a consumer reading on that notification would otherwise see a child that is running with no start time.
- On finish: the payload (`Result` / `Error` / token figures) **before** `State`, for the same reason. A signal that arrives before the thing it announces is a lie about the row it belongs to.
- On cancellation or failure the token figures are left `null` rather than set to zero: the response those paths would have measured no longer exists, and `HasTokens` is what keeps "not measured" and "spent nothing" apart in the UI.

> Source: `SubAgentStatus.cs` (enum + summary), `SubAgentStatusViewModel.cs` (row), and `SubAgentScope.cs` lines 781-839 (`RunAsync` / `Finish`). Tests: `SubAgentMetricsTests`, `SubAgentDispatchTests`, `SubAgentCapabilityGrantTests` under `Src/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/`.
