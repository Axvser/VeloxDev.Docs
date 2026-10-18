# 03 · Tool Budgets & Host-Policy Gates

The scope decides how much the agent may spend and which dangerous tools exist at all. These are **host-policy** decisions enforced in code, not in prompt prose: a gated tool is either filtered out of the tool list or returns a structured JSON refusal before its body runs.

## 1. Tool-call budgets

```csharp
scope.WithMaxToolCalls(200)          // total cap on all tool calls
    .WithMaxReadToolCalls(100)       // cap on read-only/query calls (ListNodes, GetFullTopology, ...)
    .WithMaxWriteToolCalls(50);      // cap on everything else (mutations, execution, commands)
```

- A call counts as **read** when its name is in the toolkit's read-only set — the Query tools plus `TakeSnapshot` / `GetChangesSinceSnapshot`, `GetNodeStatistics`, the five Graph tools, `RequestSelection` / `RequestConfirmation`, `ResetToolCallLimit`, the four compile/plan read tools (`CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus`, `GetExecutionLog`), **plus every skill and sub-agent tool name** (folded in from `SkillAgentToolkit.ToolNames` and `SubAgentAgentToolkit.ToolNames`). `EnterPlanMode` / `ExitPlanMode` are not in that name list, so they count as **write** calls even though they do not touch the graph.
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
- It puts the question to the user through the scope's confirmation handler under the operation key `extend-tool-call-budget`. Asking is the whole safety property — the agent can only ask, never widen its own budget. With **no** handler registered the answer is **deny** (an unanswerable prompt must deny). `AgentActionCategory.Interact` is never put to the mode's policy, so no mode can silence the question.
- On agreement it calls `ResetChain()`, zeroing this level **and every level above it** — a session whose root allowance stayed spent would refuse the very next call.

**Expected result:** calling `ResetToolCallLimit` with a limit reached and a handler that answers "allow" returns `Tool-call budget reset by the user. You may continue.`; without a handler it returns `status:"denied"`.

## 3. Capability gates

```csharp
scope.WithAllowNodeExecution(true)                 // enable the code-running tools
    .WithAllowedGenericCommands("ReceiveCommand"); // allowlist for ExecuteCommandOnNode/ExecuteCommandById
```

- `WithAllowNodeExecution(enabled)` gates the tools that run arbitrary node business code: `ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`, `RunCompiledWorkflow`, `GetNodeResult`, `StartCompiledWorkflow` and `ContinueCompiledWorkflow`. Off by default. A blocked run tool returns `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).` The compile-only plan tools (`CompileWorkflow`, `CompileNodeResult`, `GetCompileStatus`) never run node code and are **not** gated; neither are the handle operations `GetCompiledRunStatus` / `PauseCompiledRun` / `ResumeCompiledRun` / `StopCompiledRun`.
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

## 5. Permission modes — the code gate

The session's permission policy replaces the old interaction-safety dial and the separate tool-approval switch. It is one `AgentPermissionMode` plus optional rules, evaluated **per call** before the tool body runs. `PermissionDecision` is `Allow` | `Ask` | `Deny`; a mode is a *named state* the user can switch, and every refusal names the mode and what to switch to.

| Mode | Value | What it permits |
|---|---|---|
| `Plan` | 0 | Read and interact only; edits, execution and reach changes are refused. |
| `Manual` | 1 | Every non-read action is put to the user. |
| `AutoEdit` | 2 | Reads and graph edits run; execution and reach changes ask. |
| `Auto` | 3 | Reads, edits and execution run; only reach changes (`Curate`) ask. **Default.** |
| `Bypass` | 4 | Nothing is asked; explicit `Deny` rules still hold. |

```csharp
scope.WithPermissionMode(AgentPermissionMode.AutoEdit)
     .WithPermissionRule(PermissionDecision.Ask, "DeleteNode", "DeleteSlot")
     .WithPermissionRule(PermissionDecision.Deny, "category:Curate");
bool moved = scope.SetPermissionMode(AgentPermissionMode.Manual);  // runtime switch
```

- **Rules are the fine layer.** Patterns select by tool name (`DeleteNode`, `Get*`), by category (`category:Edit`), or by source (`source:mcp:*`, `source:skill`). A `Deny` rule holds in every mode, including `Bypass`.
- **The gate is in code.** `ToolPipeline.Confirm` calls `PermissionPolicy.Evaluate(invocation)`; an `Ask` goes to the confirmation handler under the tool name (so "allow for the session" approves that tool), and a `Deny` returns `DescribePermissionRefusal`. A model cannot skip it by declining to call `RequestConfirmation`.
- **MCP management tools are `Curate`** (they change what the session can reach), so `Auto` still asks for `AddMcpServer`, `SetMcpServerArguments`, `LoadMcpServers` and `UnloadMcpServer`. Tools *exported by* a connected server are third-party code classified `Execute`; `Auto` lets them run, `AutoEdit`/`Manual` ask, and a host rule such as `Ask("source:mcp:*")` can gate them. `WithPermissionJudge` supplies the decision in `Auto` for calls no rule settles; a judge that throws denies.
- **The Agent has two transitions of its own**, both asking first: `EnterPlanMode` and `ExitPlanMode` (registered only with a confirmation handler). There is deliberately no tool that widens the mode.

**Expected result:** at `Plan`, `CreateNode` returns a refusal naming `Plan`; at `AutoEdit`, it runs without asking, while `ExecuteNode` asks. A `Deny` rule on `DeleteNode` refuses it in every mode.

## 6. Interaction handlers

Two optional tools ask the user directly; registration depends only on the handler, never on a safety level:

```csharp
scope.WithSelectionHandler(async args =>        // backs RequestSelection
{
    args.SelectedOption = args.Options.FirstOrDefault();
    await Task.CompletedTask;
});
scope.WithConfirmationHandler(async args =>      // backs RequestConfirmation / Ask decisions / ResetToolCallLimit
{
    args.Result = AgentConfirmationResult.AllowOnce;   // or AllowAlways | Deny
    await Task.CompletedTask;
});
```

- `RequestSelection` is registered when `WithSelectionHandler` was called; inside the handler set `args.SelectedOption` (single) or `args.SelectedOptions` / `args.FreeTextResponse`. The nested `WorkflowAgentScope.SelectionResult` offers `Single` / `Multi` / `FreeText` factories for low-level use.
- `RequestConfirmation` is registered when `WithConfirmationHandler` was called; set `args.Result = AllowOnce | AllowAlways | Deny`. `AllowAlways` is remembered per `operationKey` for the session (`ResolveConfirmationAsync`).
- With no confirmation handler every `Ask` decision answers as a denial, and `ResetToolCallLimit` also denies.

**Expected result:** with both handlers registered, `RequestSelection` and `RequestConfirmation` each appear exactly once in `ProvideTools()`; with neither, both are absent and the tool count drops by those two plus `EnterPlanMode` / `ExitPlanMode`.

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

- ⚠️ **Not run for this revision** — statically verified against the current source on 2026-10-18. A previously recorded deterministic suite run (2026-10-01, `失败: 0，通过: 387`) exists, but it predates the permission-mode / context-tree redesign, so it is not evidence that the gates described on this page behave as documented today.
