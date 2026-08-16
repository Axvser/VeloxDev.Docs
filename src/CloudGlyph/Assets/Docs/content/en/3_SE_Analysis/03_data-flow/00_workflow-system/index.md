# Data Flow — Workflow System

Five PlantUML sequence diagrams trace the main data flows. Every participant is declared, every `activate` has a matching `deactivate`, and `alt/else/end` blocks are balanced.

## 1. Connect Flow — `SendConnection` → `ReceiveConnection` → `CreateLink`

A connection is built in two phases. `SendConnection(sender)` checks sender capacity, shows the `VirtualLink` and sets `PreviewSender`. `ReceiveConnection(receiver)` validates capacity + `ValidateConnection`, cleans up conflicting same-direction links, creates the link via `GetHelper().CreateLink(...)`, and submits the whole connection as one undoable `WorkflowActionPair`.

```plantuml
@startuml
    participant Caller
participant "IWorkflowTreeViewModel" as Tree
participant "Slot(sender)" as Sender
participant "Slot(receiver)" as Receiver
participant "IWorkflowLinkViewModel" as Link
participant "TreeCache(UndoStack)" as Cache

    == SendConnection ==
    Caller -> Tree: SendConnectionCommand.Execute(sender)
    activate Tree
    Tree -> Sender: StandardCanBeSender()
    alt not canBeSender
        Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
    else canBeSender
        Tree -> Tree: StandardSmartCleanupSenderConnections(sender)
        Tree -> Tree: VirtualLink.IsVisible = true
        Tree -> Sender: State = PreviewSender; UpdateState()
        Tree --> Caller: CurrentSender = sender
    end

    == ReceiveConnection ==
    Caller -> Tree: ReceiveConnectionCommand.Execute(receiver)
    alt CurrentSender == null
        Tree --> Caller: no-op (return)
    else CurrentSender != null
        Tree -> Receiver: StandardCanBeReceiver()
        Tree -> Tree: GetHelper().ValidateConnection(CurrentSender, receiver)
        alt invalid (capacity / validation / same parent)
            Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
        else valid
            Tree -> Tree: StandardCleanupSameDirectionConnections / StandardSmartCleanupReceiverConnections
            Tree -> Link: GetHelper().CreateLink(sender, receiver)
            activate Link
            Link --> Tree: new link (IsVisible = true)
            deactivate Link
            Tree -> Cache: StandardSubmit(new WorkflowActionPair(...))
            activate Cache
            Cache -> Cache: redo: LinksMap[s][r] = link; Links.Add; Targets/Sources.Add
            deactivate Cache
            Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
        end
    end
    deactivate Tree
@enduml
```

Error path: any failed validation (capacity, custom `ValidateConnection`, same-node connection) resets the virtual link and leaves no connection; existing same-direction connections are atomically replaced through a submitted `WorkflowActionPair`.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `StandardSendConnection` lines 97-128, `StandardReceiveConnection` lines 130-171, `StandardCreateNewConnection` lines 375-428.*

## 2. Compile + Run — `CompileAsync` → `CompilerEngine.RunAsync` → `ReceiveAsync`

`CompilerViewModel.CompileAsync(start)` decomposes the subgraph reachable from the start node into `CompiledGraph`s (linear segments → `ExecuteEntry`, branches → `BranchEntry`, fan-outs → `ParallelEntry`). `CompilerEngine.RunAsync(graph, context, ct)` drives entries one by one, invoking each node's `ReceiveCommand → ReceiveAsync(context, ct)` and writing the return value back to `RuntimeContext.Data` to chain to the next node.

