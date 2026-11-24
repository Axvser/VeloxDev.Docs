# Usage

## The five dispatch tools

| Tool | What it does |
|---|---|
| `SpawnSubAgent` | starts a child and returns a handle immediately |
| `WaitSubAgents` | waits for named children, or all; a timeout is information, not a failure |
| `GetSubAgentResult` | reads one child's result, capped by `maxChars` |
| `ListSubAgents` | lists the roster and each child's state |
| `CancelSubAgent` | stops a running child |

A wait that times out reports `timedOut: true` and leaves the children running, so the model can wait again or cancel. `GetSubAgentResult` returns the child's answer only after it completes.

**Expected result:** `SpawnSubAgent` returns a handle while the child is still `Running`; `WaitSubAgents` with a short timeout returns `timedOut: true` and `state: "Running"`.

## What a spawn may ask for

Every narrowing field is optional, and **omitting a field means inherit, not none**. An empty array is a request for none, which is a different thing.

| Field | Effect |
|---|---|
| `task` | the child's user message; required |
| `name` | the roster label (a numbered stand-in when omitted) |
| `allowedTools` | the exact tools the child may use |
| `allowedSkills` | skills the child may read; none also removes its skill tools |
| `allowedMcpServers` | MCP servers the child may reach |
| `maxToolCalls` / `maxReadToolCalls` / `maxWriteToolCalls` | the child's sub-limits |
| `allowNodeExecution` | whether the child may run node business code |
| `allowedGenericCommands` | the allowlisted command names the child may invoke |
| `model` | opaque to this library; handed to the host's factory |
| `notes` | free text contributed to the child's briefing |

**Expected result:** a spawn naming two of seven skills gives the child those two, and its briefing names them; the other five are absent and reported as dropped if the spawn asked for more than the parent had.

## The budget contract

A child's scope is given the parent's ledger as its **outer ledger**, so every call anywhere in the tree is charged at the root. Three consequences follow:

1. The root's `WithMaxToolCalls` is the tree's total cap, not a per-agent cap.
2. Spawning three children does not divide the pot; each child receives a sub-limit, and the pot is enforced at call time.
3. A grant is clamped to at most one less than the parent's remaining allowance, so grants strictly decrease along any root-to-leaf path and every grant is at least one. **Depth therefore terminates even without a depth limit.**

`WithSpawnBudget` is the allowance assumed when the parent set no call cap. `WithSubAgentDepth` is what makes the tree usable: a root allowing 200 calls permits a 199-deep chain, which is bounded but pointless.

**Expected result:** with `WithMaxToolCalls(10)` on the root, ten successful calls across parent and children exhaust the tree; an eleventh is refused with a message naming the limit and `ResetToolCallLimit`.

## Watch the roster

`Children` is an `ObservableCollection<SubAgentStatusViewModel>` bound to the UI thread. From any other thread read `Snapshot`, an immutable `IReadOnlyList<SubAgentSummary>`.

| Property | Meaning |
|---|---|
| `Id`, `ParentId`, `Depth` | place in the tree |
| `State` | `Queued`, `Running`, `Completed`, `Failed`, `Cancelled` |
| `Result`, `Error` | the answer, or what went wrong |
| `CallCount`, `TokensUsed`, `Duration` | what the child spent |
| `GrantedSummary` | the narrowed capability set, when the spawn asked for less |

`SubAgentTreeViewModel` builds a tree from the roster for a panel: a scope root, per-node children, and aggregates `TotalCount`, `RunningCount`, `CompletedCount`, `FailedCount`, `CancelledCount`, `SubtreeTokens`.

**Expected result:** after two spawns, `subAgents.Snapshot.Count` is `2` and a `SubAgentTreeViewModel` reports `RunningCount == 2` while both are in flight.

## Verification

1. Run the complete program without a model. It prints the depth, the spawn budget, the five tool names and an idle roster.
2. Wire a real client and ask: "Spawn two children to list the nodes and the links, then wait for both." Expect two spawn handles, a wait, and two results.
3. Cancel one child before it finishes; its state becomes `Cancelled`, which is not an error.

## Complete code

```csharp
using Microsoft.Extensions.AI;
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClientFactory(
        model => throw new NotSupportedException($"Wire a chat client for '{model ?? "(default)"}'."))
    .WithSubAgentDepth(3)
    .WithSpawnBudget(40);

Console.WriteLine($"max depth:    {subAgents.MaxDepth}");
Console.WriteLine($"spawn budget: {subAgents.SpawnBudget}");
Console.WriteLine($"children:     {subAgents.Snapshot.Count}");

foreach (var name in SubAgentAgentToolkit.ToolNames)
    Console.WriteLine($"tool: {name}");

using var roster = new SubAgentTreeViewModel(subAgents);
Console.WriteLine($"idle: {roster.IsIdle}, total: {roster.TotalCount}");
```

## Run declaration

- ⚠️ Not actually run — statically verified against `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/SubAgentScope.cs`, `SubAgentAgentToolkit.cs`, `SubAgentStatus.cs`, `SubAgentStatusViewModel.cs`, `SubAgentTreeViewModel.cs`, and the dispatch/budget tests under `Src/Test/Unit/Core/VeloxDev.Core.Extension.Test/Agent/SubAgents/`. Spawning a child needs a live model, so no run output is recorded.
