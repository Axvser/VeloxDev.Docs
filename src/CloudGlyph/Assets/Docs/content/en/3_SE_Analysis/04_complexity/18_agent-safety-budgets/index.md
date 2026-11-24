# Agent Safety and Budgets

A tool call is admitted by two gates and then charged to a ledger shared with its ancestors. Every gate walks a rule array, so the cost of safety is proportional to the number of host rules, not to the graph; the cost of budgets is proportional to spawn depth, not to spend.

## Cost model

| Symbol | Meaning |
|---|---|
| $r$ | rules on the active permission policy |
| $d$ | spawn-chain depth of the calling agent |
| $|v|, |p|$ | length of the matched value and the glob pattern |
| $t$ | tool calls already spent on the chain |
| $c$ | characters in a tool result |

## Decision evaluation

`AgentPermissionPolicy` is immutable: `WithMode`, `WithRule`, `WithJudge` and `WithoutRules` each allocate a new instance (`Src/Core/VeloxDev.Core.Extension/Agent/Safety/AgentPermissionPolicy.cs:73-95`). A mode or judge swap is $O(1)$ by reference; adding rules one at a time reallocates the array, so building $r$ rules incrementally is

$$
T_{\text{setup}} = O(r^2)
$$

`Evaluate` runs a fixed order: deny scan, Plan-mode refusal, ask scan, allow scan, Auto judge, mode default (`AgentPermissionPolicy.cs:100-124`).

```csharp
if (Has(PermissionDecision.Deny, invocation)) return PermissionDecision.Deny;
if (Mode == AgentPermissionMode.Plan && ModeDefault(Mode, invocation.Category) == PermissionDecision.Deny)
    return PermissionDecision.Deny;
if (Has(PermissionDecision.Ask, invocation)) return PermissionDecision.Ask;
if (Has(PermissionDecision.Allow, invocation)) return PermissionDecision.Allow;

if (Mode == AgentPermissionMode.Auto && Judge is { } judge)
{
    try
    {
        return judge(invocation);
    }
    catch (Exception)
    {
        // A judge that cannot answer must not answer "yes". Nothing here is worth failing open for.
        return PermissionDecision.Deny;
    }
}
```

When no rule settles the call, `Has` is invoked three times and each call is a full LINQ scan of the same array. The rule's own cost is a two-pointer glob match with one backtrack point, not a regex (`Src/Core/VeloxDev.Core.Extension/Agent/Safety/AgentPermissionRule.cs:70-103`), so a call is

$$
T_{\text{eval}} = O(r \cdot |v| \cdot |p|)
$$

in the worst case, and $O(3r)$ `Matches` attempts per unsettled call.

## The gates run twice

`TrackedAIFunction` asks the pipeline to refuse, then to confirm, and both paths evaluate the policy (`Src/Core/VeloxDev.Core.Extension/Agent/TrackedAIFunction.cs:77`, `:90`). `ConfirmMutationAsync` re-evaluates without a category guard, so a read in `Auto` mode with a judge registered can reach the judge twice (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/WorkflowAgentToolkit.cs:299-313`). A denial adds a third rule scan through `DescribePermissionRefusal`.

There is no single-pass partition of rules by decision, so an allowed call pays two scans and a denied call up to four.

## Budget enforcement

`CheckInvocation` evaluates the rule set, then, unless the mode is Bypass, reads the ledger and tests the total, read-specific, write-specific and token caps (`WorkflowAgentToolkit.cs:352-414`).

```csharp
var (spent, readCalls, writeCalls) = _ledger.Usage;
if (_scope.MaxToolCalls.HasValue && spent >= _scope.MaxToolCalls.Value)
    return BudgetRefusal($"Tool call limit ({_scope.MaxToolCalls.Value}) reached.");

bool isQueryTool = IsQueryTool(toolName);
if (!isQueryTool && _scope.MaxWriteToolCalls.HasValue && writeCalls >= _scope.MaxWriteToolCalls.Value)
    return BudgetRefusal($"Mutation tool call limit ({_scope.MaxWriteToolCalls.Value}) reached.");
if (isQueryTool && _scope.MaxReadToolCalls.HasValue && readCalls >= _scope.MaxReadToolCalls.Value)
    return BudgetRefusal($"Query tool call limit ({_scope.MaxReadToolCalls.Value}) reached.");
```

The counter read is $O(1)$; the rule evaluation before it is the only superlinear term. After a successful call, `AccountAsync` increments the ledger and, when `AutoMarkDirty` is on, marks the tree dirty for non-query tools (`WorkflowAgentToolkit.cs:469-483`). Call caps are neither enforced nor counted in Bypass; the token cap is.

## Ledger across a spawn chain

`ToolCallLedger` holds three `int` counters moved by `Interlocked` and one link to its parent (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/Functions/ToolCallLedger.cs:31-89`). `Root` is recursive, and `Spend` walks upward:

```csharp
public void Spend(bool isQuery)
{
    Interlocked.Increment(ref _total);
    if (isQuery)
        Interlocked.Increment(ref _read);
    else
        Interlocked.Increment(ref _write);

    // Walk rather than snapshot: a scope's own total must include everything its subtree spent, or the
    // sub-limit a host granted would never be reached while a child quietly spent the tree's allowance.
    Outer?.Spend(isQuery);
}
```

Accounting is therefore

$$
T_{\text{spend}} = O(d)
$$

per call and $O(d)$ per reset, with $O(1)$ storage per ledger. A child's cap is always strictly smaller than its parent's remaining allowance, which is what bounds the tree.

## Token accounting and prompt stability

Token counters are `Interlocked.Add` over up to three values. `UsageBand` folds four counters into a 20-percent bucket capped at 5 (`Src/Core/VeloxDev.Core.Extension/Agent/Workflow/WorkflowAgentScope.cs:2124-2142`), and only the band enters `ContextKey`. Quantising the counter is what keeps a ticking token count off the per-turn render path: the prompt lags actual spend by at most one bucket and stays byte-identical within a bucket.

`AppendBudgetLine` suppresses usage figures below the 80-percent band and prints a percentage above it (`WorkflowAgentScope.cs:2306-2327`). The render is $O(1)$ per line plus appended characters.

## Result-size cap

`TrackedAIFunction.CapResult` measures a string by `Length`, but for an `AIFunctionFactory` result it calls `JsonElement.GetRawText().Length` — re-materialising the payload purely to measure it (`Src/Core/VeloxDev.Core.Extension/Agent/TrackedAIFunction.cs:135-148`).

$$
T_{\text{cap}} = \begin{cases} O(1) & \text{string result} \\ O(c) & \text{JSON result} \end{cases}
$$

The payload has already been produced, so the cap bounds tokens, not memory. The same holds for `CapText`, which allocates a `Substring` of the preview after the document is complete.

## Interaction gate

`ResolveConfirmationAsync` checks a session-wide `HashSet` of approved operation keys in $O(1)$; with no handler the answer is false, and `AllowAlways` inserts the key (`WorkflowAgentScope.cs:991-1004`). `ResetToolCallLimit` is the only path that reopens a budget, and it is exempt from both the gate and the spend (`WorkflowAgentToolkit.cs:500-531`).

## Related

- [Workflow Agent Tools](../17_workflow-agent-tools/index.md) — the tools the gate admits.
- [Sub-Agents](../21_sub-agents/index.md) — the chain the ledger walks.
