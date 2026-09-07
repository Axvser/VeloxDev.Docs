# Data Flow — Root Chain Run (`RunCompiledWorkflow`)

`RunCompiledWorkflow(startNodeIndex, seed)` is the chain-level execution entry — the same path the demo's Run button uses. It compiles the sub-graph reachable from a start node with `CompileRole.Root` and lets `RuntimeEngine` drive the whole chain. This is distinct from `ExecuteNode`, which executes one node via `ReceiveCommand` (node-level EXEC).

```plantuml
@startuml
participant "IAIAgent" as Agent
participant "RunCompiledWorkflow" as Tool
participant "WorkflowAgentScope" as Scope
participant "CompilerViewModel" as Compiler
participant "RuntimeEngine" as Engine
participant "RuntimeContext" as Ctx
participant "Compiled chain nodes (IRuntimeAware)" as Node

Agent -> Tool: RunCompiledWorkflow(startNodeIndex, seed)
activate Tool
Tool -> Scope: AllowNodeExecution gate check
alt disabled by host policy
    Tool --> Agent: {"status":"error","message":"... disabled by host policy ..."}
else allowed
    Tool -> Compiler: new CompilerViewModel().CompileAsync(node, CompileRole.Root)
    activate Compiler
    Compiler -> Compiler: compile reachable sub-graph -> CompiledGraph entries
    Compiler --> Tool: IReadOnlyList~CompiledGraph~ (graph[0] = root chain)
    deactivate Compiler
    alt graphs.Count == 0
        Tool --> Agent: {"status":"error","message":"Compile produced no graphs from this start node."}
    else
        Tool -> Ctx: RuntimeContext { Data = seed }  (no Target for Root)
        Tool -> Engine: new RuntimeEngine().RunAsync(graphs[0], context, ct)
        activate Engine
        Engine -> Node: inject IRuntimeContext session; drive chain in compiled order
        activate Node
        Node -> Node: ReceiveAsync in compiled-step mode (NO auto-broadcast; engine owns dispatch)
        Node -> Node: routers keep real selection (ICompileTimeRouter / redirects)
        Node --> Engine: step result / redirect
        deactivate Node
        Engine --> Tool: context.Status / EndedWithError / Attempt / Data / Logs
        deactivate Engine
        Tool --> Agent: {"status":"ok","role":"Root","runStatus":... ,"endedWithError":...,"attempts":...,"data":...,"logs":[...]}
    end
end
deactivate Tool
@enduml
```

Notes:

- Because the engine owns downstream dispatch, a compiled-step node does not auto-broadcast; branch selection happens at runtime through the compile-time router, keeping results identical to a GUI run of the same graph.
- `GetNodeResult` is the sibling *Terminal* entry that computes one node's result from its ancestor cone — see [Terminal result](../04_terminal-result-execution/index.md).

> Source: `WorkflowAgentToolkit.cs`, `RunCompiledWorkflow` lines 1789-1794 and shared `RunCompiledRoleAsync` lines 1804-1861; `WorkflowLifecycleFidelityTests` covers the gating and terminal run contract.
