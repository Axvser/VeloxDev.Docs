# Data Flow — Interaction & Confirmation

When the agent hits an ambiguous or destructive action it can pause and delegate the decision to the host UI. `RequestSelection` asks the user to pick from options (plus a free-text field); `RequestConfirmation` asks for an allow/deny decision, and `AllowAlways` approvals are remembered per `operationKey` for the rest of the session (`ResolveConfirmationAsync`).

```plantuml
@startuml
actor User
participant "IAIAgent" as Agent
participant "RequestSelection / RequestConfirmation" as Tool
participant "WorkflowAgentScope" as Scope
participant "Host UI handler" as Host

Agent -> Tool: invoke interaction tool
activate Tool

alt RequestSelection(prompt, optionsJson, freeTextPrompt, allowMultiSelect)
    Tool -> Tool: parse options; null handler -> error
    Tool -> Scope: SelectionHandler(prompt, options, freeTextPrompt, allowMultiSelect)
    activate Scope
    Scope -> Host: AgentSelectionEventArgs (Prompt, Options, AllowMultiSelect, FreeTextPrompt)
    activate Host
    Host -> User: dialog (radio / checkboxes + free text)
    User --> Host: SelectedOption / SelectedOptions / FreeTextResponse
    Host --> Scope: args completed
    deactivate Host
    Scope --> Tool: SelectionResult
    deactivate Scope
    Tool --> Agent: {"status":"ok","chosen"/"chosenList","freeText"} or cancelled/rejected

else RequestConfirmation(operationKey, description)
    Tool -> Scope: ResolveConfirmationAsync(operationKey, description)
    activate Scope
    alt operationKey already AllowAlways (session cache)
        Scope --> Tool: allowed (no dialog)
    else first request
        Scope -> Host: AgentConfirmationEventArgs (OperationKey, Description)
        activate Host
        Host -> User: confirmation dialog
        User --> Host: AllowOnce / AllowAlways / Deny
        Host --> Scope: args.Result
        deactivate Host
        Scope -> Scope: remember key when AllowAlways
    end
    deactivate Scope
    alt result == Deny
        Tool --> Agent: {"status":"denied","message":"User denied ... Do NOT proceed."}
    else allowed
        Tool --> Agent: {"status":"ok","message":"User confirmed. Proceed."}
    end
end

deactivate Tool
Agent -> Agent: a Deny is not worked around; ask the user what to do instead
Agent --> User: reports the decision / blocker in its reply
@enduml
```

Notes:

- The interaction tools are registered when the matching handler exists; there is no safety-level gate. `RequestSelection` / `RequestConfirmation` are `AgentActionCategory.Interact`, which no permission mode ever puts to the user.
- An `Ask` permission decision (from the mode or a rule) reaches the same confirmation handler, keyed by the **tool name**; a `Deny` decision never asks and returns `DescribePermissionRefusal`, which names the mode or rule.
- `EnterPlanMode` / `ExitPlanMode` ask through the confirmation handler under the keys `mode:plan` / `mode:build` before moving the mode.
- `SelectionResult` (single/multi/free-text) is returned from the host layer to the toolkit (`WorkflowAgentScope.SelectionResult`).

> Source: `WorkflowAgentScope.cs` (`WithSelectionHandler`, `WithConfirmationHandler`, `ResolveConfirmationAsync`, `PermissionPolicy`); `WorkflowAgentToolkit.cs` (`RequestSelection`, `RequestConfirmation`, `EnterPlanMode`, `ExitPlanMode`).
