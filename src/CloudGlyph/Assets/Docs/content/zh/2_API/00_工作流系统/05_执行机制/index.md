# Workflow System — 执行机制（Compiler 与 非Compiler）

两条执行机制驱动**同一个**单一入口。**Compiler** 是引擎驱动：先对可达子图（或目标节点的祖先锥）做编译，再由 `RuntimeEngine` 沿图逐节点驱动。**非Compiler** 路径是节点驱动：每个节点执行后*自动广播*结果到下游，投递本身触发下一个节点。两者最终都落到同一个方法——节点只能靠**收到的 context 类型**区分自己走的是哪条路径。

> 本页是“数据究竟怎么流动”的指南。CompilerEx 类型参考见 `compilerex`；核心接口表见 `workflowsystem`；编译产物与运行语义见 `data-flow 数据流分析`。

---

## 1. 唯一入口：`ReceiveAsync`

所有路径——编译驱动、广播投递、手动 EXEC——都汇入同一个方法：

```csharp
Task<object?> IWorkflowNodeViewModelHelper.ReceiveAsync(ITaskContext context, CancellationToken ct)
```

`ReceiveCommand` 只是*人 / Agent* 的触发入口。其生成的处理程序把参数包成 context 后调用 `ReceiveAsync`（`NodeDefaultViewModel.cs` 的 `Receive` 命令）：

```csharp
[VeloxCommand]
private async Task<object?> Receive(object? parameter, CancellationToken ct)
{
    var ctx = parameter as ITaskContext ?? new TaskContext(parameter);
    return await Helper.ReceiveAsync(ctx, ct);
}
```

**Compiler 绕过 `ReceiveCommand`** —— `RuntimeEngine` 直接以 `IRuntimeContext` 会话调用 `Helper.ReceiveAsync(context, ct)`。所以到达 `ReceiveAsync` 共有**三种**方式：

| 路径 | 谁触发 | 如何到达 | 收到的 `context` |
|---|---|---|---|
| **编译驱动** | `RuntimeEngine.RunAsync` | **直接**调用 `Helper.ReceiveAsync(context, ct)`（无命令） | `IRuntimeContext` —— 运行时会话（本身是 `ITaskContext`） |
| **广播 RECV** | `StandardBroadcastAsync` | 每条边：`new TaskContext(data, sender, receiver)` → `receiverNode.ReceiveCommand.Execute(ctx)` → `ReceiveAsync` | `TaskContext`，`Sender`/`Receiver` 已填充 |
| **手动 EXEC** | `ReceiveCommand.Execute(data)` | 裸参数包成 `new TaskContext(data)` | `TaskContext`，`Sender`/`Receiver` = `null` |

节点从 context 判断自己所在路径——demo `EnumSelectorHelper`（路由节点）的做法：

```csharp
if (ctx is IRuntimeContext)
{
    Component.LastRouted = Component.SelectedValue is { } sv ? $"[{sv}]" : "[?]";
    return ctx.Data;          // 纯路由：原样透传，否则选中分支看到 null
}
```

demo `PythonHelper`（线性 / 汇合节点）则在编译运行中借会话写日志与错误：

```csharp
if (ctx is IRuntimeContext rc)
    rc.Log($"Python finished in {Component.LastRun}: {Truncate(raw, 200)}");
// 或出错请求重定向：rc.Error($"Python execution failed: {ex.Message}");
```

*源码：`Templates/ViewModels/NodeDefaultViewModel.cs`；`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/{EnumSelectorHelper,PythonHelper,TimerHelper}.cs`。*

---

## 2. 两种机制一览

