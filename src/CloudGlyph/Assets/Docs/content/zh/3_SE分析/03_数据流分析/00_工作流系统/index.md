# 数据流 — 工作流系统

八张 PlantUML 时序图追踪主要数据流。所有参与者均已声明，每个 `activate` 都有配对的 `deactivate`，`alt/else/end` 块已配平。执行模型是**两阶段**：编译期 `CompilerViewModel.CompileAsync` 固定身份并做静态校验（此时上下文 `IsCompilePhase = true`、`Data = null`）；运行期 `RuntimeEngine.RunAsync` 以 `IRuntimeContext` 会话驱动不可变段（`Data` 携带真实负载）。

## 1. 连接流 —— `SendConnection` → `ReceiveConnection` → `CreateLink`

连接分两阶段建立。`SendConnection(sender)` 检查发送端容量、清理同向连接冲突、显示 `VirtualLink` 并设 `PreviewSender`。`ReceiveConnection(receiver)` 校验容量 + `ValidateConnection` + 同节点判定，成功后经 `GetHelper().CreateLink(...)` 建连，并把整条连接作为一个可撤销的 `WorkflowActionPair` 提交。

```plantuml
@startuml
participant Caller
participant "IWorkflowTreeViewModel" as Tree
participant "Slot(sender)" as Sender
participant "Slot(receiver)" as Receiver
participant "IWorkflowLinkViewModel" as Link
participant "TreeCache(UndoStack)" as Cache

    == SendConnection ==
    Caller -> Tree: SendConnectionCommand.Execute(sender)
    activate Tree
    Tree -> Sender: StandardCanBeSender()
    alt not canBeSender
        Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
    else canBeSender
        Tree -> Tree: StandardSmartCleanupSenderConnections(sender)
        Tree -> Tree: VirtualLink.IsVisible = true
        Tree -> Sender: State = PreviewSender; UpdateState()
        Tree --> Caller: CurrentSender = sender
    end

    == ReceiveConnection ==
    Caller -> Tree: ReceiveConnectionCommand.Execute(receiver)
    alt CurrentSender == null
        Tree --> Caller: no-op
    else CurrentSender != null
        Tree -> Receiver: StandardCanBeReceiver()
        Tree -> Tree: ValidateConnection(CurrentSender, receiver)
        alt invalid（容量 / 校验 / 同节点）
            Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
        else valid
            Tree -> Tree: StandardCleanupSameDirectionConnections / StandardSmartCleanupReceiverConnections
            Tree -> Link: CreateLink(sender, receiver)
            activate Link
            Link --> Tree: new link（IsVisible = true）
            deactivate Link
            Tree -> Cache: StandardSubmit(new WorkflowActionPair(...))
            activate Cache
            Cache -> Cache: redo: LinksMap[s][r] = link; Links.Add; Targets/Sources.Add
            deactivate Cache
            Tree -> Tree: StandardResetVirtualLink(); CurrentSender = null
        end
    end
    deactivate Tree
@enduml
```

错误路径：任何校验失败（容量、自定义 `ValidateConnection`、同节点连接）都重置虚拟连接且不建立连接；已有同向连接通过提交的 `WorkflowActionPair` 原子替换。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`——`StandardSendConnection` 第 97-128 行、`StandardReceiveConnection` 第 130-171 行、`StandardCreateNewConnection`（private）第 375-428 行；`StandardCanBeSender/StandardCanBeReceiver` 在 `StandardEx/WorkflowSlotEx.cs` 第 179-189 行。*

## 2. 广播派发（无状态）—— `BroadcastCommand` → `BroadcastAsync` → 每边 `AccessAsync` 门

单节点任务与无状态广播都经命令层。`BroadcastCommand` 触发节点的广播处理器（`NodeDefaultViewModel.Broadcast`，第 121-125 行）→ `NodeHelper.BroadcastAsync` → `StandardBroadcastAsync`：先对每个输出槽的每条 `Targets` 边构造携带 `data/sender/receiver` 的 `TaskContext`，用**运行期** `AccessAsync`（`IsCompilePhase = false`、`Data` 有值）逐边过滤（被拒边视为未连接），再在第二遍对每个通过的接收者执行 `ReceiveCommand.Execute(ctx)`：

```plantuml
@startuml
participant Caller
participant "Node(BroadcastCommand)" as Node
participant "NodeHelper" as Helper
participant "IWorkflowNodeViewModelHelper\n(AccessAsync)" as Access
participant "Slot(receiver)\nReceiveCommand" as Cmd

    Caller -> Node: BroadcastCommand.Execute(parameter)
    activate Node
    Node -> Helper: BroadcastAsync(parameter, ct)
    activate Helper
    loop 每个 sender × Targets 边
        Helper -> Helper: ctx = new TaskContext(data, sender, receiver)
        Helper -> Access: AccessAsync(ctx, ct)
        activate Access
        Access --> Helper: true / false
        deactivate Access
        alt false（被拒 = 未连接）
            Helper -> Helper: 跳过该接收者
        end
    end
    loop 收集到的接收者
        Helper -> Cmd: ReceiveCommand.Execute(ctx)
        activate Cmd
        Cmd --> Helper: 节点执行（命令级）
        deactivate Cmd
    end
    Helper --> Node
    deactivate Helper
    deactivate Node
