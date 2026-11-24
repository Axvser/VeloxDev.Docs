# Usage

## The mode matrix

`AgentPermissionPolicy.ModeDefault(mode, category)` is the whole contract of a mode. It is five modes by five categories:

| Mode | Read | Edit | Execute | Curate | Interact |
|---|---|---|---|---|---|
| `Plan` | Allow | Deny | Deny | Deny | Allow |
| `Manual` | Allow | Ask | Ask | Ask | Allow |
| `AutoEdit` | Allow | Allow | Ask | Ask | Allow |
| `Auto` | Allow | Allow | Allow | Ask | Allow |
| `Bypass` | Allow | Allow | Allow | Allow | Allow |

`Read` and `Interact` are never put to the user in any mode. `Interact` is the asking mechanism itself — a mode that blocked it would leave the agent able to refuse but not to ask.

**Expected result:** for `AutoEdit`, a `DeleteNode` call (`Edit`) is allowed by the matrix; the rule added in Setup turns it into `Ask`.

## Evaluation order

`Evaluate` is most-powerful-first, and the order is the contract:

1. a `Deny` rule — unconditional, which is why `Bypass` is not "the safety system off";
2. `Plan`'s refusals — also unconditional, so an `Allow` rule cannot open a graph edit during planning;
3. an `Ask` rule;
4. an `Allow` rule;
5. the judge, **in `Auto` only**;
6. `ModeDefault(mode, category)`.

A judge that throws answers `Deny`, never `Allow`.

## Rule patterns

`AgentPermissionRule` selects on one axis, named by its prefix:

```csharp
var policy = AgentPermissionPolicy.For(AgentPermissionMode.Auto)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask,  "Get*"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask,  "source:mcp:filesystem"));
```

| Pattern | Matches |
|---|---|
| `DeleteNode`, `Get*` | the tool name, with `*` matching any run of characters |
| `category:Edit` | every tool in one `AgentActionCategory` |
| `source:mcp:filesystem` | tools whose origin is that MCP server; `source:mcp:management` is the MCP management toolkit |

Matching is case-insensitive and there is no escaping. A name containing `*` cannot be matched exactly; tool names are C# identifiers, so that costs nothing.

**Expected result:** `GetNodeDetail` is `Ask`, `AddMcpServer` is `Deny`, and `read_file` from `mcp:other` is unaffected by the `mcp:filesystem` rule.

## The judge

The judge is the host's answer for calls the rules and mode do not settle. It runs only in `Auto`; in `AutoEdit` the matrix already decides `Edit`, so a judge would never be asked about it.

```csharp
var judged = AgentPermissionPolicy.For(AgentPermissionMode.Auto)
    .WithJudge(call => call.Name == "RunCompiledWorkflow"
        ? PermissionDecision.Deny
        : PermissionDecision.Allow);

Console.WriteLine(judged.Evaluate(new ToolInvocation(
    "RunCompiledWorkflow", AgentActionCategory.Execute, null,
    new Dictionary<string, object?>()))); // Deny
```

**Expected result:** prints `Deny`. Replace the judge body with one that throws and the same call prints `Deny` for a different reason: a gate that cannot answer must not answer yes.

## Budgets

| Setter | Bounds |
|---|---|
| `WithMaxToolCalls` | all calls in the session |
| `WithMaxReadToolCalls` | calls the toolkit classifies as queries |
| `WithMaxWriteToolCalls` | calls that mutate the graph |
| `WithMaxTokens` | `InputTokens` / `OutputTokens` / `TotalTokens` |
| `WithMaxToolResultChars` | the size of one tool result (default 64 KiB) |

Three details decide real behaviour:

- **`Bypass` skips the three call-count caps and records no spend.** It does not skip `MaxTokens` or `Deny` rules. The prompt text is generated from the same mode, so the model is not planning around a cap that will not be enforced.
- **`ResetToolCallLimit` is always registered and always allowed.** It is the host's only exit from a budget; hiding it exactly when it is needed would be useless.
- **Sub-agents charge the same ledger.** A child's allowance is a sub-limit of its parent's, not a second pot; see [Sub-Agents](../../21_sub-agents/index.md).

**Expected result:** with `WithMaxToolCalls(2)`, a third successful call is refused; the refusal names the limit and `ResetToolCallLimit`, not just "host setting".

## Execution and generic commands

Two opt-ins sit inside the tool body rather than the shared wrapper:

```csharp
scope.WithAllowNodeExecution(true)                       // ExecuteNode / RunCompiledWorkflow
     .WithAllowedGenericCommands("SendEmail", "ExportCsv"); // ExecuteCommandOnNode / ExecuteCommandById
```

Both default off. `WithAllowNodeExecution` is what the demo needs to run node business code; leave it off when the graph is untrusted.

**Expected result:** `ExecuteNode` returns a refusal until `WithAllowNodeExecution(true)` is set.

## Verification

1. Run the complete program. It prints one decision per call and the `Bypass` cross-check.
2. Change `AutoEdit` to `Plan` and re-run: `MoveNode` flips from `Allow` to `Deny`, while an `Allow` rule on `category:Edit` cannot reopen it.
3. Add a rule with a misspelt pattern and confirm it changes nothing — an unmatched rule is silent, so read the printed decisions rather than assuming.

## Complete code

```csharp
using VeloxDev.AI.Safety;

var empty = new Dictionary<string, object?>();

var calls = new[]
{
    new ToolInvocation("MoveNode",            AgentActionCategory.Edit,    null, empty),
    new ToolInvocation("RunCompiledWorkflow", AgentActionCategory.Execute, null, empty),
    new ToolInvocation("AddMcpServer",        AgentActionCategory.Curate,  "mcp:management", empty),
    new ToolInvocation("DeleteNode",          AgentActionCategory.Edit,    null, empty),
};

var policy = AgentPermissionPolicy.For(AgentPermissionMode.AutoEdit)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask,  "DeleteNode"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"));

foreach (var call in calls)
    Console.WriteLine($"{call.Name,-22} {policy.Evaluate(call)}");

var bypass = AgentPermissionPolicy.For(AgentPermissionMode.Bypass)
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "DeleteNode"));
Console.WriteLine($"Bypass still denies: {bypass.Evaluate(calls[3])}");

var judged = AgentPermissionPolicy.For(AgentPermissionMode.Auto)
    .WithJudge(call => call.Name == "RunCompiledWorkflow"
        ? PermissionDecision.Deny
        : PermissionDecision.Allow);
Console.WriteLine($"Judge on Execute: {judged.Evaluate(calls[1])}");
```

**Expected output:**

```text
MoveNode               Allow
RunCompiledWorkflow    Ask
AddMcpServer           Deny
DeleteNode             Ask
Bypass still denies:   Deny
Judge on Execute:      Deny
```

## Run declaration

- ⚠️ Not actually run — statically verified against `Src/Core/VeloxDev.Core.Extension/Agent/Safety/AgentPermissionPolicy.cs`, `AgentPermissionRule.cs`, `ToolInvocation.cs`, and the cell-by-cell matrix in `Src/Test/Unit/Core/VeloxDev.Core.Extension.Test/Agent/Safety/AgentPermissionPolicyTests.cs`. The expected output follows that test's matrix; no run output is recorded.
