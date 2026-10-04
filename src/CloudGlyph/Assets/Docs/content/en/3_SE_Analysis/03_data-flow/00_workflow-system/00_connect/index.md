# Workflow System — Connect Flow

`SendConnection` → `ReceiveConnection` → `CreateLink`.

A connection is built in two phases. `SendConnection(sender)` validates sender capability, cleans up conflicting sender connections, shows the `VirtualLink` and sets `CurrentSender`. `ReceiveConnection(receiver)` validates capability + custom `ValidateConnection` + the same-node rule, cleans up same-direction conflicts, then `StandardCreateNewConnection` asks the tree helper for a new link and submits the whole connection as one undoable `WorkflowActionPair`.

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

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `StandardSendConnection` lines 95-126, `StandardReceiveConnection` lines 128-169, `StandardCreateNewConnection` lines 373-426.*
