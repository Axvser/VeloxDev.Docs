# 03 · Tool Budgets & Host-Policy Gates

The scope decides how much the agent may spend and which dangerous tools exist at all. These are **host-policy** decisions enforced in code, not in prompt prose: a gated tool is either filtered out of the tool list or returns a structured JSON refusal before its body runs.

## 1. Tool-call budgets

```csharp
scope.WithMaxToolCalls(200)          // total cap on all tool calls
    .WithMaxReadToolCalls(100)       // cap on read-only/query calls (ListNodes, GetFullTopology, ...)
    .WithMaxWriteToolCalls(50);      // cap on everything else (mutations, execution, commands)
```

- A call counts as **read** when its name is in the toolkit's read-only set — the Query tools plus `TakeSnapshot` / `GetChangesSinceSnapshot`, `GetNodeStatistics`, the five Graph tools, `RequestSelection` / `RequestConfirmation`, `ResetToolCallLimit`, the four compile/plan read tools (`CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus`, `GetExecutionLog`), **plus every skill and sub-agent tool name** (folded in from `SkillAgentToolkit.ToolNames` and `SubAgentAgentToolkit.ToolNames`). Everything else counts as **write**.
- A pre-flight gate (`CheckBudget`) runs inside the marshalled block, before the body. When a limit is already reached it returns a refusal; the body never runs and the call is **not** counted.

Refusal wording (from `LimitRefusal`):

```text
Tool call limit (200) reached. No further tool calls are accepted until the budget is extended.
If the task is unfinished, call ResetToolCallLimit — it asks the user, and only their agreement
reopens the budget. Do not retry this call, and do not tell the user you can continue without it.
```

