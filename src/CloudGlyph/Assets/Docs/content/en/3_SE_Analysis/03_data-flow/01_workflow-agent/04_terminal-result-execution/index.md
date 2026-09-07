# Data Flow — Terminal Result (`GetNodeResult`)

`GetNodeResult(nodeIndex, seed)` computes a single node's result in isolation. It reverse-compiles the node's **ancestor cone** (the upstream producers feeding its input slots) with `CompileRole.Terminal` and drives that cone with the runtime engine, so no controller/start node is needed. Routers inside the cone keep real branch semantics: only the branch leading to the target is compiled.

```plantuml
@startuml
participant "IAIAgent" as Agent
participant "GetNodeResult" as Tool
participant "WorkflowAgentScope" as Scope
participant "CompilerViewModel" as Compiler
participant "RuntimeEngine" as Engine
participant "RuntimeContext" as Ctx
participant "Ancestor-cone node with router" as RouterNode
participant "Target node" as Target

Agent -> Tool: GetNodeResult(nodeIndex, seed)
activate Tool
Tool -> Scope: AllowNodeExecution gate check
alt disabled by host policy
    Tool --> Agent: {"status":"error","message":"... disabled by host policy ..."}
else allowed
    Tool -> Compiler: CompileAsync(node, CompileRole.Terminal)  -- reverse-compile ancestor cone
    activate Compiler
    Compiler -> Compiler: trace input slots backward; compile only branch that leads to target
    Compiler --> Tool: CompiledGraph (cone) or compile error (multi-route-key to same node)
    deactivate Compiler
    alt graphs.Count == 0
        Tool --> Agent: {"status":"error","message":"Compile produced no graph for this terminal node."}
    else
        Tool -> Ctx: RuntimeContext { Data = seed, Target = node }
        Tool -> Engine: new RuntimeEngine().RunAsync(graphs[0], context, ct)
        activate Engine
        Engine -> RouterNode: drive cone; router selects branch at runtime
        alt router selects the branch that leads to the target
            Engine -> Target: drive target -> context.TargetReached = true
            Engine --> Tool: context.Status/Data/Logs
            Tool --> Agent: {"status":"ok","role":"Terminal","runStatus":...,"targetReached":true,"data":...,"logs":[...]}
        else router selects a SIBLING branch (target not reached)
            Engine --> Tool: context.TargetReached = false
            note over Tool: NO fabricated value from the sibling branch
            Tool --> Agent: {"status":"error","message":"Target node 'X' (id ...) was NOT reached ... No result was produced."}
        end
        deactivate Engine
    end
end
deactivate Tool
@enduml
```

This is the exact error contract the embedded prompt spec (and `RunCompiledRoleAsync`) enforces: if a router on the cone selects a sibling branch, the target is **not** reached and the tool returns `status:error` naming the target — it never reports another branch's final payload as this node's result. To succeed, point the router at the branch that leads to the node first, or ask for a node on the actually-selected branch.

> Source: `WorkflowAgentToolkit.cs`, `GetNodeResult` lines 1796-1801 and shared `RunCompiledRoleAsync` lines 1804-1861 (forward-consistent `Target`/`TargetReached` semantics at lines 1827-1836); tests `WorkflowLifecycleFidelityTests.GetNodeResult_*`.