@enduml
```

反向广播对称（`ReverseBroadcastCommand` → `StandardReverseBroadcastAsync`，沿 `Sources` 派发，`WorkflowNodeEx.cs` 第 141-171 行）。选择器的无状态路径更窄：`EnumSelectorHelper` 只把数据投给**当前选中分支**对应槽位的下游（`SelectorBroadcast.ToSlotAsync`，每个接收者也过 owner 的 `AccessAsync` 门）。派发最终仍落在 `ReceiveCommand`，而编译运行不触发任何节点命令——引擎直接调 `Helper.ReceiveAsync`（见 §3）。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowNodeEx.cs`（`StandardBroadcastAsync` 第 109-139 行）。测试证据：`EntrySemanticsTests.StandardBroadcast_DeliversTaskContextPerValidEdge_SkipsAccessRejectedEdge`（第 40-71 行）、`CompiledRun_DrivesOnlyThroughHelper_NeverExecutesNodeCommands`（第 17-38 行）。*

## 3. 编译 + 运行（Root 正向）—— `CompileAsync(Root)` + `RuntimeEngine.RunAsync`

`CompilerViewModel.CompileAsync(node, CompileRole.Root)` 把 node 当作根/入口，沿 `Targets` 下游把可达子图分解为段（`ChainSegment`/`BranchSegment`/`ParallelSegment`）；每条输出边都经 `AccessAsync` 静态校验。`RuntimeEngine.RunAsync` 随后驱动各段，把每节点 `ReceiveAsync` 的返回值写回 `context.Data` 链式传给下游。

```plantuml
@startuml
participant Caller
participant "CompilerViewModel" as Compiler
participant "NodeHelper(AccessAsync)" as Access
participant "CompileContext" as CCtx

    == 编译（Role = Root） ==
    Caller -> Compiler: CompileAsync(node, CompileRole.Root)
    activate Compiler
    Compiler -> Compiler: 沿 Slots→Targets 行走（visited 守卫 / 多输入边界）
    loop 每条输出边
        Compiler -> CCtx: new CompileContext { Order=游标, Sender, Receiver }
        Compiler -> Access: AccessAsync(compileCtx, ct)（IsCompilePhase=true, Data=null）
        activate Access
        Access --> Compiler: true / false
        deactivate Access
        alt false（静态被拒 = 未连接）
            Compiler -> Compiler: 该边不入编译图
        end
    end
    Compiler -> Compiler: 线性段→ChainSegment；ICompileTimeRouter→BranchSegment（Static 剪枝标记 Order=-1）
    Compiler -> Compiler: 多目标扇出→ParallelSegment；汇合点登记 JoinInputs
    Compiler -> CCtx: 为 ICompileTimeAware 注入固定身份（Order/ChainIndex/Offset/InputNodes）
    Compiler --> Caller: IReadOnlyList<CompiledGraph>
    deactivate Compiler
@enduml
```

