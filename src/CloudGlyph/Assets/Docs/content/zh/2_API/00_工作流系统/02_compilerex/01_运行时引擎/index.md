# 工作流系统 — 运行时引擎

`VeloxDev.Core.WorkflowSystem.CompilerEx` 的运行半边。`RuntimeEngine` 走一遍编译图，通过 `IWorkflowNodeViewModelHelper.ReceiveAsync` 驱动每个节点；会话契约 `IRuntimeContext` 把身份、日志、执行位置、黑板与产物登记表带过整轮运行。

源码：`Runtime/RuntimeEngine.cs`、`Runtime/Contracts/IRuntimeContext.cs`、`Runtime/Contracts/IRuntimeAware.cs`、`Runtime/Contracts/IRedirectable.cs`、`Runtime/Contracts/RunOutcome.cs`。

---

## `RuntimeEngine`

`public sealed class`，没有构造状态。引擎自己负责下游派发 —— 编译运行期间节点从不广播。每次运行新建一个（`new RuntimeEngine()`）。

#### `RuntimeEngine.RunAsync`

**签名：**

```csharp
Task RunAsync(
    CompiledGraph graph,
    IRuntimeContext context,
    CancellationToken ct,
    ExecutionCheckpoint? resumeFrom = null);
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `graph` | `CompiledGraph` | 要驱动的编译图。为 `null` 时立即返回。 |
| `context` | `IRuntimeContext` | 会话。为 `null` 时立即返回。 |
| `ct` | `CancellationToken` | 宿主令牌：取消会在下一个节点边界停下整轮。 |
| `resumeFrom` | `ExecutionCheckpoint?` | 可选，从哪份检查点继续；通常就是 `RuntimeContext.CheckpointStore` 里那份。它记录为已完成的节点不会再被驱动。 |

**返回：** `Task` —— 运行结束时完成。之后读 `Status`、`Outcome`、`Data`、`TargetReached`、`Attempt` 与 `Logs`。

**异常：**

| 异常 | 条件 |
|---|---|
| `InvalidOperationException` | `resumeFrom` 取自另一张图（`Shape` 不符）。在**碰会话之前**就拒绝 —— `Status` 停在 `"Idle"`，一个节点都不驱动。 |
| `InvalidOperationException` | 重定向超过 50 次（`MaxRedirects`）。抛出**之前**已把 `Status = "Stopped"`、`EndedWithError = true`、`CurrentOrder = -1` 写好。 |
| `OperationCanceledException` | 宿主的 `ct` 触发。被吸收成 `Status = "Stopped"`，不向调用方抛。 |

**示例（Demo）：**

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

// Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs（Run/Resume 驱动）
var graph = Compiler.Graphs.FirstOrDefault();
if (graph is null) return;

var context = new RuntimeContext { IsRunning = true, Data = SeedPayload };
ConfigureSessionWith(context);                       // 宿主策略钩子
ExecutionCheckpoint? place = resume ? await CheckpointSource(ct) : null;
await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);
```

**说明：** 重定向统一实现为「带目标 Order 重跑整张图」。`Order < 目标` 的节点是契约保留前缀，会被跳过；`Attempt` 数的是过图的趟数。

### 一轮运行内各分段的处理

| 分段 | 行为 |
|---|---|
| `ChainSegment` | 逐个驱动 `Nodes`。`Order <` 重定向目标、或检查点已记录为完成的节点被跳过。每次驱动前清 `RedirectRequested`，驱动后由它报了什么决定运行往哪走。 |
| `BranchSegment` | 先驱动路由器本身，再取键 —— `branch.IsDynamic ? ResolveRouteKey(context) : branch.CompileKey` —— 记到 `BranchKey`，然后驱动选中选项的子图。终结选项（或无匹配）返回「运行到此结束」。当重定向目标在路由器或其之后时（`target < routerOrder` 不成立），路由器**不**重驱动（只重选路），但**分支仍然进入**，所以落在分支内部的重定向会把目标及其之后的节点再驱动一遍。 |
| `ParallelSegment` | 扇出组。先恢复 `Data = sourceData`，让每条分支都从扇出源的产物出发；随后分支在调用方 `SynchronizationContext` 上作为交错异步操作**并发**运行。`MaxParallelBranches` 限制同时在飞的分支数。任意分支内命中终结分支即整轮结束；多条分支同时请求重定向时按分支顺序第一条胜出，其余记日志忽略。 |

### 逐节点驱动

对每个节点，引擎：等待 `ExecutionGate.WaitAsync`（只在门确实关着时才写 `Status = "Paused"`）；节点即 `Target` 时置 `TargetReached = true`；向 `IRuntimeAware` 节点注入会话；按编译身份写 `CurrentOrder`；记一行含节点类型名的日志；当身份携带多于一个 `InputNodes` 时，把 `Data` 换成 `GroupData(CollectGroupedInputs(inputs))`。然后调用 `Helper.ReceiveAsync(context, ct)`，登记产物，并写 `context.Data = result`。

重试策略就是在驱动循环里被询问的（**只**对抛出的异常），抛出的异常在这里变成 `ExecutionFailurePhase.Node` 错误记录，驱动成功也在这里保存检查点。`AttachRuntimeContext` 的注入发生在失败纪律**之内**，因此宿主实现抛异常会结束整轮，而不是静默跳过该节点。

---

## `IRuntimeContext : ITaskContext`

