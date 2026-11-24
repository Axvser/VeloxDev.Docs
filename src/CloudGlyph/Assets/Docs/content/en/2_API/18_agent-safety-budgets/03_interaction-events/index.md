# Interaction events

These Core types carry the data a host handler receives and a caller observes. They live in `VeloxDev.AI`, not in the safety namespace, because they describe the agent-facing contract rather than the policy engine.

## Class: AgentToolCallEventArgs

Provides data for `IAgentToolCallNotifier.ToolCalled`, raised after each **successful** tool invocation. Refused and failed calls travel as `AgentToolCallCompleted` on the scope's pipeline instead.

| Member | Type | Description |
|---|---|---|
| `ToolName` | `string` | The invoked tool's name. Throws `ArgumentNullException` at construction when null. |
| `Result` | `string` | The JSON result; empty when none. |
| `CallCount` | `int` | Cumulative calls in the session. In `Bypass` mode no spend is recorded, so it reports `0` for every call there. |

## Interface: IAgentToolCallNotifier

The contract for a scope or toolkit that raises `ToolCalled`.

| Member | Signature | Description |
|---|---|---|
| `ToolCalled` | `event EventHandler<AgentToolCallEventArgs>? ToolCalled` | Raised after a successful invocation. |

## Class: AgentSelectionEventArgs

Data for the `RequestSelection` tool.

| Member | Type | Description |
|---|---|---|
| `Prompt` | `string` | The question shown above the option list. |
| `Options` | `IReadOnlyList<string>` | The ordered candidate strings. |
| `AllowMultiSelect` | `bool` | `true` for checkboxes, `false` (default) for radio buttons. |
| `FreeTextPrompt` | `string` | Label above the free-text field. Defaults to `"Custom input (optional)"`. |
| `SelectedOption` | `string?` | Single-select answer; set by the handler before completing. |
| `SelectedOptions` | `IReadOnlyList<string>?` | Multi-select answer; set by the handler. |
| `FreeTextResponse` | `string?` | Free-text answer; `null` or empty when none. |

A free-text field is always shown below the options.

## Class: AgentConfirmationEventArgs

Data for the `RequestConfirmation` tool.

| Member | Type | Description |
|---|---|---|
| `OperationKey` | `string` | A stable, machine-readable key for the operation type, e.g. `"DeleteNode"`. Persisted approvals are keyed on it. |
| `Description` | `string` | A human-readable explanation shown as the dialog body. |
| `Result` | `AgentConfirmationResult` | The user's decision; defaults to `Deny`. Set by the handler before completing. |

## Enum: AgentConfirmationResult

| Member | Meaning |
|---|---|
| `Deny` | The user refused; the agent must not proceed. |
| `AllowOnce` | Allow this request only; an identical request asks again. |
| `AllowAlways` | Allow the operation for the rest of the session, silently approving later requests with the same `OperationKey`. |

## Notes

`IAgentSelectionNotifier` and `IAgentConfirmationNotifier` exist in Core but are marked obsolete. No library type implements or raises them: hosts supply a handler through `WithSelectionHandler` / `WithConfirmationHandler` instead, and the interfaces are kept only so existing source still compiles.

## Related

- [Scope safety](../01_scope-safety/index.md) — where these handlers are registered.
- [Agent Dashboard and Transcript](../../22_agent-dashboard-transcript/index.md) — the pipeline events that carry refused and failed calls.