| | **Compiler**（引擎驱动） | **非Compiler**（节点驱动、无状态） |
|---|---|---|
| **谁决定下一个节点** | 引擎沿预编译的 `CompiledGraph` 行走（`ChainSegment` / `BranchSegment` / `ParallelSegment`） | 每个节点自己的 `BroadcastAsync` 沿实时输出边（`LinksMap`）行走 |
| **是否预编译** | 是 —— `CompileAsync(node, role)` 一次性分解子图 / 祖先锥 | 否 —— 调用时刻的 `LinksMap` 拓扑 |
| **节点自动广播** | **关闭** —— 节点*不*自动转发；下游派发归引擎所有 | **开启** —— `ReceiveAsync` 返回后节点调用 `BroadcastAsync(flow, ct)` |
| **每节点的 context** | 共享的 `IRuntimeContext` 会话；引擎每驱动完一个节点写 `RegisterOutput` + `Data` 以链式传递 | 每条投递边一个全新的 `TaskContext` |
| **`AccessAsync` 门** | 仅编译期静态检测（`ICompileContext`，`Data = null`）把非法边从图中剪除 | 每条边投递前的运行期实时检测（`TaskContext`，`Data = 负载`） |
| **错误 / 重定向** | `IRedirectable` → 引擎从目标 `Order` **重跑整张图**（可跨链；目标为 Router 只重新路由）；否则状态 -1 结束 | 无重跑；出错仅结束本步 |
| **扇出 / 汇聚** | `ParallelSegment` + 汇合点 `IGroupData`（`RegisterOutput`/`CollectGroupedInputs` 聚合） | 纯广度优先扇出，无汇合聚合 |
| **目标可达性** | `RuntimeContext.Target` / `TargetReached`（`CompileRole.Terminal` 反向运行据此判定结果是否算出） | 无目标跟踪模型 |
| **适用场景** | 多输入汇合、路由、扇出、确定性的整链运行（demo 的 Run） | 手动单步 EXEC、简单线性馈送、GUI 逐步驱动 |

两条路径在线上共享**相同**的运行时 `AccessAsync` 语义，但 Compiler 把这道门移到编译期——图本身已排除被拒绝的边。

---

## 3. 参数 —— 每条路径携带什么

### 3.1 上下文继承体系

所有 context 都派生自一个携带负载的根：

```
IContext                       object? Data { get; }        // 运行期为真实数据，编译身份恒为 null
└─ IAccessContext              + bool IsCompilePhase, IWorkflowSlotViewModel? Sender, Receiver
   ├─ ITaskContext             // ReceiveCommand → ReceiveAsync 的入参契约（data/sender/receiver 均可空）
   │   └─ IRuntimeContext      // 运行时会话：Uid/Sequence/Logs/共享变量(Set/TryGet)/执行位置/CurrentOrder
   │                            //   new Data { set } 可写链式结果；Target/TargetReached
   │                            //   RegisterOutput/ResetOutputs/CollectGroupedInputs；Log/Error/Warn
   └─ ICompileContext          // 编译身份：Order/ChainIndex/Offset/InputNodes（Order = -1 = 绝对停止）
```

### 3.2 编译运行下 `Data` 的形态

编译运行中节点从 `context.Data` 读到的形态：

| 形态 | 何时出现 | 说明 |
|---|---|---|
| `null` | 无 seed，或上游返回 `null` | `RunAsync` 前的 seed 可选（调用方先写 `context.Data`） |
| **任意链式值** | 每个非汇合节点 | 引擎每驱动完一个 `ReceiveAsync` 写 `RegisterOutput` + `context.Data = result` —— 上游返回什么就是什么 |
| **`IGroupData`** | 多输入汇合（`CompileContext.InputNodes.Count > 1`） | 只读 `IReadOnlyDictionary<IWorkflowNodeViewModel, object?>`，Key = 来源节点引用身份；未运行的来源不存在（`TryGetValue` → false） |
| **扇出源负载恢复** | `ParallelSegment` | 引擎在每分支前设 `Data = sourceData`，所有分支读到*同一个*源输出 |
| *透传* | 纯路由节点（router） | 必须 `return ctx.Data` 原样，否则选中分支看到 `null` |

### 3.3 各路径的 `Data` / `Sender` / `Receiver`

| 路径 | `Data` | `Sender` / `Receiver` |
|---|---|---|
| 编译驱动 | seed / 链式值 / `IGroupData` / 恢复的扇出源负载 | **恒为 `null`**（引擎按图驱动，不走边） |
| 广播 RECV | 发送方广播的负载 | 该投递边的两端槽 |
| 手动 EXEC | 传给 `ReceiveCommand` 的裸参数 | `null` |