```plantuml
@startuml
participant Caller
participant "RuntimeEngine" as Engine
participant "CompiledGraph" as Graph
participant "IRuntimeContext" as Ctx
participant "NodeHelper\n(ReceiveAsync)" as Helper
participant "GroupData" as Group

    Caller -> Engine: RunAsync(graph, context, ct)
    activate Engine
    Engine -> Ctx: IsRunning=true; Status="Running"; ResetOutputs()
    loop 每次整图 pass（Attempt++）
        Engine -> Graph: 遍历 Entries
        alt ChainSegment（线性段）
            loop 段内每个节点
                Engine -> Engine: Order < 重定向目标 → 跳过（跨链）
                Engine -> Ctx: RedirectRequested=false
                Engine -> Ctx: IRuntimeAware 注入 AttachRuntimeContext；CurrentOrder = cc.Order
                Engine -> Ctx: Target 命中 → TargetReached = true
                alt InputNodes.Count > 1（汇合点）
                    Engine -> Group: Data = GroupData(CollectGroupedInputs(inputs))
                end
                Engine -> Helper: ReceiveAsync(context, ct)
                activate Helper
                Helper -> Ctx: 读写共享变量 / 记日志 / 返回结果
                Helper --> Engine: result
                deactivate Helper
                Engine -> Ctx: RegisterOutput(node, result); Data = result
                alt 节点 Error/Warn 或抛异常
                    Engine -> Engine: RedirectRequested=true（见 §5）
                end
            end
        else BranchSegment（路由）
            Engine -> Engine: key = IsDynamic ? ResolveRouteKey(ctx) : CompileKey
            Engine -> Engine: 无下游/终点分支 → 运行结束（终止）
        else ParallelSegment（扇出）
            Engine -> Ctx: Data = 扇出源负载（每条分支前恢复）
            Engine -> Engine: 顺序驱动各分支子图（共享黑板非线程安全）
        end
    end
    Engine --> Caller: Status = "Completed" / "Stopped"
    deactivate Engine
@enduml
```

编译图是**不可变**的可能执行集合描述（`CompiledGraph` 文档第 6-10 行），真实路径由运行期状态决定。取消：`ct.ThrowIfCancellationRequested()` 中止链；节点抛 `OperationCanceledException` 立即重抛（取消不是重定向）。

*源码：`CompilerEx/Compile/CompilerViewModel.cs`（第 37-57 行统一入口、第 59-232 行 `CompileGraphAsync`、第 397-430 行 `GetValidTargetsAsync` 逐边 `AccessAsync`）、`CompilerEx/Runtime/RuntimeEngine.cs`（第 19-68 行 `RunAsync`、第 71-97 行 `RunGraphAsync`、第 106-160 行 `RunExecuteAsync`、第 205-214 行扇出恢复、第 227-261 行 `DriveAsync`）。测试证据：`RuntimeEngineRunTests.LinearChain_DrivesEachNodeOnceInOrder_DataFlowsThroughSession`、`FanOutParallel_RestoresSourcePayload_BeforeEachBranch`、`JoinWithTwoUpstreams_ReceivesGroupDataKeyedBySourceNode`、`CompileDecompositionTests.InvalidOutputEdge_AccessFalse_IsPrunedFromGraph_DegradesToSinglePath`、`StaticRouter_SelectionALocksCompileKey_UnselectedBranchDownstreamGetsMinusOne`。*

## 4. 反向 / Terminal 锥编译与运行 —— `CompileAsync(node, CompileRole.Terminal)`

以节点为*结果终点*，无需显式起点：编译器沿 `Sources` 反向 BFS 收集其**祖先锥**（每条反向边也过 owner 的 `AccessAsync` 门，与正向同一“被拒即未连接”规则），锥内无入边者构成入口前沿；Router 保留真实分支语义，只编译通往锥内的分支，扇入的多个独立产源汇合到共同的漏斗汇合点后继续：

```plantuml
@startuml
participant Caller
participant "CompilerViewModel" as Compiler
participant "RuntimeEngine" as Engine
participant "IRuntimeContext" as Ctx
participant "Target node" as Target

    == 编译（Role = Terminal） ==
    Caller -> Compiler: CompileAsync(target, CompileRole.Terminal)
    activate Compiler
    Compiler -> Compiler: BuildAncestorConeAsync：反向 BFS over Sources + AccessAsync 门
    Compiler -> Compiler: 入口前沿 = 锥内无入边节点
    alt 单个入口
        Compiler -> Compiler: 从入口正向编译（Router 只保留指向锥内的分支）
    else 多个独立产源
        Compiler -> Compiler: 各自编译 + 共同漏斗汇合点续链
        alt 不汇合于单一 join
            Compiler --> Caller: 抛 InvalidOperationException（不编造结果）
        end
    end
    Compiler --> Caller: CompiledGraph
    deactivate Compiler

    == 运行 ==
    Caller -> Engine: RunAsync(graph, context{ Target=target }, ct)
    activate Engine
    Engine -> Ctx: TargetReached = false
    Engine -> Engine: 逐段驱动
    alt 实际驱动到 target 节点
        Engine -> Ctx: TargetReached = true
    else router 在运行期选择了锥外兄弟支
        Engine -> Ctx: 流程在 target 之前结束（NOT reached）
    end
    Engine --> Caller: 不编造值；由调用方读 TargetReached
    deactivate Engine
@enduml
```

