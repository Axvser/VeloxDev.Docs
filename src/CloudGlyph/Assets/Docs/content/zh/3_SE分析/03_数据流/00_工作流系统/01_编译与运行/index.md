# 工作流系统 — 编译与运行（Root）

`CompileAsync(role: Root)` → `RuntimeEngine.RunAsync` → `ReceiveAsync`。

两个阶段。**编译**从控制器出发走过可达子图，构建不可变分段：线性段成为 `ChainSegment`，实现 `ICompileTimeRouter` 的节点成为 `BranchSegment`，多目标扇出成为 `ParallelSegment`。每条节点出边都用 `ICompileContext` 调用发送端 `AccessAsync` 做静态校验（被拒边视为未连接并略去）；每个可达节点通过 `ICompileTimeAware` 获得固定编译身份（`Order`/`ChainIndex`/`Offset`），多输入 join 点登记其输入源节点。**运行**驱动这些分段：引擎拥有下游派发，用 `IRuntimeContext` 直接调用 `Helper.ReceiveAsync`，把返回值写回 `context.Data`，并注册每个节点的输出。

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

取消路径：`ct.ThrowIfCancellationRequested()` 中止本趟；节点抛出的 `OperationCanceledException` 立即重抛（取消**不是**重定向），`RunAsync` 设置 `Status = "Stopped"` 并记录 `RunOutcome.Cancelled` —— **没有** `[Error]` 日志行，因为宿主停止自己的运行不是失败。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs`、`CompilerEx/Runtime/RuntimeEngine.cs`。Demo：`Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`。测试证据：`CompilerEx/RuntimeEngineRunTests.cs`、`CompilerEx/EntrySemanticsTests.cs`。*