The three `cause` prefixes are `Tool call limit (N) reached.`, `Mutation tool call limit (N) reached.` and `Query tool call limit (N) reached.`; a spawned child can additionally hit `The session's tool-call budget (N) is spent.` (the root scope's ceiling, asked first).

**Expected result:** after a cap is reached the affected tool returns `status:"error"` carrying that message instead of executing.

## 2. `ResetToolCallLimit` — the way out of a spent budget

Every toolkit registers one extra tool, `ResetToolCallLimit` (constant `WorkflowAgentToolkit.ResetBudgetToolName`), **whatever category flags were asked for**. It is the only way to continue after a refusal.

- It never spends the budget (counting it would re-spend the just-zeroed counter — the reset would undo itself).
- It survives the gate it exists to open: the pre-flight gate returns `null` for it even when the budget is spent.
- It puts the question to the user through the scope's confirmation handler under the operation key `extend-tool-call-budget`. Asking is the whole safety property — the agent can only ask, never widen its own budget. With **no** handler registered the answer is **deny** (an unanswerable prompt must deny).
- At interaction safety level 0 the host asked never to be interrupted, so the tool returns `denied` rather than asking.
- On agreement it calls `ResetChain()`, zeroing this level **and every level above it** — a session whose root allowance stayed spent would refuse the very next call.

**Expected result:** calling `ResetToolCallLimit` with a limit reached and a handler that answers "allow" returns `Tool-call budget reset by the user. You may continue.`; without a handler it returns `status:"denied"`.

## 3. Capability gates

```csharp
scope.WithAllowNodeExecution(true)                 // enable the code-running tools
    .WithAllowedGenericCommands("ReceiveCommand"); // allowlist for ExecuteCommandOnNode/ExecuteCommandById
```

- `WithAllowNodeExecution(enabled)` gates the tools that run arbitrary node business code: `ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`, `RunCompiledWorkflow`, `GetNodeResult`, and the four background run tools (`StartCompiledWorkflow`, `ContinueCompiledWorkflow`, `GetCompiledRunStatus` does not run code but is grouped with them for the compile path, and `StopCompiledRun`). Off by default. A blocked run tool returns `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).` The compile-only plan tools (`CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus`) never run node code and are **not** gated.
- `WithAllowedGenericCommands(params string[])` allowlists command names for `ExecuteCommandOnNode` / `ExecuteCommandById`; the `"Command"` suffix is optional. Never called ⇒ generic command execution is disabled entirely (secure default). This gate is checked per call by `CommandInvoker`.

## 4. Per-tool switches

```csharp
scope.WithToolEnabled("ClearHistory", false);   // fluent: off from the next invocation
bool moved = scope.SetToolEnabled("Undo", true);// runtime: returns whether the switch moved
bool on = scope.IsToolEnabled("Undo");          // read the current state
```

- `CreateTools(categories)` filters the final list by `IsToolEnabled`; `CreateAllTools()` returns the **unfiltered** surface (that is what a host UI enumerates to show switchable tools).
- A switched-off tool is also **refused** by the pre-flight gate, not merely filtered: the gate's hook is shared with every slice the scope composes (the MCP and skill providers are given this same policy), so one switch reaches an MCP- or skill-sourced tool too. The refusal is `'{toolName}' is disabled by host policy. Do not try to work around it — use another tool or report it to the user.`
- The switch may be flipped **mid-session**: the tool set is re-rendered per turn (see the Run a Conversation page), so no agent rebuild is needed and no cached render goes stale.
- `DisabledToolNames` (read-only) lists what is off; the `Changed` event fires whenever the scope version moves.

**Expected result:** after `SetToolEnabled("Undo", false)` the next invocation offers no `Undo` tool, and a direct call to it is refused with the host-policy message.

## 5. Tool approval — a code gate

`WithToolApproval(true)` requires a human to approve **every non-query tool call before it runs**, by putting the tool name to the confirmation handler.

- Query tools are never asked (a read has nothing to approve). MCP-sourced tools are third-party code and **are** treated as mutations, so they are gated too.
- The key handed to the confirmation handler is the **tool name**, so "allow for the session" approves that tool for the rest of the session.
- A denial is reported as `AgentToolOutcome.Refused` and never reaches the body. On refusal the model is told: `'{toolName}' was not approved by the user. The call did not run. Do not retry it, and do not look for another tool that makes the same change — ask the user what they want instead.`
- This complements `WithInteractionSafety` rather than replacing it: that one shapes what the model is *told* to ask about; this one decides what it may actually do, and cannot be skipped by a model that declines to call `RequestConfirmation`.

## 6. Interaction safety & the two handlers

Interaction safety is one integer 0–3 (default **1**), set with `WithInteractionSafety(level)`:

| Level | Name | Behaviour |
|---|---|---|
| 0 | Silent | Fully autonomous. Both interaction tools are skipped and no policy is emitted. |
| 1 | Cautious (default) | Ask only when intent is genuinely ambiguous or the action is bulk/destructive. |
| 2 | Balanced | Ask when multiple paths are plausible OR the action touches ≥ 2 nodes/links. |
| 3 | Strict | Ask before every mutation that is not a pure single-node creation. |

```csharp
scope.WithInteractionSafety(3);
scope.WithInteractionSafetyPrompt(2, "Ask before any structural change that touches more than one node.");

scope.WithSelectionHandler(async args =>        // backs RequestSelection
{
    args.SelectedOption = args.Options.FirstOrDefault();
    await Task.CompletedTask;
});
scope.WithConfirmationHandler(async args =>      // backs RequestConfirmation
{
    args.Result = AgentConfirmationResult.AllowOnce;   // or AllowAlways | Deny
    await Task.CompletedTask;
});
```

- `RequestSelection` is registered only when level > 0 **and** `WithSelectionHandler` was called; inside the handler set `args.SelectedOption` (single) or `args.SelectedOptions` / `args.FreeTextResponse`. The nested `WorkflowAgentScope.SelectionResult` offers `Single` / `Multi` / `FreeText` factories for low-level use.
- `RequestConfirmation` is registered only when level > 0 **and** `WithConfirmationHandler` was called; set `args.Result = AllowOnce | AllowAlways | Deny`. `AllowAlways` is remembered per `operationKey` for the session (`ResolveConfirmationAsync`).
- `WithInteractionSafetyPrompt(level, body)` replaces a level's policy body (1–3); level 0's silent rule cannot be overridden.

**Expected result:** at level 0 there are no `RequestSelection` / `RequestConfirmation` tools; at level 3, with both handlers registered, each appears exactly once.

## 7. UI thread, callbacks & dirty tracking

```csharp
scope.WithSynchronizationContext(SynchronizationContext.Current)  // marshal every tool call to the UI thread
    .WithAutoMarkDirty(false)                                     // default: the agent calls MarkDirty itself
    .WithToolCallCallback(args =>                                 // after every completed call
    {
        Console.WriteLine($"tool {args.ToolName} (count {args.CallCount})");
        return Task.CompletedTask;
    });
```

- `WithSynchronizationContext(context)` marshals every tool call onto that context — required when components are UI-bound (the demo passes `SynchronizationContext.Current`).
- `WithAutoMarkDirty(enabled)` — `true` marks the tree dirty after every **succeeded, non-query** call (`AccountingStage` → `AccountAsync`); default `false` leaves the injected `CommandReference.md` prompt to tell the agent to call `MarkDirty` once at the end.
- `WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` is invoked after every completed call; `ToolCalled` (the `IAgentToolCallNotifier` event) also fires.

**Expected result:** every tool call runs on the registered context; with auto-mark off the tree's dirty flag changes only when the agent calls `MarkDirty`.

## Run declaration

- ✅ Actually built and ran — the deterministic agent test suite was executed on 2026-10-01:

```text
dotnet test Src/Core/VeloxDev.Core.Extension.Test/VeloxDev.Core.Extension.Test.csproj --filter "FullyQualifiedName~Agent&FullyQualifiedName!~SubAgentLiveTests"
已通过! - 失败: 0，通过: 387，已跳过: 0，总计: 387，持续时间: 920 ms
```

That run covers `ToolSwitchTests`, `ToolApprovalTests`, `CompiledRunControlTests` and the rest of `Agent/**` except `SubAgentLiveTests` (which needs a real model key and is non-deterministic — excluded on purpose). It does not run a conversation against a model.