约束：若某 Router 有**多条**不同 key 分支都能抵达终点，则“单次正向运行只能走一支”，该锥被拒绝而非猜测（`RestrictRouteToCone` 抛 `InvalidOperationException`）；若多个独立产源不汇合到单一共同 join，同样拒绝（series-parallel 锥之外不可表达）。汇合处 `InputNodes.Count > 1` 时运行期注入 `IGroupData`，与正向语义一致。

*源码：`CompilerEx/Compile/CompilerViewModel.Reverse.cs`（`BuildAncestorConeAsync` 第 33-74 行、`CompileConeAsync` 第 82-134 行）、`CompilerEx/Compile/CompilerViewModel.cs`（`RestrictRouteToCone` 第 286-308 行）、`CompilerEx/Compile/CompileRole.cs`。测试证据：`CompileToReverseTests`——`LinearChain_TargetMidCone_CompilesFromOwnEntry_MatchesForwardRun`、`RouterOnConePath_SelectedSiblingBranch_TargetNotReached_FlowEndsWithoutValue`、`FanOutJoin_TargetAfterJoin_CompilesConeFunnel_GroupDataAtJoin`、`NoStartNodeProvided_EntryFrontierIsDerivedFromTheCone`、`MultiLevelFanInAcrossIndependentEntries_ThrowsInformative`。*

## 5. 错误 / 重定向 —— `Error()`/`Warn()` → `IRedirectable` 整图重跑

`ReceiveAsync` 内调用 `Error()/Warn()` 或抛异常即请求重定向。若节点实现 `IRedirectable`，引擎按其返回的前驱 `Order`（`Order < 当前`）重跑整图——目标之前的节点（可跨链）跳过不驱动，属**契约保留前缀**；目标若是 Router 自身则只重新路由、不重算。未实现 `IRedirectable` 时流程以 `-1` 结束：

```plantuml
@startuml
participant "RuntimeEngine" as Engine
participant "IWorkflowNodeViewModel" as Node
participant "IRuntimeContext" as Ctx
participant "IRedirectable" as Redirectable

    == 驱动节点 ==
    Engine -> Node: ReceiveAsync(context, ct)
    activate Node
    Node -> Ctx: Error(message) / Warn(message)
    Ctx -> Ctx: RedirectRequested = true
    Node --> Engine: 返回或抛异常（记录后按重定向处理）
    deactivate Node

    == 解析重定向 ==
    alt node is IRedirectable
        Engine -> Redirectable: ResolveRedirectAsync(context, ct)
        activate Redirectable
        Redirectable --> Engine: 前驱 target Order (int?) / null
        deactivate Redirectable
        alt targetOrder < 当前 Order（合法前驱）
            Engine -> Ctx: PendingRedirectTarget = targetOrder
            Engine -> Engine: 重跑整图（跳过 Order < target；重定向上限 50 次）
            Engine -> Engine: 每 pass 重写 Attempt / ActiveRedirectTarget；陈旧产物按 pass 戳过滤
        else null / 非前驱
            Engine -> Engine: 忽略该 target，继续当前链
        end
    else node is not IRedirectable
        Engine -> Ctx: CurrentOrder = -1; EndedWithError = true
        Engine -> Engine: 流程结束，Status = "Stopped"
    end
@enduml
```

回退超过 50 次（`MaxRedirects`）抛 `InvalidOperationException` 放弃。重定向是纯运行期契约——编译图本身无环。

*源码：`CompilerEx/Runtime/RuntimeEngine.cs`（第 19-68 行 `RunAsync`、第 136-158 行 `RunExecuteAsync` 重定向分支）、`CompilerEx/Runtime/Contracts/IRedirectable.cs`、`CompilerEx/Runtime/Model/RuntimeContext.cs`（`CollectGroupedInputs` 第 127-151 行 pass 戳过滤）。测试证据：`RuntimeRedirectTests.RedirectToPredecessor_SkipsPrefixOnRerun_CountsNodesPerPass`、`RedirectTargetNotAPredecessor_IsIgnored_FlowCompletesSinglePass`、`RedirectToRouter_ReroutesOnly_WithoutRecomputingRouter`、`RedirectLoopsExceedingLimit_AbortWithException`。*

