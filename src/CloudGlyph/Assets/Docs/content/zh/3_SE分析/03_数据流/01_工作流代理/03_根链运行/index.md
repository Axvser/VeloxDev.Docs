# 数据流 —— 根链运行（`RunCompiledWorkflow`）

`RunCompiledWorkflow(startNodeIndex, seed)` 是链级执行入口 —— 与示例 Run 按钮相同的路径。它用 `CompileRole.Root` 编译从起始节点可达的子图，并让 `RuntimeEngine` 驱动整条链。这与 `ExecuteNode` 不同，后者经 `ReceiveCommand` 执行单个节点（节点级 EXEC）。

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

说明：

- 因为引擎负责下游派发，编译步节点不自动广播；分支选择在运行时经编译期路由器发生，使结果与同一张图的 GUI 运行完全一致。
- `GetNodeResult` 是兄弟 *Terminal* 入口，从祖先锥计算单节点结果 —— 见[终结点结果](../04_终结点结果执行/index.md)。

> 源码：`WorkflowAgentToolkit.cs`（`RunCompiledWorkflow` 与共享的 `RunCompiledRoleAsync`）；`WorkflowLifecycleFidelityTests` 覆盖闸门与 terminal 运行契约。
