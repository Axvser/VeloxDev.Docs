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
Agent -> Agent: Level>=2: do not substitute an alternative action after a deny
Agent --> User: reports the decision / blocker in its reply
@enduml
```

Notes:

- The interaction tools are only registered when a handler exists **and** safety level > 0; a `Deny` is not worked around — higher safety levels forbid substituting an alternative action.
- `SelectionResult` (single/multi/free-text) is returned from the host layer to the toolkit (`WorkflowAgentScope.SelectionResult`).

> Source: `WorkflowAgentScope.cs`, `WithSelectionHandler`/`WithConfirmationHandler`/`ResolveConfirmationAsync` lines 324-450; `WorkflowAgentToolkit.cs`, `RequestSelection` lines 2153-2194, `RequestConfirmation` lines 2197-2208.