> 编译运行中的节点若检查 `context.Sender`/`context.Receiver` 恒看到 `null` —— 那里只有 `Data` 有意义。运行期 `AccessAsync` 门（带 Sender/Receiver）在编译运行中**不会触发**，只出现在非Compiler 的广播线上。

---

## 4. 时序 —— 谁驱动谁

### 4.1 Compiler 路径（引擎拥有整条链）

```
CompileAsync(node, CompileRole.Root)   // 或 CompileRole.Terminal 反向编译祖先锥
  └─ 遍历 → ChainSegment / BranchSegment / ParallelSegment（每条输出边编译期 AccessAsync 静态门）
RunAsync(graph, context, ct)           // RuntimeEngine
  └─ ResetOutputs() 一次；TargetReached = false；循环 pass（重定向时重跑整图）
       ChainSegment   → 逐节点：写 NodeIndex/CurrentOrder、注入 IRuntimeAware
                        InputNodes.Count > 1 → Data = new GroupData(CollectGroupedInputs(...))
                        ReceiveAsync(context, ct)   ← 会话即任务上下文
                        RegisterOutput(node, result); Data = result
                        节点报错(Error/Warn/异常) → IRedirectable? → PendingRedirectTarget → 重跑(跳 Order<target)
       BranchSegment  → 驱动 Router（除非“仅重新路由”）→ 选键（CompileKey | ResolveRouteKey(context)）
                        → 驱动选中子图；IsTerminal → 整轮结束
       ParallelSegment → 每分支前 Data = 源负载 → 并发驱动每个分支图
```

时序图见 `数据流分析`。

- 节点**不**广播；引擎取返回值驱动下一个节点。
- 节点调用 `Error()`/`Warn()` 或抛异常即请求重定向 → `IRedirectable` 从目标 Order 重跑（见 `策略-运行期`）；不实现 `IRedirectable` 则流程以状态 -1 结束。

### 4.2 非Compiler 路径（节点驱动的广播链式反应）

```
ReceiveCommand.Execute(seed)
  └─ TaskContext(seed, null, null)  →  node.ReceiveAsync  (EXEC)
        └─ 执行节点步骤（读取 context.Data）
        └─ AutoBroadcast → BroadcastAsync(result)   (StandardBroadcastAsync)
             └─ 对每条输出边：new TaskContext(data, sender, receiver)
                  ├─ AccessAsync(ctx) 运行期门 —— false → 该边按“未连接”跳过
                  └─ receiverNode.ReceiveCommand.Execute(ctx)
                        └─ receiver.ReceiveAsync  (RECV, Sender != null)
                              └─ 执行步骤 → AutoBroadcast → ...（链式反应）
```

时序是**节点驱动的深度优先链**：从一个节点起跑，每个节点向所有相连的下游扇出，各自再继续扇出。没有中央调度器、没有 `IGroupData` 聚合 —— 多输入节点只是每条入边各执行一次（每次 `ReceiveCommand` 一次）。

---

## 5. 每次驱动周围的能力管线

自 2026-09-27 起，引擎的逐节点驱动被七个可选宿主接缝包住。每一个都从**具体**的 `RuntimeContext` 上读（绝不从 `IRuntimeContext` 上读），每一个都经私有的 `Session()` 助手取用（因此在扇出内同样有效），每一个不设置时都精确复现 2026-09-27 之前的行为。它们运行的先后顺序就是契约：

