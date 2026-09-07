# Data Flow — Workflow System

PlantUML sequence diagrams trace the core data flows of the workflow-system feature. Participants are declared before use, `activate`/`deactivate` are balanced, and `alt/else/end` blocks are balanced.

## 1. Connect Flow — `SendConnection` → `ReceiveConnection` → `CreateLink`

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

The submitted pair is executed immediately (`redo`) and pushed onto the undo stack; `StandardUndo`/`StandardRedo` later run `undo`/`redo` and swap stacks (see the [Command pattern](../../02_design-patterns/00_workflow-system/03_command-pattern/index.md)). Any failed validation resets the virtual link and leaves no connection.

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, `StandardSendConnection` lines 97-128, `StandardReceiveConnection` lines 130-171, `StandardCreateNewConnection` lines 375-428.*

## 2. Compile + Run (Root) — `CompileAsync(role: Root)` → `RuntimeEngine.RunAsync` → `ReceiveAsync`

Two phases. **Compile** walks the sub-graph reachable from the controller and builds immutable segments: linear runs become `ChainSegment`, a node implementing `ICompileTimeRouter` becomes a `BranchSegment`, a multi-target fan-out becomes a `ParallelSegment`. Each node's output edge is statically validated by calling the sender's `AccessAsync` with an `ICompileContext` (a rejected edge is treated as unconnected and omitted); every reachable node receives a fixed compile identity (`Order`/`ChainIndex`/`Offset`) via `ICompileTimeAware`, and multi-input join points are registered with their input source nodes. **Run** drives those segments: the engine owns downstream dispatch, calls `Helper.ReceiveAsync` directly with an `IRuntimeContext`, writes the return value back as `context.Data`, and registers each node's output.

```plantuml
@startuml
!theme plain
participant Caller
participant "CompilerViewModel" as Compiler
participant "Node / Router" as Node
participant "Helper" as Helper
participant "RuntimeEngine" as Engine
participant "RuntimeContext" as Context

== Compile (Root) ==
Caller -> Compiler: CompileAsync(controller, CompileRole.Root)
activate Compiler
Compiler -> Node: GetValidTargetsAsync walks output edges
Compiler -> Helper: AccessAsync(ICompileContext with Sender/Receiver)
Helper --> Compiler: bool (false ⇒ edge pruned as unconnected)
Compiler -> Node: AttachCompileTimeContext (Order / ChainIndex / Offset)
Compiler -> Compiler: decompose ChainSegment / BranchSegment / ParallelSegment
Compiler -> Compiler: static mode prunes unselected branches (Order = -1); register join InputNodes
Compiler --> Caller: CompiledGraph (stored in Graphs)
deactivate Compiler

== Run (RuntimeEngine) ==
Caller -> Engine: RunAsync(graph, context, ct)
activate Engine
Engine -> Context: IsRunning=true; Status=Running; ResetOutputs(); TargetReached=false
loop each pass (Attempt++) and each segment in graph.Entries
    alt ChainSegment
        Engine -> Node: DriveAsync(node)
        Engine -> Context: CurrentOrder = node.Order
        Engine -> Helper: ReceiveAsync(context, ct)   // context is IRuntimeContext
        activate Helper
        Helper -> Context: read Data / Set / TryGet / Log
        Helper --> Engine: result
        deactivate Helper
        Engine -> Context: RegisterOutput(node, result); Data = result
    else BranchSegment
        Engine -> Node: DriveAsync(Router) unless re-route-only
        Engine -> Engine: key = IsDynamic ? ResolveRouteKey(context) : CompileKey
        Engine -> Engine: run chosen Option.Graph (IsTerminal option ends the run)
    else ParallelSegment
        Engine -> Engine: foreach branch: Data = sourceData (restore fan-out payload); run branch
    end
end
Engine --> Caller: Status = EndedWithError ? "Stopped" : "Completed"
deactivate Engine
@enduml
```

