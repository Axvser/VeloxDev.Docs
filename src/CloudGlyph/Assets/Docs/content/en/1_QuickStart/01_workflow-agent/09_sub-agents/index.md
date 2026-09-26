# Workflow Agent — Dispatch Sub-Agents

The sub-agent subsystem (`VeloxDev.AI.SubAgents`, source `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/`) lets the agent dispatch **background child agents**. A child is a fresh `WorkflowAgentScope` over the same tree, carrying a *narrowed slice* of its dispatcher's capabilities. Its tool calls and its reasoning never reach the dispatcher's context — only the child's final report does — and it runs while the dispatcher carries on.

The shape is **dispatch and poll**, not call and wait: `SpawnSubAgent` returns a handle immediately, and `WaitSubAgents` collects. That is forced by where a spawn runs — inside a tool body, on the thread the host's UI owns; a synchronous child would hold that thread for the child's whole conversation.

## 1. Prerequisites

The subsystem ships inside `VeloxDev.Core.Extension` — no extra package beyond the ones the [install page](../01_install/index.md) already adds. You need only what the rest of this Quick Start needs: a running `IWorkflowTreeViewModel` and an `IChatClient`. Since the library never holds a chat client of its own, the model a child runs on is the host's decision, expressed as a factory.

**Expected result:** the following compiles against `VeloxDev.AI.SubAgents` with the same package references already in place.

## 2. Build the subsystem

```csharp
using VeloxDev.AI.SubAgents;

var subAgents = SubAgentScope.ForClient(chatClient)  // children share the host's own model
    .WithSubAgentDepth(3)                            // how deep the tree may go
    .WithSpawnBudget(64)                             // the stand-in cap for an uncapped parent
    .WithSynchronizationContext(SynchronizationContext.Current);
```

- `SubAgentScope.ForClient(IChatClient, string? instructions = null)` is the factory the library supplies: it builds each child as `scope => client.AsAIAgent(scope.CreateContextProviders(), instructions ?? DefaultInstructions).WithPipeline(scope.Pipeline)`. The default preamble is a few hundred bytes — deliberately not the megabyte workflow skeleton, because a background child learns what it can do from its own context provider on every turn.
- `SubAgentScope(Func<WorkflowAgentScope, AIAgent> agentFactory, string? instructions = null)` is the public constructor behind it. Pass a factory when children should run on a different model than the dispatcher.
- `WithSubAgentDepth(int depth)` bounds how deep the tree may go: a child of the scope this is attached to is depth 1, a grandchild depth 2. A scope at or past the limit keeps no ability to spawn, and says so instead of failing silently.
- `WithSpawnBudget(int budget)` sets the allowance *assumed* for a spawn when the host never called `WithMaxToolCalls`. Its default is 64. Without it, "the parent's remaining allowance" would be undefined for an uncapped parent and the descending grant that guarantees termination would not exist — set it explicitly rather than relying on the default.
- `WithSynchronizationContext(SynchronizationContext)` binds the roster to the host's UI thread; `WithSubAgents` sets it from the workflow scope anyway, so call it only when the subsystem is configured before the scope is.

**Expected result:** `subAgents.SpawnBudget == 64`, `subAgents.MaxDepth == 3`, `subAgents.Children` is empty.

## 3. Attach it to the host scope

```csharp
scope.WithSubAgents(subAgents);
```

Attach last: skills (`WithSkills`) and MCP servers (`WithMcps`) must be configured **before** this call, because the narrowing reads them off the parent at spawn time. `WithSubAgents` hands the subsystem this scope rather than the other way round — it needs the parent's real capabilities to narrow against and the parent's ledger to charge to, and neither exists until the scope does.

The five management tools then join the agent's surface on every turn, wrapped like the built-in tools so each spawn is counted, gated and reported exactly like any other call:

| Tool | Required argument | What it does |
|---|---|---|
| `SpawnSubAgent` | `task` | Dispatches a child; returns its `id` at once |
| `WaitSubAgents` | — | Waits for named ids (or every running child) up to `timeoutMs` (default 60000) |
| `GetSubAgentResult` | `id` | One child's state, and its **untruncated** report once finished |
| `ListSubAgents` | — | The roster this scope issued, with state, depth and call counts |
| `CancelSubAgent` | `id` | Stops a running child; it reports as `Cancelled`, not as a failure |

**Expected result:** `scope.SubAgents` is the instance you passed, and all five names reach the model. They are contributed by `SubAgentAgentContextProvider`, **not** by `WorkflowAgentToolkit`, so they do not appear in `scope.ProvideTools()` — a scope nobody attached the subsystem to contributes none of them.

## 4. Narrow what a child may have

Every capability argument is optional, and **omitting one means inherit, not none**:

