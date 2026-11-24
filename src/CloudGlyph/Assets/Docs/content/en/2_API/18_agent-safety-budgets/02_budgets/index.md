# Budgets and dirty marking

The same scope that decides *whether* a call may run also decides *how much* the session may spend. Five caps are available; each is enforced before a call and named in the refusal.

## Call and token caps

| Member | Signature | Description |
|---|---|---|
| `WithMaxToolCalls` | `WorkflowAgentScope WithMaxToolCalls(int maxCalls)` | Caps total tool calls for the scope's lifetime, until `ResetToolCallLimit` clears the ledger. Not counted or enforced in `Bypass`. |
| `WithMaxReadToolCalls` | `WorkflowAgentScope WithMaxReadToolCalls(int maxCalls)` | Caps read-only (query) calls. Use it to stop token-heavy queries from consuming the mutation budget. |
| `WithMaxWriteToolCalls` | `WorkflowAgentScope WithMaxWriteToolCalls(int maxCalls)` | Caps mutation (non-query) calls. |
| `WithMaxToolResultChars` | `WorkflowAgentScope WithMaxToolResultChars(int maxChars)` | Caps one tool result's text. Over the cap, the result is replaced by a truncation envelope. `0` disables the cap. Default 64 KiB. |
| `WithMaxTokens` | `WorkflowAgentScope WithMaxTokens(int maxTokens)` | Caps total tokens. Once the reported total reaches it, tool calls are refused; the model may still answer. Unlike the call caps, this one is enforced in `Bypass`. |

## Spend properties

| Member | Type | Description |
|---|---|---|
| `MaxToolCalls` | `int?` | The total-call cap, or `null` for none. |
| `MaxToolResultChars` | `int` | The result-size cap. |
| `MaxTokens` | `int?` | The token cap, or `null`. |
| `InputTokens` / `OutputTokens` / `TotalTokens` | `long` | Provider-reported spend for this scope's runs. |
| `ResetTokenUsage()` | `void` | Clears the reported token counters so a later switch can spend the budget again. |

## Behaviour that decides outcomes

- **`Bypass` skips the three call-count caps and records no spend.** It does not skip `MaxTokens` or `Deny` rules. The prompt text is generated from the same mode, so the model is not planning around a cap that will not be enforced.
- **`ResetToolCallLimit` is always registered and always allowed.** It is the host's only exit from a call budget, so it cannot be switched off or filtered away. Calling it asks the user; only their agreement reopens the budget.
- **Sub-agents charge the same ledger.** A child's allowance is a sub-limit of its parent's, not a second pot; the root cap is the tree's cap. See [Sub-Agents](../../21_sub-agents/index.md).

A budget refusal names the limit and `ResetToolCallLimit` rather than reporting a vague host setting.

## Dirty marking

| Member | Signature | Description |
|---|---|---|
| `AutoMarkDirty` | `bool AutoMarkDirty { get; }` | Whether mutating tool calls automatically mark the tree dirty. |
| `WithAutoMarkDirty` | `WorkflowAgentScope WithAutoMarkDirty(bool enabled = false)` | When `true`, every mutation tool call marks the tree dirty and the agent need not call `MarkDirty`. When `false` (default), the injected prompt instructs the agent to call `MarkDirty` once at the end of a mutation task. Query tools never auto-mark. |

## Example

```csharp
scope.WithMaxToolCalls(200)
     .WithMaxReadToolCalls(150)
     .WithMaxWriteToolCalls(50)
     .WithMaxToolResultChars(48 * 1024)
     .WithMaxTokens(200_000);
```

With `WithMaxToolCalls(2)`, a third successful call is refused and the refusal names the limit and `ResetToolCallLimit`.

## Related

- [Permission model](../00_permission-model/index.md) — the deny-first evaluation order that budgets cooperate with.
- [Scope safety](../01_scope-safety/index.md) — execution and command opt-ins.
- [Sub-Agents](../../21_sub-agents/index.md) — how a child draws on the root ledger.