运行时会话契约。它从 `IAccessContext` 继承 `Data`、`Sender`、`Receiver`、`IsCompilePhase`，并把 `Data` 以带 setter 的形式重新声明。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Uid` | `Guid` | 本次运行会话的身份。 |
| `Sequence` | `int` | 下一个执行序号（自增）。 |
| `Logs` | `ObservableCollection<string>` | 日志行，每行前缀 `NN. `（序号、点、空格）。 |
| `CurrentEntry` | `CompileSegment?` | 当前正在执行的分段。 |
| `NodeIndex` | `int` | 当前节点在其链内的下标。 |
| `BranchKey` | `object?` | 当前分支键。 |
| `Attempt` | `int` | 过图趟数 = `1 + 重定向次数`。同时是产物登记表的趟戳。重试**不**推进它。 |
| `IsRunning` | `bool` | 是否有运行在进行。 |
| `Status` | `string` | `Idle` / `Running` / `Paused` / `Completed` / `Stopped`。 |
| `CurrentOrder` | `int` | 当前节点的编译期 `Order`；`-1` = 绝对停止。 |
| `Target` | `IWorkflowNodeViewModel?` | 可选，本轮希望抵达的节点（结果/终端运行会设）。 |
| `TargetReached` | `bool` | `Target` 是否真被驱动过。`false` = 其分支未被选中。 |
| `Data` | `object?`（可读**可写**） | 链式产物。引擎把每个节点的返回值写回，供下一节点读取。 |
| `RedirectRequested` | `bool` | 本次驱动是否报过任何东西。每次驱动前清空。 |
| `EndedWithError` | `bool` | 流程提前结束 —— 运行处于 `"Stopped"` 且状态码 `-1`。 |
| `PendingRedirectTarget` | `int?` | 引擎请求的重定向目标 `Order`；`RunAsync` 用它重跑整张图。 |
| `ActiveRedirectTarget` | `int?` | 本趟正在使用的目标 Order；首趟为 `null`。产物收集器靠它区分契约保留前缀与陈旧分支。 |
| `Log(string)` | `void` | 推一行普通日志。 |
| `Error(string)` | `void` | 推一行 `[Error]`，并**把本轮标记为需要重定向**。刻意同步且无返回值 —— 它跑在节点帧里，绝不能阻塞或抛出。 |
| `Warn(string)` | `void` | 推一行 `[Warning]`。是提醒不是停止：运行带着节点返回的值继续走。 |
| `ErrorAsync(string)` | `Task` | `Error` 加上宿主的记录：以 `ExecutionReportLevel.Error` 等待 `IExecutionErrorSink.OnErrorAsync`。 |
| `WarnAsync(string)` | `Task` | `Warn` 加上宿主的记录，级别 `ExecutionReportLevel.Warning`。 |
| `Set(string, object?)` | `void` | 写共享变量（键为空/空白时忽略）。 |
| `TryGet(string, out object?)` | `bool` | 读共享变量。 |
| `RegisterOutput(IWorkflowNodeViewModel, object?)` | `void` | 登记节点本趟产物，盖 `Attempt` 戳。 |
| `ResetOutputs()` | `void` | 清空产物登记表（每次 `RunAsync` 一次；重定向重跑**不**清）。 |
| `CollectGroupedInputs(IEnumerable<IWorkflowNodeViewModel>)` | `IReadOnlyDictionary<IWorkflowNodeViewModel, object?>` | 汇合点用的只读「来源 → 产物」字典。未登记的来源不在其中（`TryGetValue` 返回 `false`）。 |

> 2026-09-27 新增、但**不**在本接口上的成员 —— `MaxParallelBranches`、`MaxRetainedLogs`、`LogWriter`、`ExecutionGate`、`Observer`、`RetryPolicy`、`ErrorSink`、`Compensation`、`CheckpointStore`、`Outcome` —— 见 `运行时上下文`。把它们留在契约之外是刻意的决定，那里有解释。

---

## 节点侧的运行时契约

| 类型 | 签名 / 说明 |
|---|---|
| `IRuntimeAware` | `void AttachRuntimeContext(IRuntimeContext context)`。引擎在驱动节点之前把当前会话交给它，节点因此可以记录序号、写日志、读写共享变量。注入发生在驱动的失败纪律之内（见上）。 |
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)`。当某次驱动报错或抛出时被调用。返回的 Order 若是**前驱**（`target < 当前 Order`），引擎会朝它重跑整张图，可能跨链；`null`（或非法目标）让失败留在引擎原有的路径上。只有抛出的异常会进重试策略；`Error()`/`Warn()` 调用是节点自己要的控制流。 |

---

## `RunOutcome`

**签名：** `public enum RunOutcome { Unknown = 0, Completed, Cancelled, Failed }`

对 `Status` + `EndedWithError` 的精确读法，因为 `Status` 必须让一个 `"Stopped"` 同时承担失败与取消两种收尾。

| 成员 | 值 | 映射 |
|---|---|---|
| `Unknown` | 0 | 运行还没结束 —— 要么没跑过，要么还在跑。 |
| `Completed` | 1 | `Status == "Completed"` —— 每个条目都走完了。一条合法地提前结束整轮的分支（终结路由键）属于完成，不是失败。 |
| `Cancelled` | 2 | `Status == "Stopped"` 且 `EndedWithError == false` —— 宿主的令牌结束了它。 |
| `Failed` | 3 | `Status == "Stopped"` 且 `EndedWithError == true` —— 失败让流程提前结束。 |

**说明：** 刻意**没有** `Stopped` 成员 —— 每一条产出那个状态字符串的路径都落在下面两个成员之一，为它设一个成员将永远不可达。结局在引擎的 `finally` 里写进 `RuntimeContext.Outcome`；宿主自带的其它会话实现没有地方放它。

## 子页

| 页面 | 内容 |
|---|---|
| [会话：RuntimeContext 与 GroupData](00_运行时上下文/index.md) | 具体会话对象 `RuntimeContext` —— 全部成员，含宿主能力属性 —— 以及汇合载荷 `IGroupData` / `GroupData` |
