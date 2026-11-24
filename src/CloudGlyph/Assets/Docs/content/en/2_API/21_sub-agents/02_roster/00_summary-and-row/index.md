# Summary and row

Two shapes describe one child: an immutable summary safe to read from any thread, and a bindable row written on the roster's thread. They are kept apart because an agent invocation and a UI panel read from threads neither controls.

## Enum: SubAgentState

| Member | Meaning |
|---|---|
| `Queued` | Created, not yet running. |
| `Running` | Working. |
| `Completed` | Finished with a result. |
| `Failed` | Finished with an error. |
| `Cancelled` | Stopped on purpose. Deliberately distinct from `Failed`: a child stopped by the host or its parent did not go wrong. |

## Class: SubAgentSummary

An immutable copy of one child's state.

| Member | Type | Description |
|---|---|---|
| `Id` | `string` | The handle a spawn returned, and what every other tool takes. |
| `Name` | `string` | The task's display title, or a numbered stand-in. |
| `ParentId` | `string?` | The spawning child's id, or `null` for a child of the root scope. |
| `Depth` | `int` | 1 for a direct child of the root scope, 2 for a grandchild. |
| `Task` | `string` | The task the spawn was asked to carry out. |
| `State` | `SubAgentState` | Where the run is. |
| `StateText` | `string` | Localized state text. |
| `Result` | `string?` | The answer once finished; `null` before. |
| `Error` | `string?` | Why it failed, or `null`. |
| `CallCount` | `int` | Tool calls made by the child and everything it spawned. |
| `MaxToolCalls` | `int?` | The granted call cap, or `null`. |
| `TokensUsed` | `long?` | The child's own spend, not its subtree's. `null` when unmeasured. |
| `InputTokens` / `OutputTokens` | `long?` | The split halves of `TokensUsed`, when reported. |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | Run boundaries. |
| `GrantedToolCount` | `int` | Tools the child was actually given. |
| `GrantedSkillCount` | `int` | Skills given; zero when it has no skill provider. |
| `GrantedMcpServerCount` | `int` | MCP servers given; zero is ordinary. |
| `DroppedRequests` | `IReadOnlyList<string>` | What the spawn asked for and did not get, one line each. |
| `IsRunning` | `bool` | Still running. |
| `IsFinished` | `bool` | Finished, however it finished. |
| `HasError` | `bool` | There is an error worth showing. |
| `HasResult` | `bool` | There is a result worth showing. |
| `HasTokens` | `bool` | The provider reported a token count. `false` means "not measured", not zero. |
| `Duration` | `TimeSpan?` | How long the child ran, or has been running. Measured live; read it, do not cache it. |

## Class: SubAgentStatusViewModel

One child as a bindable row. `Id`, `ParentId` and `Depth` are fixed at spawn time; the granted lists are populated once and never revised, because rewriting what a running child was granted would be a lie about its history.

### Generated properties

| Name | Type | Description |
|---|---|---|
| `Name` | `string` | Display title. |
| `Task` | `string` | The task. |
| `State` | `SubAgentState` | Lifecycle state. |
| `Result` | `string` | The answer. |
| `Error` | `string` | Failure text. |
| `Notes` | `string` | Spawn notes. |
| `CallCount` | `int` | Calls made. |
| `MaxToolCalls` | `int?` | Granted cap. |
| `StartedAt` / `FinishedAt` | `DateTimeOffset?` | Run boundaries. |
| `TokensUsed` / `InputTokens` / `OutputTokens` | `long?` | Spend. |
| `GrantedTools` / `GrantedSkills` / `GrantedMcpServers` | `ObservableCollection<string>` | The granted names. |
| `DroppedRequests` | `ObservableCollection<string>` | Refused requests. |

### Own and computed members

| Member | Type / Signature | Description |
|---|---|---|
| `Id` | `string` | The handle every tool takes. |
| `ParentId` | `string?` | The spawning scope's id, or `null`. |
| `Depth` | `int` | Tree depth. |
| `Transcript` | `AgentTranscript?` | The child's own conversation, once its scope has one. Held, not copied. |
| `StateText` | `string` | Display text for the state. |
| `IsRunning` / `IsFinished` | `bool` | Run boundary predicates. |
| `HasError` / `HasResult` | `bool` | Display predicates. |
| `HasDroppedRequests` | `bool` | Something the spawn asked for was refused. |
| `GrantedSummary` | `string` | The granted capability, one line per entry. |
| `Duration` | `TimeSpan?` | Live elapsed time. |
| `DurationText` | `string` | Elapsed time as text. |
| `HasTokens` | `bool` | Whether a token count was reported. |
| `TokensText` | `string` | Token count as text; empty when none. |
| `NotifyElapsed()` | `void NotifyElapsed()` | Tells a bound panel that `Duration` and `DurationText` moved. The library owns no timer; the host drives the clock. |

## Related

- [Tree](../01_tree/index.md) — the bindable projection over these rows.
- [Dispatch tools](../../01_dispatch-tools/index.md) — the fields that populate them.
