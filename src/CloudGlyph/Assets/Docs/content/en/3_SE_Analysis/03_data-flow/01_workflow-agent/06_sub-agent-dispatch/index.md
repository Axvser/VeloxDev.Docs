# Data Flow — Sub-Agent Dispatch (`SpawnSubAgent` → `WaitSubAgents`)

The sub-agent flow is one tool call that starts a background run and a second that collects it. What makes it worth tracing is that all the narrowing happens **synchronously inside the first tool body** — on the host's UI thread, before the child exists — while the child's own run goes to the thread pool. This page follows one spawn from the model's argument list to a settled roster row, and then the wait that reads it.

```plantuml
@startuml
participant "LLM" as Model
participant "SpawnSubAgent" as Tool
participant "SubAgentScope._parent\n(WorkflowAgentScope)" as Parent
participant "SkillScope / McpScope" as Sources
participant "new child scope" as Child
participant "thread pool" as Pool
participant "SubAgentScope roster" as Roster

Model -> Tool: SpawnSubAgent(task, allowedTools?, allowedSkills?,\nallowedMcpServers?, maxToolCalls?, …)
activate Tool
Tool -> Tool: blank task? -> {"status":"refused"} and no row is created
Tool -> Roster: TrySpawn(request, out refusal)
activate Roster

group depth & lifecycle gates
    Roster -> Roster: _disposed -> refuse "session has been disposed"
    Roster -> Roster: Depth >= MaxDepth -> refuse "the limit is N and this agent is at depth D"
end

group the allowance: a share of the parent's, never the whole of it
    Roster -> Parent: CreateToolkit().Ledger
    Roster -> Roster: remaining = min((MaxToolCalls ?? SpawnBudget) - ledger.Usage,\n                                 rootCap - rootUsage)
    Roster -> Roster: granted = min(requested ?? remaining, remaining - 1)
    alt granted < 1
        Roster --> Tool: refuse (no row created)
    else a request above the grant
        Roster -> Roster: dropped += "maxToolCalls: asked for X, granted Y"
    end
end

group the tool surface: two lists, one switch-off loop
    Roster -> Parent: CreateAllTools() names
    Roster -> Sources: SkillAgentToolkit.ToolNames (if Skills attached)\nSubAgentAgentToolkit.ToolNames (always)\nMcpScope.LoadedTools names (always)
    Roster -> Roster: everyName = distinct union
    Roster -> Roster: available = everyName.Where(parent.IsToolEnabled)
    alt request named its tools
        Roster -> Roster: grantedTools = available ∩ named, canonicalised\nrefusals -> dropped
    else omitted
        Roster -> Roster: grantedTools = available (inherit)
    end
    Roster -> Roster: grantedSkills = parent.Skills.GrantableNames ∩ named
    Roster -> Roster: grantedServers = parent.Mcp.GrantableNames ∩ named
    alt grantedSkills is empty and the parent has a skill source
        Roster -> Roster: strip the skill tools and say why in dropped
    end
end

group the child scope is configured while nothing runs yet
    Roster -> Child: parent.Tree.AsAgentScope()
    Roster -> Child: WithMaxToolCalls(granted), read/write caps clamped,\nWithAllowNodeExecution(opt-in on both sides),\nWithAutoMarkDirty(never beyond the parent)
    loop every name in everyName not granted (MCP names skipped)
        Roster -> Child: WithToolEnabled(name, false)
    end
    Roster -> Child: parent.GrantInteractionTo(child) — level, overrides, both handlers
    Roster -> Child: WithSkills(parentSkills.CreateNarrowed(grantedSkills))
    Roster -> Child: WithMcps(McpScope.CreateGrantedView(parentMcp, grantedServers, grantedTools))
    Roster -> Child: parent.GrantCustomToolsTo(child, grantedTools)
    Roster -> Child: ParentLedger = the parent's ledger\nWithSynchronizationContext(parent.UIContext)\nWithTranscript(new AgentTranscript())\nWithSubAgents(new subsystem at Depth + 1)  — unconditional
end

Roster -> Roster: create the row (grants, dropped list), Children.Add, Republish
Roster -> Pool: Task.Run(RunAsync)
Roster --> Tool: the new id
deactivate Roster
Tool --> Model: {"status":"ok","id":…,"maxToolCalls":…,"dropped":[…],"message":…}
deactivate Tool

note over Model, Pool
  Dispatch and poll, not call and wait: the child may still be on the wire when this reply is rendered.
end

== the child's own run ==

Pool -> Roster: StartAt then State = Running  (start before state)
Pool -> Pool: scopeFactory(childScope) -> AIAgent, then RunAsync(task, ct)
alt completed
    Pool -> Roster: Finish: payload FIRST (Result, Usage), State = Completed last
else OperationCanceledException
    Pool -> Roster: Finish: State = Cancelled — tokens stay null
else any other exception
    Pool -> Roster: Finish: Error, State = Failed — tokens stay null
end
Roster -> Roster: Republish -> Snapshot, Version++, Changed

== collecting it ==

Model -> Tool: WaitSubAgents(ids?, timeoutMs = 60000)
Tool -> Roster: WaitAsync(ids, timeout)
Roster -> Roster: Select: named ids (a handle this scope never issued is skipped), or every running child
alt there is something to wait for
    Roster -> Roster: WhenAll(runs) versus Task.Delay(timeout)
    note right
      Which one lost is decided by REFERENCE
      comparison: both tasks complete successfully.
    end note
else nothing matches
    Roster --> Tool: empty rows, timedOut = false — returns at once
end
Roster -> Roster: RefreshCallCounts -> Republish
Roster --> Tool: rows as they stand
Tool --> Model: {"status":"ok","timedOut":…,"agents":[…,"result" (cut at 4000), "dropped"…]}
@enduml
```