| Argument | Omitted | Empty |
|---|---|---|
| `allowedTools` | every tool the parent currently offers | no tools at all |
| `allowedSkills` | every skill the parent has switched on | none, **and its skill tools go with them** |
| `allowedMcpServers` | every connected, switched-on server | none |
| `maxToolCalls` | up to as much of the parent's remaining allowance as can be granted | — |
| `maxReadToolCalls` / `maxWriteToolCalls` | inherited from the parent | — |
| `allowNodeExecution` | `false` | — |
| `allowedGenericCommands` | none | — |
| `autoMarkDirty` | follows the parent | — |
| `name` | a numbered stand-in (`子代理 N`) | — |
| `notes` | nothing | — |

Naming is the **only** way to take anything away, and it is where the subsystem's central invariant lives: a child's abilities are its parent's own, or fewer, never more. Whatever a spawn asked for and did not get is refused **and reported** in the reply's `dropped` array — read it, because nothing else tells you.

```jsonc
// SpawnSubAgent("count the nodes", allowedTools: ["ListNodes", "DeleteNode"])
{
  "status": "ok",
  "id": "9f2c…",
  "name": "子代理 1",
  "depth": 1,
  "maxToolCalls": 199,
  "grantedToolCount": 1,
  "grantedSkillCount": 0,
  "grantedMcpServerCount": 0,
  "dropped": ["DeleteNode: not available to this agent, or switched off by the host"],
  "message": "Dispatched, but not with everything you asked for — read \"dropped\". Call WaitSubAgents to collect its report."
}
```

A child that was granted **zero** skills also loses the skill tools (`ListSkills`, `load_skill`, `UnloadSkill`, `read_skill_resource`) — a `load_skill` with nothing behind it is a tool that can only fail. Custom tools travel in the groups they were registered in, so the child is told how to use the tools it holds and not the ones it does not.

**Expected result:** naming a tool the host switched off, or one that does not exist, puts a line in `dropped`; the child's own surface contains exactly the names the reply listed.

## 5. The allowance is one pot for the whole tree

A child's budget is a **share of its parent's**, not a second pot beside it: the child's scope is given the parent's ledger as its outer ledger, so every call anywhere in the tree is counted at the root, and the root's cap is the tree's cap. What a grant sets is a *sub-limit on the child's own subtree*, never a reservation — spawning three children does not divide the pot, it bounds each of them.

```text
effective cap  = MaxToolCalls ?? SpawnBudget            // always finite
grant          = min(requested ?? remaining, remaining - 1)
remaining      = min(effective cap - this level spent, root cap - root spent)
grant < 1  ⇒ the spawn is refused (a row is not created)
```

The `- 1` is what makes an **unbounded depth terminate**: along any root-to-leaf path the grants strictly decrease and each is at least one, so the tree cannot be deeper than the root's allowance. That buys termination, not practicality — a root allowing 200 calls permits a 199-deep chain — which is why `WithSubAgentDepth` exists and why a host should set both: the budget is the guarantee, the depth limit is what makes the tree useful.

Anchored arithmetic from the tests (`SubAgentBudgetTests`, `SubAgentNarrowingTests`, `SubAgentHierarchyTests`): a parent capped at 10 grants 9 to a child that asks for 20, and reports the clamp; a parent capped at 40 grants 39 / 38 / 37 down a chain; each sibling gets the *remainder*, not a share of it.

**Expected result:** a spawn whose requested `maxToolCalls` exceeds what the parent has left comes back with the granted number in `maxToolCalls` **and** a `dropped` line naming the clamp.

## 6. Collect, cancel, dispose

```csharp
// the model's side — these are the tools it calls, in the order the standing text asks for
// SpawnSubAgent(task: "…")             → {"status":"ok","id":"9f2c…", …}
// WaitSubAgents(ids: ["9f2c…"], timeoutMs: 60000)
//   → {"status":"ok","timedOut":false,"agents":[{"id":"9f2c…","state":"Completed","result":"…"}]}
// ListSubAgents()                      → {"status":"ok","count":1,"running":0,"agents":[…]}
// CancelSubAgent(id: "9f2c…")          → {"state":"Cancelled", …}
```

- A wait that times out is information, not a failure: it returns `"timedOut": true` with the children still marked `Running`, so the model can decide between waiting again and cancelling. Prefer one long wait over polling — each `WaitSubAgents` call costs the model a tool call, while the children cost it none while they run.
- `WaitSubAgents` results are truncated at 4000 characters per report; `GetSubAgentResult` returns the whole thing, untruncated. The truncation marker is inside the text as well as in a `truncated` flag, so a model reading the value alone can tell a complete report from a cut one.
- Cancelling a child that already finished changes nothing. Cancellation is its own state — a child stopped by the host, by its parent or by disposal did not go wrong, and a panel that painted it red would teach the user to distrust the control.
- `await subAgents.DisposeAsync()` cancels every running child and **waits** for them to settle. The wait is what makes disposal a boundary rather than a race: a child's tool calls are marshalled onto the host's UI thread, so a host that tore its dispatcher down while children were in flight would have them post into a pump that no longer exists. After disposal no further spawn is accepted.

