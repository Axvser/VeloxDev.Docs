# Workflow System — Parallel Fan-Out and Its Concurrency Cap

A `ParallelSegment` runs its branches **concurrently**, as interleaved async operations rather than threads, with `MaxParallelBranches` bounding how many may be in flight at once.

Every branch gets its own `BranchRuntimeContext`, so payload, redirect request and log buffer are per branch while identity, progress, the output registry and the shared variables stay on the host's single session. Each branch starts from the **fan-out source's** payload and can never see a sibling's output. Logs are **forwarded**, not buffered, so the lines read in the order they actually happened.

```plantuml
@startuml
!theme plain
participant "RuntimeEngine" as Engine
participant "Session (RuntimeContext)" as Session
participant "SemaphoreSlim (MaxParallelBranches)" as Cap
participant "Branch A facade" as BA
participant "Branch B facade" as BB
participant "Node A" as NA
participant "Node B" as NB

== Enter the fan-out group ==
Engine -> Session: sourceData = Data
Engine -> Session: limit = MaxParallelBranches      (cast to RuntimeContext; null = uncapped)
Engine -> Cap: new SemaphoreSlim(limit, limit)  [only when limit > 0]
note right of Engine: branches.Count == 1 keeps the plain path — nothing to interleave

== Start both branches (they interleave, they do not run on two threads) ==
Engine -> BA: new BranchRuntimeContext(session) { Data = sourceData }
Engine -> BB: new BranchRuntimeContext(session) { Data = sourceData }
par branch 0
    Engine -> Cap: WaitAsync(ct)
    Cap --> Engine: acquired
    Engine -> Session: Observer(BranchStarted, "branch 0")
    Engine -> NA: ReceiveAsync(branchContext, ct)
    activate NA
    NA -> BA: read Data (the fan-out source payload)
    NA --> Engine: result
    deactivate NA
    Engine -> BA: RegisterOutput -> forwarded to Session
    Engine -> Cap: Release()
else branch 1
    Engine -> Cap: WaitAsync(ct)
    alt cap is 1 and branch 0 still holds it
        Cap --> Engine: branch 1 waits here — no overlap
    else cap is null or > 1
        Cap --> Engine: acquired immediately — branches overlap
    end
    Engine -> Session: Observer(BranchStarted, "branch 1")
    Engine -> NB: ReceiveAsync(branchContext, ct)
    activate NB
    NB -> BB: read Data (the SAME source payload, never branch 0's output)
    NB --> Engine: result
    deactivate NB
    Engine -> Cap: Release()
end

== Merge the group ==
Engine -> Engine: winner = first branch (in branch order) with a PendingRedirectTarget
Engine -> Session: ignored losers are logged
Engine -> Session: Data = last branch's Data   (what the sequential loop used to leave behind)
Engine --> Engine: any terminal branch hit ⇒ the whole run ends
@enduml
```

**Determinism, in branch order.** When several branches ask to redirect, the **first in branch order** wins while the rest are logged and ignored — first by *order*, not by wall clock, so a run stays reproducible. The payload left in the session is the last branch's. A terminal branch hit inside any branch ends the whole run. One deliberate change from the earlier sequential engine: a branch that throws no longer aborts its siblings mid-flight — the exception surfaces once the group has finished.

**Verified behavior** (reproduced against the shipped library; two 120 ms branches):

```text
[11] segments: ChainSegment, ParallelSegment
[11] MaxParallelBranches=null: overlap=True
[11] MaxParallelBranches=1:    overlap=False
```

With no cap both branches were in flight at the same time (total wall time ≈ one branch, not two); with `MaxParallelBranches = 1` the second branch's start fell after the first branch's end.

No demo sets `MaxParallelBranches`; the contract is pinned by `ParallelExecutionTests` (`Branches_AreInFlightAtTheSameTime`, `MaxParallelBranches_SerialisesTheGroupWhenSetToOne`, `EachBranch_SeesOnlyTheFanOutSourcePayload`, `LogLines_KeepTheOrderTheyHappened`, `TwoBranchesAskingToRedirect_TheFirstInBranchOrderWins_AndTheOtherIsLogged`).

*Sources: `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs` — `RunParallelAsync` lines 329-383, `RunOneBranchAsync` 389-403; `CompilerEx/Runtime/Model/BranchRuntimeContext.cs`.*