```plantuml
@startuml
    participant Caller
participant "CompilerViewModel" as Compiler
participant "CompilerEngine" as Engine
    participant Graph as CompiledGraph
participant "ActionEntry" as Entry
participant "ReceiveCommand" as Cmd
participant "NodeHelper" as Helper
participant "RuntimeContext" as Context

    == Compile ==
    Caller -> Compiler: CompileAsync(start)
    activate Compiler
    Compiler -> Compiler: walk Nodes / Slots / Targets (visited set)
    Compiler -> Compiler: decompose linear / branch / fan-out entries
    Compiler --> Caller: IReadOnlyList<CompiledGraph>
    deactivate Compiler

    == RunAsync (drive entries) ==
    Caller -> Engine: RunAsync(graph, context, ct)
    activate Engine
    Engine -> Context: IsRunning = true; Status = "Running"
    Engine -> Context: inject IRuntimeAware nodes before each drive
    loop each entry in graph.Entries
        Engine -> Entry: drive entry
        alt ExecuteEntry (linear chain)
            loop each node in Entry.Nodes
                Engine -> Cmd: ReceiveCommand.ExecuteAsync(context)
                activate Cmd
                Cmd -> Helper: ReceiveAsync(context, ct)
                activate Helper
                Helper -> Context: mutate Data / logs / shared variables
                Helper --> Cmd: result
                deactivate Helper
                Cmd --> Engine: result
                deactivate Cmd
                Engine -> Context: Data = result (chain to next node)
            end
        else BranchEntry (router)
            Engine -> Engine: pick branch via CompileKey (static) or ResolveRouteKey (dynamic)
        else ParallelEntry (fan-out)
            Engine -> Engine: run each branch graph in order (join semantics)
        end
    end
    Engine --> Caller: Status = "Completed" / "Stopped"
    deactivate Engine
@enduml
```

Cancellation path: `ct.ThrowIfCancellationRequested()` aborts the chain; an `OperationCanceledException` from a node rethrows immediately (cancellation is not a redirect).

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerViewModel.cs`, `CompilerEngine.cs` (`RunGraphAsync` lines 63-89, `RunExecuteAsync` lines 96-148). Test evidence: `CompilerExTests.CompileThenRun_EngineDrivesGraph_WithRuntimeContext`.*

## 3. Undo / Redo

Every mutating operation is submitted as a `WorkflowActionPair(redo, undo)` onto a `ConcurrentStack`. `UndoCommand` pops the pair and runs its `Undo` action, then pushes it onto the redo stack; `RedoCommand` does the inverse.

```plantuml
@startuml
    participant Caller
participant "IWorkflowTreeViewModel" as Tree
participant "TreeCache(UndoStack/RedoStack)" as Cache
participant "WorkflowActionPair" as Pair
    participant Node as IWorkflowNodeViewModel

    == Undo ==
    Caller -> Tree: UndoCommand.Execute(null)
    activate Tree
    Tree -> Cache: StandardUndo()
    activate Cache
    Cache -> Cache: UndoStack.TryPop(out pair)
    alt pair found
        Cache -> Pair: pair.Undo.Invoke()
        activate Pair
        Pair -> Tree: undo: Nodes.Remove(node); node.Parent = oldParent
        deactivate Pair
        Cache -> Cache: RedoStack.Push(pair)
    else stack empty
        Tree --> Caller: no-op
    end
    deactivate Cache
    deactivate Tree

    == Redo ==
    Caller -> Tree: RedoCommand.Execute(null)
    activate Tree
    Tree -> Cache: StandardRedo()
    activate Cache
    Cache -> Cache: RedoStack.TryPop(out pair)
    alt pair found
        Cache -> Pair: pair.Redo.Invoke()
        activate Pair
        Pair -> Tree: redo: Nodes.Add(node); node.Parent = tree
        deactivate Pair
        Cache -> Cache: UndoStack.Push(pair)
    else stack empty
        Tree --> Caller: no-op
    end
    deactivate Cache
    deactivate Tree
