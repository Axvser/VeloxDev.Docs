# Scope safety

These `WorkflowAgentScope` members attach a permission policy and the opt-ins that sit inside tool bodies. Each returns the same scope for chaining.

## Permission members

| Member | Signature | Description |
|---|---|---|
| `PermissionPolicy` | `AgentPermissionPolicy PermissionPolicy { get; }` | The policy in force. Never `null`. |
| `PermissionMode` | `AgentPermissionMode PermissionMode { get; }` | The mode in force. |
| `WithPermissionMode` | `WorkflowAgentScope WithPermissionMode(AgentPermissionMode mode)` | Moves the session to another mode during construction. |
| `SetPermissionMode` | `bool SetPermissionMode(AgentPermissionMode mode)` | Runtime counterpart for a host driven by a binding; returns whether the mode moved. |
| `WithPermissionRule` | `WorkflowAgentScope WithPermissionRule(PermissionDecision decision, params string[] patterns)` | Adds one rule per pattern beneath the mode. A rule holds in every mode, including `Bypass`. |
| `WithoutPermissionRules` | `WorkflowAgentScope WithoutPermissionRules()` | Removes every rule; the mode is untouched. |
| `WithPermissionJudge` | `WorkflowAgentScope WithPermissionJudge(Func<ToolInvocation, PermissionDecision>? judge)` | Supplies the `Auto`-mode judge, or `null` to remove it. |
| `WithModePrompt` | `WorkflowAgentScope WithModePrompt(AgentPermissionMode mode, string? promptBody)` | Appends host rules after the library's shipped text for one mode. The shipped text is not replaced; the addition is presented as taking priority. `null` removes the addition. |

The policy is read per call, so a mode set with `SetPermissionMode` governs the very next tool call. Prompt text catches up on the next turn.

```csharp
using VeloxDev.AI.Safety;

scope.WithPermissionMode(AgentPermissionMode.AutoEdit)
     .WithPermissionRule(PermissionDecision.Ask, "DeleteNode", "DeleteSlot", "DisconnectSlots");
```

## Execution opt-ins

Two independent controls sit **inside** the tool bodies rather than in the shared wrapper. Both default off.

| Member | Signature | Description |
|---|---|---|
| `WithAllowNodeExecution` | `WorkflowAgentScope WithAllowNodeExecution(bool enabled = false)` | Allows `ExecuteNode`, `ExecuteNodes`, `BroadcastNode`, `ReverseBroadcastNode`, `RunCompiledWorkflow` and the related execution tools. These run arbitrary business code, so a graph from an untrusted source should leave this off. |
| `WithAllowedGenericCommands` | `WorkflowAgentScope WithAllowedGenericCommands(params string[] commandNames)` | Allowlists command names for `ExecuteCommandOnNode` and `ExecuteCommandById`. The `Command` suffix is optional. When never called, generic command execution is disabled entirely. |

Security is enforced here, not in prompt prose. The mode still gates the calls; these switches decide whether the tool is registered as executable at all.

## Interaction handlers

| Member | Signature | Description |
|---|---|---|
| `WithSelectionHandler` | `WorkflowAgentScope WithSelectionHandler(Func<AgentSelectionEventArgs, Task> handler)` | Registers the handler for `RequestSelection`. When `null`, the tool is not registered at all. |
| `WithConfirmationHandler` | `WorkflowAgentScope WithConfirmationHandler(Func<AgentConfirmationEventArgs, Task> handler)` | Registers the handler for `RequestConfirmation`. When `null`, the tool is not registered. |

A handler must set the result fields on the event args before completing. Interaction tools are never blocked by a mode: asking is how a plan gets agreed to.

## Nested class: WorkflowAgentScope.SelectionResult

Carries the result of a selection interaction.

| Member | Type / Signature | Description |
|---|---|---|
| `SelectedOption` | `string?` | For single-select: the chosen option, or `null` when cancelled. |
| `SelectedOptions` | `IReadOnlyList<string>` | For multi-select: the chosen options; empty when none. |
| `FreeTextResponse` | `string?` | The free-text input, or `null`. |
| `Single` | `static SelectionResult Single(string? option)` | Creates a single-select result. |
| `Multi` | `static SelectionResult Multi(IReadOnlyList<string> options, string? freeText = null)` | Creates a multi-select result. |
| `FreeText` | `static SelectionResult FreeText(string text)` | Creates a free-text-only result. |

## Related

- [Permission model](../00_permission-model/index.md) — the policy these members configure.
- [Budgets and dirty marking](../02_budgets/index.md) — spend caps on the same scope.
- [Interaction events](../03_interaction-events/index.md) — the event-args shapes.