Cancellation path: `ct.ThrowIfCancellationRequested()` aborts the pass; `OperationCanceledException` from a node is rethrown immediately (cancellation is **not** a redirect) and `RunAsync` sets `Status = "Stopped"`.

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs` (lines 26-57 entry, 59-232 decomposition, 385-430 `GetValidTargetsAsync`); `CompilerEx/Runtime/RuntimeEngine.cs` (`RunAsync` lines 19-68, `RunExecuteAsync` 106-160, `RunParallelAsync` 205-214, `DriveAsync` 227-261). Demo: `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` lines 30-58. Test evidence: `CompilerEx/RuntimeEngineRunTests.cs`, `CompilerEx/EntrySemanticsTests.cs`.*

## 3. Reverse / Terminal cone flow — `CompileAsync(role: Terminal)` → run with `Target`

`CompileRole.Terminal` computes a sink node's result from its **ancestor cone**: reverse BFS over `Sources`, validating each edge with the sender's `AccessAsync` (rejected edges are not ancestors). The cone's own entry frontier (nodes with no in-cone input) is derived automatically — no controller/start node required. A router on the cone **keeps real `BranchSegment` semantics** but only the branch that leads into the cone is compiled (`RestrictRouteToCone`); several independent producers funnel into the target as a `ParallelSegment` then a common join chain. Reachability is reported by `RuntimeContext.Target`/`TargetReached`; no value is fabricated.

```plantuml
@startuml
!theme plain
participant Caller
participant "CompilerViewModel" as Compiler
participant "Producer nodes" as Producer
participant "RuntimeEngine" as Engine
participant "RuntimeContext" as Context
participant "Router (ICompileTimeRouter)" as Router

== Compile (Terminal) ==
Caller -> Compiler: CompileAsync(target, CompileRole.Terminal)
activate Compiler
Compiler -> Producer: reverse BFS over slot.Sources
Compiler -> Producer: AccessAsync gate per edge (ICompileContext) → ancestor cone
Compiler -> Compiler: frontier = cone nodes with no in-cone predecessor
alt single frontier entry
    Compiler -> Compiler: forward compile restricted to cone (Cone set)
else multiple independent producers
    Compiler -> Compiler: compile each as a fan-out branch → ParallelSegment
    Compiler -> Compiler: funnel join (CommonNext) becomes the tail chain
end
Compiler -> Router: route table restricted to the cone branch (RestrictRouteToCone)
alt several router branches reach the cone
    Compiler --> Caller: throw InvalidOperationException (no result guessed)
else one branch
    Compiler --> Caller: CompiledGraph (BranchSegment kept, only cone branch compiled)
end
deactivate Compiler

== Run (track the target) ==
Caller -> Engine: RunAsync(graph, context { Target = target }, ct)
activate Engine
Engine -> Context: TargetReached = false
Engine -> Engine: drive segments (fan-out/join, chain, branch)
alt router selects the branch that reaches the target
    Engine -> Engine: DriveAsync(target) sets TargetReached = true; Data = target output
else router selects a sibling branch outside the cone
    Engine -> Engine: flow ends before target; TargetReached stays false
    Engine --> Caller: no fabricated value (Data null / absent)
end
Engine --> Caller: Status = Completed / Stopped
deactivate Engine
@enduml
```

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs` (`BuildAncestorConeAsync` lines 33-74, `CompileConeAsync` 82-134); `CompilerViewModel.cs` `RestrictRouteToCone` lines 286-308. Test evidence: `CompilerEx/CompileToReverseTests.cs` (`RouterOnConePath_SelectedBranchMatchesTarget_ReachesAndReturnsResult`, `RouterOnConePath_SelectedSiblingBranch_TargetNotReached_FlowEndsWithoutValue`, `FanOutJoin_TargetAfterJoin_CompilesConeFunnel_GroupDataAtJoin`).*

## 4. Redirect re-run — `RuntimeContext.Error()` → `IRedirectable` → whole-graph re-run

An in-node `Error()`/`Warn()` call or a `ReceiveAsync` exception is a redirect request. With `IRedirectable` the node returns a predecessor `Order`; `RunAsync` re-runs the whole graph toward that state — nodes with `Order < target` are skipped, so a redirect may skip forward across chains and resume later. The output registry is *not* cleared between passes; stale outputs are filtered by pass stamp and `ActiveRedirectTarget` so a join never aggregates results the re-run superseded.