Notes:

- **Everything before `Task.Run` is serialized with every other spawn and with the panel**, because it happens on the roster's thread. Only the child's own run is handed off — which is what lets a spawn be treated like any other read-only tool call while the child works in parallel.
- **`SpawnSubAgent` is classified read-only** (`SubAgentAgentToolkit.ToolNames` joins the workflow toolkit's query list), so a spawn and a wait are charged to the read counter and never mark the tree dirty. `SubAgentBudgetTests.ASpawnIsAQuery_AndSoIsNotChargedToTheMutationBudget` asserts both directions, including that a spawn is refused when the *read* budget is spent and unaffected when the *mutation* budget is.
- **The spawn itself is one call against the shared pot**, which is why the grant is `remaining - 1` rather than `remaining`: the `- 1` keeps the descending-grant invariant true even if that accounting had not happened yet.
- **The child is charged to the tree from its very first call**, because `ParentLedger` is set before the toolkit exists. `SubAgentBudgetTests.AChildsCalls_AreCountedOnTheRootsLedger` asserts the root's usage is the spawn plus the child's call.
- **A refused spawn leaves no row.** The refusal is a JSON object and the model is expected to read `message`; nothing is half-created.
- **The child's own roster is empty at first** and is populated only if the child dispatches something itself; nothing here makes a sibling's handle reachable.

> Source: `SubAgentScope.cs` (`TrySpawn` 387-606, `RunAsync` 781-806, `Finish` 815-839, `WaitAsync` 891-906); `SubAgentAgentToolkit.cs` (the five tools, 85-229); `WorkflowAgentScope.cs` (`GrantInteractionTo` 283-296, `GrantCustomToolsTo` 251-268, `WithSubAgents` 1659-1673); `ToolCallLedger.cs`. Tests: `SubAgentDispatchTests`, `SubAgentBudgetTests`, `SubAgentHierarchyTests`, `SubAgentCapabilityGrantTests`.
