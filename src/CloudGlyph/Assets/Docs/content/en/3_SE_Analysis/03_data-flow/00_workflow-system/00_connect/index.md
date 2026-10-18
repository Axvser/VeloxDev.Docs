# Workflow System — Connect Flow

`SendConnection` → `SetPreviewReceiver` (zero or more) → `ReceiveConnection` → `CreateLink`.

A connection is built in two phases, with a preview stage in between. `SendConnection(sender)` validates sender capability, cleans up conflicting sender connections, shows the `VirtualLink` and sets `CurrentSender`. While the pointer moves, `SetPreviewReceiver(candidate)` computes the framework check, marks the candidate, and publishes the stage. `ReceiveConnection(receiver)` validates capability + custom `ValidateConnection` + the same-node rule, cleans up same-direction conflicts, then `StandardCreateNewConnection` asks the tree helper for a new link and submits the whole connection as one undoable `WorkflowActionPair`.

The preview and the completion share **one rule set** (`StandardCheckConnection`), so the red/green rubber band and the final acceptance cannot disagree about direction, same-node or the host's `ValidateConnection`. The release-time `IWorkflowTreeEvents.Connecting` veto is deliberately *not* part of the preview: it is a per-attempt decision raised only on release.

```plantuml
@startuml
!theme plain
participant User
participant "Tree (IWorkflowTreeViewModel)" as Tree
participant "Sender slot" as Sender
participant "Receiver slot" as Receiver
participant "TreeHelper" as Helper

== SendConnection ==
User -> Tree: SendConnectionCommand.Execute(sender)
activate Tree
alt not StandardCanBeSender(sender)
    Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
else can send
    Tree -> Tree: StandardSmartCleanupSenderConnections(sender)
    Tree -> Tree: VirtualLink.IsVisible = true
    Tree -> Sender: State = PreviewSender; UpdateState()
    Tree --> User: CurrentSender = sender
end

== Pointer move (preview) ==
User -> Tree: StandardSetPreviewReceiver(candidate)
Tree -> Tree: StandardCheckConnection(sender, candidate)   [pure; first refusal wins]
alt candidate is sender, or no candidate
    Tree -> Tree: PreviewReceiver = null; state = Started
else framework check passed
    Tree -> Tree: PreviewValidating (host may Reject for this preview only)
    Tree -> Tree: slot.State |= PreviewReceiver; PreviewState = ValidTarget / InvalidTarget
    Tree -> Tree: ((IConnectionPreviewLink)VirtualLink).SetPreview(state)
end
Tree -> User: PreviewChanged(sender, candidate, state, check)

== ReceiveConnection ==
User -> Tree: ReceiveConnectionCommand.Execute(receiver)
alt CurrentSender == null
    Tree --> User: no-op
else CurrentSender != null
    Tree -> Tree: StandardCanBeReceiver(receiver) check
    Tree -> Helper: ValidateConnection(CurrentSender, receiver)
    alt invalid (capacity / validation / same parent node)
        Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
    else valid
        Tree -> Tree: cleanup same-direction + smart receiver cleanup
        Tree -> Helper: CreateLink(sender, receiver)
        Helper --> Tree: new link (IsVisible = true)
        Tree -> Tree: StandardCreateNewConnection submits WorkflowActionPair(redo, undo)
        Tree -> Tree: redo: LinksMap[s][r]=link; Links.Add; Targets/Sources.Add
        Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
    end
end
deactivate Tree
@enduml
```

The submitted pair is executed immediately (`redo`) and pushed onto the undo stack; `StandardUndo`/`StandardRedo` later run `undo`/`redo` and swap stacks (see the Command-pattern page in the design-patterns dimension). Any failed validation resets the virtual link and leaves no connection.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs` — `StandardSendConnection` lines 105-137, `StandardSetPreviewReceiver` 150-152, `StandardRefreshConnectionPreview` 162-174, `StandardCheckConnection` 195-216, `StandardReceiveConnection` 253-307, `StandardCreateNewConnection` 517-570; `StandardEx/WorkflowSlotEx.cs` — `StandardUpdateState` 93-106. Preview behavior: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowConnectionPreviewTests.cs`.*