```plantuml
@startuml
!theme plain
participant Caller
participant "RuntimeEngine" as Engine
participant "Node (IRedirectable)" as Node
participant "RuntimeContext" as Context
participant "IRedirectable" as Redirectable

== Drive node ==
Engine -> Node: DriveAsync → ReceiveAsync(context, ct)
alt node calls Error/Warn
    Node -> Context: Error/Warn(message); RedirectRequested = true
else exception thrown
    Context -> Context: [Error] log recorded; RedirectRequested = true
end

== Resolve redirect ==
alt node is IRedirectable
    Engine -> Redirectable: ResolveRedirectAsync(context, ct)
    activate Redirectable
    Redirectable --> Engine: target Order (must be < current Order)
    deactivate Redirectable
    alt target is a predecessor
        Engine -> Context: PendingRedirectTarget = target
        Engine -> Context: re-run whole graph (skip nodes Order < target; router target ⇒ re-route only)
        Engine -> Engine: CollectGroupedInputs keeps this pass ∪ contract-preserved prefix before target
    else invalid / not a predecessor
        Engine -> Engine: continue current pass (target ignored)
    end
else node is not IRedirectable
    Engine -> Context: CurrentOrder = -1; EndedWithError = true; Status = Stopped
end

alt redirects exceed 50 (MaxRedirects)
    Engine -> Context: Error("Redirected more than 50 times"); abort
    Engine --> Caller: throw InvalidOperationException
end
@enduml
```

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs` (`RunAsync` lines 19-68, `RunExecuteAsync` 106-160); `CompilerEx/Runtime/Model/RuntimeContext.cs` (`Error`/`Warn` lines 87-98, `RegisterOutput` 111-115, `CollectGroupedInputs` 127-140); `CompilerEx/Runtime/Contracts/IRedirectable.cs`. Test evidence: `CompilerEx/RuntimeRedirectTests.cs`.*

## 5. Broadcast dispatch — `StandardBroadcastAsync` (stateless / edge-level)

The model has three execution entries: ① a single-node task (`ReceiveCommand.Execute(ctx)` with an `ITaskContext`), ② edge-level broadcast, and ③ the chain-level compiled run. This diagram shows entry ②: `StandardBroadcastAsync` iterates the node's output-slot targets, builds a `TaskContext(parameter, sender, receiver)` per edge, applies the runtime `AccessAsync` gate — a rejected edge is treated as unconnected and skipped — and delivers each accepted edge via `ReceiveCommand.Execute(ctx)`. Entry ③ never uses this path: the compiled engine dispatches downstream itself and never triggers node commands.

```plantuml
@startuml
!theme plain
participant Caller
participant "Node (sender)" as Sender
participant "Helper" as Helper
participant "Receiver A" as RecvA
participant "Receiver B" as RecvB

Caller -> Sender: BroadcastCommand.Execute(payload)
activate Sender
Sender -> Sender: StandardBroadcastAsync(payload, ct)
Sender -> Helper: AccessAsync(TaskContext(payload, sender, receiver))
alt edge to B rejected by AccessAsync
    Helper --> Sender: false → edge skipped (treated as unconnected)
else edge to A accepted
    Helper --> Sender: true
    Sender -> RecvA: ReceiveCommand.Execute(ctx)   // ctx.Data = payload, ctx.Sender/Receiver set
    activate RecvA
    RecvA -> RecvA: node task runs (may chain result back)
    deactivate RecvA
end
Sender --> Caller: broadcast done
deactivate Sender
@enduml
```

*Source: `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs`, `StandardBroadcastAsync` lines 109-139 (reverse: `StandardReverseBroadcastAsync` lines 141-169, walking `Sources`). Test evidence: `CompilerEx/EntrySemanticsTests.cs` (`StandardBroadcast_DeliversTaskContextPerValidEdge_SkipsAccessRejectedEdge`, `CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`).*

Join aggregation (`IGroupData`) and serialization round-trip are analyzed on the [Complexity](../../04_complexity/00_workflow-system/index.md) and design-patterns pages.
