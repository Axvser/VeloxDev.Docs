# 数据流 — Root 链运行（`RunCompiledWorkflow`）

`RunCompiledWorkflow(startNodeIndex, seed)` 是链级执行入口——与 demo 的 Run 按钮同一条路径。它用 `CompileRole.Root` 编译从起始节点可达的子图，并让 `RuntimeEngine` 驱动整条链。它与 `ExecuteNode`（单节点经 `ReceiveCommand` 的节点级 EXEC）不同。

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

要点：

- 引擎拥有下游派发，因此编译步节点不会自动广播；分支选择在运行时经编译期路由器完成，结果与 GUI 运行同一张图一致。
- `GetNodeResult` 是孪生的 *Terminal* 入口，从其祖先锥计算单节点结果——参见 [Terminal 结果](../04_Terminal结果执行/index.md)。

> 源码：`WorkflowAgentToolkit.cs`，`RunCompiledWorkflow` 第 1789-1794 行及共享 `RunCompiledRoleAsync` 第 1804-1861 行；`WorkflowLifecycleFidelityTests` 覆盖门控与 terminal 运行契约。
