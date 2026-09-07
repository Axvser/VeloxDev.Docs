# 数据流 — Terminal 结果（`GetNodeResult`）

`GetNodeResult(nodeIndex, seed)` 隔离地计算单个节点的结果。它以 `CompileRole.Terminal` 反向编译该节点的**祖先锥**（从其输入槽反向追溯的、喂给它数据的所有上游生产者），再用运行时引擎驱动该锥，因此无需控制器/起始节点。锥内路由器保持真实分支语义：只编译通向目标的那条分支。

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

这正是内嵌提示规范（与 `RunCompiledRoleAsync`）强制执行的错误契约：若锥上某路由器选中兄弟分支，目标**未**到达，工具返回点名目标的 `status:error`——绝不把另一分支的最终数据当作本节点结果上报。要成功，先把路由器指向通向本节点的分支，或改问实际选中分支上的节点。

> 源码：`WorkflowAgentToolkit.cs`，`GetNodeResult` 第 1796-1801 行及共享 `RunCompiledRoleAsync` 第 1804-1861 行（第 1827-1836 行的前向一致 `Target`/`TargetReached` 语义）；测试 `WorkflowLifecycleFidelityTests.GetNodeResult_*`。
