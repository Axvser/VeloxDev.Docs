# Workflow Agent — Tool Budgets & Host-Policy Gates

The scope decides how much the agent may spend per turn and which dangerous tools exist at all. These are **host-policy** decisions: when a tool is gated off it is either absent from `ProvideTools()` or returns a `status:"error"` JSON object saying it is disabled — enforcement lives in code, not in the prompt.

## 1. Interaction safety & human-in-the-loop handlers

Interaction safety is a single integer 0–3 (default **1**) set with `WithInteractionSafety(level)`:

| Level | Name | Behaviour |
|---|---|---|
| 0 | Silent | Fully autonomous. Both interaction tools are skipped entirely and no safety policy is emitted. |
| 1 | Cautious (default) | Asks only when intent is genuinely ambiguous or the action is bulk/destructive. |
| 2 | Balanced | Asks when there are multiple plausible paths OR the action touches ≥ 2 nodes/links. |
| 3 | Strict | Asks before every mutation that is not pure single-node creation; gates all destructive actions. |

Levels 1–3 only register the tools when a handler exists, and the whole policy body per level (1–3) can be replaced with `WithInteractionSafetyPrompt(level, body)` — level 0's silent rule cannot be overridden.

```csharp
scope.WithInteractionSafety(3);
scope.WithInteractionSafetyPrompt(2, "Ask before any structural change that touches more than one node.");

scope.WithSelectionHandler(async args =>           // backs the RequestSelection tool
{
    args.SelectedOption = args.Options.FirstOrDefault();   // single-choice result
    // multi/free-text: args.SelectedOptions = [...]; args.FreeTextResponse = "...";
    await Task.CompletedTask;
});
scope.WithConfirmationHandler(async args =>         // backs the RequestConfirmation tool
{
    args.Result = AgentConfirmationResult.AllowOnce;      // or AllowAlways | Deny
    await Task.CompletedTask;
});
```

- `RequestSelection` is registered only when `WithInteractionSafety(level)` with level > 0 **and** `WithSelectionHandler(...)` was called; inside the handler set `args.SelectedOption` (single) or `args.SelectedOptions` / `args.FreeTextResponse` (multi/free text). The scope also offers a small `SelectionResult` helper with `Single(...)` / `Multi(...)` / `FreeText(...)` factories.
- `RequestConfirmation` is registered only when level > 0 and `WithConfirmationHandler(...)` was called; inside set `args.Result = AgentConfirmationResult.AllowOnce | AllowAlways | Deny`. `AllowAlways` persists the approval for the rest of the session.

**Expected result:** with level 0 there are no `RequestSelection` / `RequestConfirmation` tools; at level 3 each tool appears exactly once (one per registered handler).

## 2. Tool-call budgets

Three budget knobs cap the number of tool invocations the model can make per turn:

```csharp
scope.WithMaxToolCalls(200)            // total cap on all tool calls
    .WithMaxReadToolCalls(100)         // cap on read-only/query calls (ListNodes, GetFullTopology, ...)
    .WithMaxWriteToolCalls(50);        // cap on everything else (mutations, execution, commands)
```

- A call is counted as **read** when its name is in the toolkit's read-only set — the `Query` tools plus read-only graph/analytics/state/interaction tools (`GetChangesSinceSnapshot`, `TakeSnapshot`, `GetNodeStatistics`, `SearchForward`/`SearchReverse`/`SearchAllRelative`, `IsConnected`, `FindPath`, `RequestSelection`, `RequestConfirmation`). Everything else counts as **write** (all Mutation tools, `MarkDirty`, all six Execution tools, both Command tools).
- Exceeding a budget returns an error JSON such as `Tool call limit (200) exceeded...` / `Mutation tool call limit (50) exceeded...` / `Query tool call limit (100) exceeded...` before the tool runs.
- Budgets are unset (`null`) until you call the corresponding `With*`, so token-heavy read queries do not silently eat the mutation budget once you set the separate caps.

**Expected result:** after the caps are exceeded the affected tool returns a `status:"error"` JSON with the limit message instead of executing.

## 3. Node execution, generic commands, UI thread & dirty tracking

```csharp
scope.WithAllowNodeExecution(true)                        // enable ExecuteNode/ExecuteNodes/BroadcastNode/
                                                          // ReverseBroadcastNode/RunCompiledWorkflow/GetNodeResult
    .WithAllowedGenericCommands("ReceiveCommand")          // allowlist for ExecuteCommandOnNode/ExecuteCommandById
    .WithSynchronizationContext(SynchronizationContext.Current) // marshal every tool call onto the UI thread
    .WithAutoMarkDirty(false)                              // default: agent must call MarkDirty itself
    .WithToolCallCallback(args =>                          // after every tool call
    {
        Console.WriteLine($"tool {args.ToolName} called (count {args.CallCount})");
        return Task.CompletedTask;
    });
```

- `WithAllowNodeExecution(enabled)` gates the six tools that run arbitrary node business code (`ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`, `RunCompiledWorkflow`, `GetNodeResult`). Off by default. The compile-only tools (`CompileWorkflow`, `CompileNodeResult`) never run node code and are **not** gated. A blocked run tool returns `... is disabled by host policy. The host must enable node execution via WithAllowNodeExecution(true).`
- `WithAllowedGenericCommands(params string[])` allowlists command names for the generic command tools (`ExecuteCommandOnNode` / `ExecuteCommandById`). Names are normalized to a `"Command"` suffix. Never called ⇒ generic command execution is disabled entirely (secure default). An unlisted command returns an error asking the host to allowlist it.
- `WithSynchronizationContext(context)` registers the UI context so every tool call is marshalled onto it — required when workflow components are UI-bound (the demo calls it with `SynchronizationContext.Current` from the UI thread).
- `WithAutoMarkDirty(enabled)` — when `false` (default) the framework does not auto-mark and the injected `CommandReference.md` prompt tells the agent to call `MarkDirty` once at the end of a mutation task; when `true`, every non-query mutation tool call marks the tree dirty automatically. Query tools never auto-mark.
- `WithToolCallCallback(Func<AgentToolCallEventArgs, Task>)` is invoked after every tool call with the tool name, result and cumulative count — handy to trigger a UI virtualization refresh (the demo raises a `ToolCalled` event from it).

**Expected result:** with `WithAllowNodeExecution` unset, `ExecuteNode` returns a `status:"error"` JSON citing the host policy; with it set and an allowlisted command, the corresponding tools appear in `ProvideTools()` and run.

## Run declaration

- ⚠️ Statically verified only. Behaviour, defaults and the error-message wording are taken from `WorkflowAgentScope.cs` and `WorkflowAgentToolkit.cs` (gating lines and `TrackedAIFunction`); nothing here was compiled or executed.
