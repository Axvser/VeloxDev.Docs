# Permission model

The model is six types: a coarse mode, a call-time category, a tri-state decision, a pattern rule, the call being judged, and the immutable policy that combines them.

## Enum: AgentPermissionMode

How much the agent may do before it has to ask, as one named state the user can switch.

| Member | Value | Meaning |
|---|---|---|
| `Plan` | `0` | Read and propose only. Edits, execution and curation are refused. Asking is still allowed. |
| `Manual` | `1` | Every non-read action is put to the user first. |
| `AutoEdit` | `2` | Graph edits run; execution and curation ask. |
| `Auto` | `3` | Read, edit and execution run; only curation asks. The default. |
| `Bypass` | `4` | Nothing is asked. Explicit `Deny` rules still hold. |

A mode is the **coarse** layer. Rules sit beneath it and can be stricter. The host may switch modes at any moment; the gate reads the mode per call, so the next call is judged by it.

## Enum: AgentActionCategory

What a tool does, read when a call is about to run.

| Member | Value | Meaning |
|---|---|---|
| `Read` | `0` | Inspection only; cannot change anything. |
| `Edit` | `1` | Graph changes: create, delete, move, connect, patch, undo/redo. |
| `Execute` | `2` | Runs something: node code, a compiled chain, an allowlisted command, a spawned sub-agent. |
| `Curate` | `3` | Changes what the session may reach: add, load or reconfigure an MCP server. |
| `Interact` | `4` | The asking mechanism itself — selection, confirmation, budget reset. Never refused by a mode. |

`Curate` is the only category whose effects outlive the conversation. Overloading `WorkflowToolCategory` with this role would conflate "was it sent" with "may it run".

## Enum: PermissionDecision

| Member | Value | Meaning |
|---|---|---|
| `Allow` | `0` | Run without asking. |
| `Ask` | `1` | Put it to the user. With no handler registered, asking answers as a refusal. |
| `Deny` | `2` | Do not run it, and do not offer it. |

## Record: ToolInvocation

One call as the permission system sees it.

```csharp
public sealed record ToolInvocation(
    string Name,
    AgentActionCategory Category,
    string? Source,
    IReadOnlyDictionary<string, object?> Arguments);
```

| Parameter | Type | Description |
|---|---|---|
| `Name` | `string` | The tool name as the model calls it. |
| `Category` | `AgentActionCategory` | What the tool does. |
| `Source` | `string?` | Origin. An MCP server's tool carries `mcp:<server>`; the MCP management toolkit carries `mcp:management`; every other tool is `null`. |
| `Arguments` | `IReadOnlyDictionary<string, object?>` | The model-supplied arguments, as they arrived. |

Arguments are present because some policies are about what the call would do: adding an MCP server from a local package installs software, while an HTTP endpoint only sends data out.

## Record: AgentPermissionRule

```csharp
public sealed record AgentPermissionRule(PermissionDecision Decision, string Pattern);
```

A rule selects on one axis, named by its prefix.

| Pattern | Matches |
|---|---|
| `DeleteNode`, `Get*`, `mcp:*` | The tool name, with `*` matching any run of characters. |
| `category:Edit` | Everything in one `AgentActionCategory`. |
| `source:mcp:*`, `source:mcp:filesystem`, `source:mcp:management` | Where the tool came from; only MCP tools carry a source. |

Matching is case-insensitive, with no escaping. A name containing `*` cannot be matched exactly; tool names are C# identifiers, so that costs nothing.

| Member | Signature | Description |
|---|---|---|
| `Matches` | `bool Matches(ToolInvocation invocation)` | Whether the rule is about the invocation. Throws `ArgumentNullException` when null. |

## Class: AgentPermissionPolicy

The session's policy: one mode, an ordered rule list, and an optional judge used in `Auto` only. It is immutable; every `With*` returns a new policy, so a reader evaluating a call holds one consistent rule set.

| Member | Type / Signature | Description |
|---|---|---|
| `Mode` | `AgentPermissionMode` | The mode in force. |
| `Rules` | `IReadOnlyList<AgentPermissionRule>` | The host's rules, in the order added. |
| `Judge` | `Func<ToolInvocation, PermissionDecision>?` | Decides calls the rules and mode do not settle, in `Auto`. |
| `DefaultMode` | `static AgentPermissionMode` | `Auto`. Graph work runs; the asking moves to changing what the session may reach. |
| `For` | `static AgentPermissionPolicy For(AgentPermissionMode mode)` | A policy with no rules and no judge. |
| `WithMode` | `AgentPermissionPolicy WithMode(AgentPermissionMode mode)` | A new policy in another mode. |
| `WithRule` | `AgentPermissionPolicy WithRule(AgentPermissionRule rule)` | Adds one rule; rules are evaluated by decision, not position. |
| `WithRules` | `AgentPermissionPolicy WithRules(IEnumerable<AgentPermissionRule> rules)` | Adds several rules. |
| `WithoutRules` | `AgentPermissionPolicy WithoutRules()` | A policy with no rules; the mode is untouched. |
| `WithJudge` | `AgentPermissionPolicy WithJudge(Func<ToolInvocation, PermissionDecision>? judge)` | Sets or removes the judge. |
| `Evaluate` | `PermissionDecision Evaluate(ToolInvocation invocation)` | Decides one call. Throws `ArgumentNullException` when null. |
| `ModeDefault` | `static PermissionDecision ModeDefault(AgentPermissionMode mode, AgentActionCategory category)` | The mode's answer with no rules or judge in play. |

### Evaluation order

`Evaluate` is most-powerful-first, and the order is the contract:

1. a `Deny` rule — unconditional, so `Bypass` is not "the safety system off";
2. `Plan`'s refusals — also unconditional; an `Allow` rule cannot open a graph edit while planning;
3. an `Ask` rule;
4. an `Allow` rule;
5. the judge, in `Auto` only;
6. `ModeDefault(mode, category)`.

A judge that throws answers `Deny`, never `Allow`.

### Mode matrix

`ModeDefault` is five modes by five categories.

| Mode | Read | Edit | Execute | Curate | Interact |
|---|---|---|---|---|---|
| `Plan` | Allow | Deny | Deny | Deny | Allow |
| `Manual` | Allow | Ask | Ask | Ask | Allow |
| `AutoEdit` | Allow | Allow | Ask | Ask | Allow |
| `Auto` | Allow | Allow | Allow | Ask | Allow |
| `Bypass` | Allow | Allow | Allow | Allow | Allow |

### Example

```csharp
using VeloxDev.AI.Safety;

var policy = AgentPermissionPolicy.For(AgentPermissionMode.AutoEdit)
    .WithRule(new AgentPermissionRule(PermissionDecision.Ask, "DeleteNode"))
    .WithRule(new AgentPermissionRule(PermissionDecision.Deny, "category:Curate"));

var call = new ToolInvocation(
    "DeleteNode", AgentActionCategory.Edit, null,
    new Dictionary<string, object?>());

Console.WriteLine(policy.Evaluate(call)); // Ask
```

## Related

- [Scope safety](../01_scope-safety/index.md) — configuring this policy on a `WorkflowAgentScope`.
- [Budgets and dirty marking](../02_budgets/index.md) — the spend limits alongside permissions.
