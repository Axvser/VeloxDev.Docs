# Workflow System — Compile and Run (Root)

`CompileAsync(role: Root)` → `RuntimeEngine.RunAsync` → `ReceiveAsync`.

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
Compiler --> Caller: CompiledGraph (stored in Graphs, one row per segment in CompiledOutline)
deactivate Compiler

== Run (RuntimeEngine) ==
Caller -> Engine: RunAsync(graph, context, ct)   [resumeFrom defaults to null]
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
Engine -> Context: Outcome = Status == "Completed" ? Completed : (EndedWithError ? Failed : Cancelled)
Engine --> Caller: Status = EndedWithError ? "Stopped" : "Completed"
deactivate Engine
@enduml
```

Cancellation path: `ct.ThrowIfCancellationRequested()` aborts the pass; `OperationCanceledException` from a node is rethrown immediately (cancellation is **not** a redirect) and `RunAsync` sets `Status = "Stopped"` and records `RunOutcome.Cancelled` — with **no** `[Error]` log line, because a host stopping its own run is not a failure.

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs` (lines 26-57 entry, 59-249 decomposition, 414-447 `GetValidTargetsAsync`); `CompilerEx/Runtime/RuntimeEngine.cs` (`RunAsync` lines 52-128, `RunExecuteAsync` 166-247, `RunParallelAsync` 329-383, `DriveAsync` 412-506). Demo: `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`. Test evidence: `CompilerEx/RuntimeEngineRunTests.cs`, `CompilerEx/EntrySemanticsTests.cs`.*