**Expected result:** waiting with nothing running returns `{"count":0,"timedOut":false}` at once rather than serving out its timeout; `CancelSubAgent` on a completed child returns `"state":"Completed"` unchanged.

## 7. Watch it — the tree panel

A roster is **flat and per scope**: it holds only the children that scope issued, which is exactly what keeps one branch from reading another's work. `SubAgentTreeViewModel` projects those rosters into one bindable tree:

```csharp
using VeloxDev.AI.SubAgents;

var tree = new SubAgentTreeViewModel(subAgents);  // bind Tree (one node: the scope itself)
// later, from your own clock:
tree.TickElapsed();                               // the library owns no timer
```

- Read the tree's `Roots` (the scope's own children), its counts (`TotalCount`, `RunningCount`, `CompletedCount`, `FailedCount`, `CancelledCount`), and its `SubtreeTokens`.
- Read `Snapshot` — not `Children` — from anywhere off the roster's thread. An agent invocation renders its prompt on a thread of the framework's choosing, and enumerating the bound `ObservableCollection` there races the host's UI.
- `Dispose()` detaches from the scopes and **does not cancel anything**. Closing a panel is not a decision about the work the panel was showing.
- The tree node's `Title` is the spawn's `name` — a task title for the person watching, not an identifier. Omitted, it falls back to `子代理 N`, numbered per parent.

**Expected result:** after one spawn, `tree.Roots` has one node whose `Row.StateText` reads `已完成` once its run settles; a grandchild dispatched by that child hangs off its node rather than beside it.

## 8. Complete code

One runnable block: a scope over a tree, a sub-agent subsystem sharing the host's model, and one turn in which the model is asked to delegate. `tree` and `chatClient` are the same two objects the earlier pages describe.

```csharp
using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using VeloxDev.AI.SubAgents;
using VeloxDev.AI.Workflow;
using VeloxDev.WorkflowSystem;

public static class SubAgentQuickStart
{
    public static async Task RunAsync(IWorkflowTreeViewModel tree, IChatClient chatClient)
    {
        var scope = tree.AsAgentScope()
            .WithMaxToolCalls(60)
            .WithAllowNodeExecution(true)
            .WithSynchronizationContext(SynchronizationContext.Current);

        // Attached after the capabilities the narrowing reads off the parent at spawn time.
        var subAgents = SubAgentScope.ForClient(chatClient)
            .WithSubAgentDepth(2)
            .WithSpawnBudget(64);
        scope.WithSubAgents(subAgents);

        using var panel = new SubAgentTreeViewModel(subAgents);

        var host = chatClient.AsAIAgent(new ChatClientAgentOptions
        {
            ChatOptions = new ChatOptions
            {
                Instructions = "You are an assistant working on a workflow graph. Use the tools you are given.",
            },
            AIContextProviders = scope.CreateContextProviders(),
        });

        await using (subAgents)
        {
            await host.RunAsync(
                "Work out how many nodes the graph has by dispatching a background sub-agent to count "
                + "them — do not count them yourself. Then wait for it and tell me the number.");

            // The roster is flat and per scope: this scope holds only the children it issued.
            foreach (var row in subAgents.Snapshot)
            {
                Console.WriteLine($"{row.Name} [depth {row.Depth}] {row.StateText} " +
                                  $"{row.CallCount} call(s), {row.GrantedToolCount} tool(s), " +
                                  $"tokens {(row.HasTokens ? row.TokensUsed!.Value.ToString() : "unmeasured")}");
                if (row.DroppedRequests.Count > 0)
                    Console.WriteLine("  dropped: " + string.Join(" | ", row.DroppedRequests));
                Console.WriteLine("  " + (row.Result ?? row.Error ?? "(no report yet)"));
            }

            Console.WriteLine($"tree total: {panel.TotalCount} sub-agent(s), {panel.SubtreeTokensText} tokens");
        }
    }
}
```

## 9. Run declaration

- ⚠️ Not actually run — statically verified only. Every signature on this page was checked against `Src/Core/VeloxDev.Core.Extension/Agent/SubAgents/*.cs` and `Agent/Workflow/WorkflowAgentScope.cs`; the tool replies and the arithmetic are copied from real assertions in `VeloxDev.Core.Extension.Test/Agent/SubAgents/` (`SubAgentDispatchTests`, `SubAgentNarrowingTests`, `SubAgentBudgetTests`, `SubAgentHierarchyTests`, `SubAgentToolSchemaTests`). The assembled program was not compiled or executed in this documentation pass, and no `API_KEY_DEEPSEEK` was available to exercise the live tests.

- The subsystem's own structure follows the parent feature's Quick Start: [build the scope](../02_build-the-scope/index.md) → [tool budgets & host policy](../03_tool-budgets-and-host-policy/index.md) → this page.