```
询问 ExecutionGate.WaitAsync(ct)            → 关着 ⇒ Status = "Paused" 直到放开
   ↓
Observer.OnObservedAsync(NodeStarted)       → 抛异常的观察者只换来一行日志
   ↓
IRuntimeAware.AttachRuntimeContext(context)  → 在失败纪律之内：抛出即结束整轮
   ↓
InputNodes.Count > 1 时注入 GroupData
   ↓
Helper.ReceiveAsync(context, ct)
   ├─ 返回                      → RegisterOutput；Data = result；Observer(NodeSucceeded)
   │                              CheckpointStore.SaveAsync(Snapshot())
   └─ 抛出                     → Observer(NodeFailed)
                                 RetryPolicy.NextRetryAsync(NodeFailure)
                                   ├─ 有等待时长 ⇒ 记 [Retry n]；Observer(NodeRetried)；Task.Delay；从同一输入重驱动
                                   └─ null      ⇒ ErrorSink.OnErrorAsync(Node 相位)；RegisterOutput(node, null)；Data = null；重抛
   ↓
报了错且不是 IRedirectable                  → ErrorSink.OnErrorAsync(Node 相位)；CurrentOrder = -1；EndedWithError；Status = "Stopped"
报了错且是 IRedirectable                    → ResolveRedirectAsync（抛出 ⇒ ErrorSink 记 Redirect 相位，整轮结束）
只是警告                                    → 值照常传下去；不请求任何重定向
   ↓
RunEnded 观察；算出 RunOutcome；Compensation.CompensateAsync 按驱动逆序
   （仅在结局为 Failed 或 Cancelled 时）
```

| 接缝 | 在何时被询问 | 能否改变运行的数据 |
|---|---|---|
| `IExecutionGate` | 每个节点之前 | 不能 —— 它只是延后 |
| `IExecutionObserver` | 7 种观察，在各自的点上 | 不能 —— 抛出只换回一行日志 |
| `INodeRetryPolicy` | 只在**抛出的**异常之后 | 它只回答「何时」，不回答「什么」 |
| `IExecutionErrorSink` | 每条记录下来的失败 | 不能 —— 抛出被吞掉 |
| `IExecutionCompensation` | 结尾一次，且仅在 Failed/Cancelled 时 | 不能 —— 抛出记日志，其余照跑 |
| `IExecutionCheckpointStore` | 每次成功之后 | 不能 —— 抛出记日志，运行继续 |
| `ILogWriter` | `AppendLog` 内、保留检查之前 | 不能 —— 但仅因为该行同时留在 `Logs` 里；抛出在 `LogWriteFailed` 上上报 |

有两条规矩贯穿所有接缝：**引擎不为取消写任何日志行**（宿主停掉自己的运行不是失败，加一行 `[Error]` 会让以后读日志的人以为出过错），以及**一次上报绝不会让上报它的那次运行失败**。

> 这些路径的时序图见 `数据流 — 宿主能力` 与 `数据流 — 从检查点恢复`。

---

## 6. 该用哪种

- **Compiler** —— 任何需要确定性整链时序的运行：多输入汇合（`IGroupData`）、路由（`ICompileTimeRouter`）、共享源负载的扇出、重定向，以及“只求某个节点结果”的反向运行（`CompileRole.Terminal` + `RuntimeContext.Target`/`TargetReached`）。demo 的 Run 路径见 `ControllerViewModel`：`Compiler.CompileAsync(this, CompileRole.Root)` → `RuntimeEngine.RunAsync`。
- **非Compiler** —— 手动单步执行（`ReceiveCommand.Execute(data)`）、每个节点自动转发的简单线性馈送、GUI/AI 逐步驱动。它没有汇合与重定向模型。

两者**不互斥**：同一个工作流可以先手动单步搭（非Compiler），再把同一张图编译成链运行（Compiler）——都走同一个 `ReceiveAsync`，所以节点只需实现一个 `ReceiveAsync` 就能同时工作在两种机制下。

---

*Sources：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`、`Runtime/Model/RuntimeContext.cs`、`Runtime/Model/GroupData.cs`、`Compile/CompilerViewModel.cs`、`Compile/Model/*.cs`；`Src/Core/VeloxDev.Core/Interfaces/WorkflowSystem/IContext.cs`、`IAccessContext.cs`、`ITaskContext.cs`；`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/ViewModels/NodeDefaultViewModel.cs`；`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/{EnumSelectorHelper,PythonHelper,TimerHelper}.cs`。*
