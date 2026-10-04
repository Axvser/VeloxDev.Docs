# Workflow System — Reverse / Terminal Cone Flow

`CompileAsync(role: Terminal)` → run with `Target`.

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
    Engine --> Caller: no fabricated value (Data stays null / absent)
end
Engine --> Caller: Status = Completed / Stopped
deactivate Engine
@enduml
```

**Verified behavior** (reproduced against the shipped library, three-node chain `Ticker → Bias → Printer`, targeting the middle node):

```text
[3] result: Completed data=tick->bias reached=True
```

The run stopped after `Bias` — `data` is the target's own output, **not** `tick->bias->print` — and because the node was actually driven, `TargetReached` is `true`.

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.Reverse.cs` (`BuildAncestorConeAsync` lines 33-74, `CompileConeAsync` 82-134); `CompilerViewModel.cs` `RestrictRouteToCone` lines 303-325. Test evidence: `CompilerEx/CompileToReverseTests.cs` (`RouterOnConePath_SelectedBranchMatchesTarget_ReachesAndReturnsResult`, `RouterOnConePath_SelectedSiblingBranch_TargetNotReached_FlowEndsWithoutValue`, `FanOutJoin_TargetAfterJoin_CompilesConeFunnel_GroupDataAtJoin`, `MultiLevelFanInAcrossIndependentEntries_ThrowsInformative`).*