@enduml
```

Error path: if `pair.Redo/Undo.Invoke()` throws, `StandardSubmit`/`StandardUndo`/`StandardRedo` catch the exception and log via `Debug.WriteLine` — the stack is left unchanged.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `StandardSubmit` lines 210-222, `StandardUndo` lines 224-239, `StandardRedo` lines 193-208.*

## 4. Error / Redirect — `RuntimeContext.Error()` → `IRedirectable` re-run

A node that calls `RuntimeContext.Error()/Warn()` or throws during `ReceiveAsync` requests a redirect. If it implements `IRedirectable`, the engine re-runs the whole graph from the returned `CompileContext.Order` (skipping earlier nodes, possibly cross-chain); otherwise the flow ends with status `-1`.

```plantuml
@startuml
participant "CompilerEngine" as Engine
participant "IWorkflowNodeViewModel" as Node
participant "RuntimeContext" as Context
participant "IRedirectable" as Redirectable

    == Drive node ==
    Engine -> Node: ReceiveAsync(context, ct)
    activate Node
    Node -> Context: Error(message) / Warn(message)
    Context -> Context: RedirectRequested = true
    Node --> Engine: returns or throws
    deactivate Node

    == Resolve redirect ==
    alt node is IRedirectable
        Engine -> Redirectable: ResolveRedirectAsync(context, ct)
        activate Redirectable
        Redirectable --> Engine: target Order (int?) / null
        deactivate Redirectable
        alt target is valid (targetOrder < current order)
            Engine -> Context: PendingRedirectTarget = targetOrder
            Engine -> Engine: re-run whole graph from target Order (skip earlier nodes, may cross chains)
        else null / invalid
            Engine -> Engine: continue current chain
        end
    else node is not IRedirectable
        Engine -> Context: CurrentOrder = -1; EndedWithError = true
        Engine -> Engine: flow ends, Status = "Stopped"
    end
@enduml
```

Redirects are abandoned after 50 attempts (`MaxRedirects` → throws `InvalidOperationException`). If the target Order is a Router, the engine re-routes only without recomputing the router.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerEngine.cs` (`RunAsync` lines 20-60, `RunExecuteAsync` lines 96-148), `IRedirectable.cs`. Test evidence: `RedirectTests.RedirectGate_RedirectsToChainHead_ThenSucceeds`, `RedirectTests.RedirectCrossChain_SkipsPriorAndReruns`, `RedirectTests.RedirectToRouter_ReroutesWithoutRecompute`.*

## 5. Async / Serialization — `Serialize` / `Deserialize`

`ComponentModelEx` serializes the whole graph to JSON via Newtonsoft with `PreserveReferencesHandling.Objects` and a writable-properties-only resolver; deserialization rebuilds the graph and re-resolves `SlotEnumerator.SelectorType` from the serialized `SelectorTypeName`. The caller then re-applies layout via `Layout.UpdateCommand`.

```plantuml
@startuml
    participant Caller
participant "IWorkflowTreeViewModel" as Tree
participant "ComponentModelEx(Newtonsoft)" as Serializer
participant "CanvasLayout" as Layout

    == Serialize ==
    Caller -> Serializer: tree.Serialize()
    activate Serializer
    Serializer -> Tree: read Nodes / Slots / Links / Layout / VeloxProperty data
    Serializer -> Serializer: JsonConvert.SerializeObject (PreserveReferences, WritablePropertiesOnlyResolver)
    Serializer --> Caller: JSON string
    deactivate Serializer

    == Deserialize ==
    Caller -> Serializer: json.Deserialize<TreeViewModel>()
    activate Serializer
    Serializer -> Serializer: JsonConvert.DeserializeObject<T> (TypeNameHandling.Auto, PreserveReferences)
    Serializer -> Tree: build nodes / slots / links; re-resolve SlotEnumerator SelectorType from SelectorTypeName
    Serializer --> Caller: restored tree
    deactivate Serializer

    == Re-apply layout ==
    Caller -> Layout: copy.Layout.UpdateCommand.Execute(null)
    activate Layout
    Layout -> Layout: recompute ActualSize / ActualOffset from OriginSize + offsets
    deactivate Layout
@enduml
```

Error path: `TryDeserialize` returns `false` for null/empty/malformed input without throwing; `Deserialize` throws `JsonSerializationException` when the result is null.

*Source: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`. Test evidence: `WorkflowSerializationTests.TreeWithEnumNode_RoundTripsSelectorType`. Demo load path: `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, lines 46-51.*