## 6. 撤销 / 重做

每个变更操作以 `WorkflowActionPair(redo, undo)` 压入撤销栈（`redo` 立即执行）。`UndoCommand` 弹栈运行 `Undo` 后压入重做栈；`RedoCommand` 相反。

```plantuml
@startuml
participant Caller
participant "IWorkflowTreeViewModel" as Tree
participant "TreeCache(Undo/RedoStack)" as Cache
participant "WorkflowActionPair" as Pair

    == Undo ==
    Caller -> Tree: UndoCommand.Execute(null)
    activate Tree
    Tree -> Cache: StandardUndo()
    activate Cache
    Cache -> Cache: UndoStack.TryPop(out pair)
    alt pair found
        Cache -> Pair: pair.Undo.Invoke()
        Cache -> Cache: RedoStack.Push(pair)
    else 栈空
        Tree --> Caller: no-op
    end
    deactivate Cache
    deactivate Tree

    == Redo ==
    Caller -> Tree: RedoCommand.Execute(null)
    activate Tree
    Tree -> Cache: StandardRedo()
    activate Cache
    Cache -> Cache: RedoStack.TryPop(out pair)
    alt pair found
        Cache -> Pair: pair.Redo.Invoke()
        Cache -> Cache: UndoStack.Push(pair)
    else 栈空
        Tree --> Caller: no-op
    end
    deactivate Cache
    deactivate Tree
@enduml
```

错误路径：`pair.Redo/Undo.Invoke()` 抛异常时 `StandardSubmit/StandardUndo/StandardRedo` 捕获并经 `Debug.WriteLine` 记录——栈保持不变。`StandardRemoveConnections` 等批处理把许多微操作聚合进单个操作对，栈深与逻辑用户操作数成正比。

*源码：`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`——`StandardSubmit` 第 210-222 行、`StandardUndo` 第 224-239 行、`StandardRedo` 第 193-208 行、`TreeCache` 第 655-660 行、`StandardRemoveConnections`（private）第 430-528 行。*

## 7. 序列化（`ComponentModelEx.Serialize` / `Deserialize`）

`ComponentModelEx` 用 Newtonsoft 以 `PreserveReferencesHandling.Objects` 与只写属性解析器把整图序列化为 JSON；反序列化重建图，并从序列化的 `SelectorTypeName` 重新解析 `SlotEnumerator.SelectorType`。调用方随后用 `Layout.UpdateCommand` 重新应用布局：

```plantuml
@startuml
participant Caller
participant "IWorkflowTreeViewModel" as Tree
participant "ComponentModelEx(Newtonsoft)" as Serializer
participant "CanvasLayout" as Layout

    == Serialize ==
    Caller -> Serializer: tree.Serialize()
    activate Serializer
    Serializer -> Tree: 读 Nodes / Slots / Links / Layout / VeloxProperty 数据
    Serializer -> Serializer: JsonConvert.SerializeObject (PreserveReferences, WritablePropertiesOnlyResolver)
    Serializer --> Caller: JSON string
    deactivate Serializer

    == Deserialize ==
    Caller -> Serializer: json.Deserialize<TreeViewModel>()
    activate Serializer
    Serializer -> Serializer: JsonConvert.DeserializeObject<T> (TypeNameHandling.Auto, PreserveReferences)
    Serializer -> Tree: 重建节点/槽/连接；从 SelectorTypeName 重解析 SelectorType
    Serializer --> Caller: restored tree
    deactivate Serializer

    == 重放布局 ==
    Caller -> Layout: copy.Layout.UpdateCommand.Execute(null)
    activate Layout
    Layout -> Layout: 由 OriginSize + offsets 重算 ActualSize / ActualOffset
    deactivate Layout
@enduml
```

错误路径：`TryDeserialize` 对 null / 空 / 畸形输入返回 `false` 而不抛；`Deserialize` 结果为空时抛 `JsonSerializationException`。

*源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`。测试证据：`WorkflowSerializationTests`（`Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowSerializationTests.cs`）。*
