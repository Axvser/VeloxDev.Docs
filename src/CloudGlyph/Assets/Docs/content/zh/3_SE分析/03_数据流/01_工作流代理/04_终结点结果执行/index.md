# 数据流 —— 终结点结果（`GetNodeResult`）

`GetNodeResult(nodeIndex, seed)` 隔离计算单个节点的结果。它用 `CompileRole.Terminal` 反向编译节点的**祖先锥**（喂给它输入槽的上游生产者），并用运行时引擎驱动该锥，因此不需要 controller/起始节点。锥内的路由器保持真实分支语义：只编译通往目标的分支。

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

这正是内嵌提示规范（与 `RunCompiledRoleAsync`）执行的错误契约：若锥上的路由器选择了兄弟分支，目标**未**被到达，工具返回点名目标的 `status:error` —— 绝不把其他分支的最终载荷当作本节点的结果。要成功，先把路由器指向通往该节点的分支，或请求一个位于实际选中分支上的节点。

> 源码：`WorkflowAgentToolkit.cs`（`GetNodeResult` 与共享的 `RunCompiledRoleAsync`，`Target`/`TargetReached` 语义）；测试 `WorkflowLifecycleFidelityTests.GetNodeResult_*`。
