# 工作流系统 — 会话：`RuntimeContext` 与 `GroupData`

宿主交给 `RuntimeEngine.RunAsync` 的具体会话对象，以及引擎在多输入节点装箱进 `Data` 的汇合载荷。

源码：`Runtime/Model/RuntimeContext.cs`、`Runtime/Model/GroupData.cs`。

---

## `RuntimeContext`

`public sealed partial class : IRuntimeContext`。`IsCompilePhase => false`，永远是：只有编译相位为真。构造即 `new RuntimeContext { Data = seed, Target = target, ExecutionGate = gate, ... }`。

它承载三组成员：共享会话上下文（`Uid` / `Sequence` / `Logs` / 黑板）、引擎维护的执行位置与决策状态（供 UI 绑定进度），以及本页末的宿主能力接缝。

### 共享上下文与执行位置

| 名称 | 类型 | 说明 |
|---|---|---|
| `Uid` | `Guid` | 会话身份；默认 `Guid.NewGuid()`。 |
| `Sequence` | `int` | 下一个序号；默认 `0`。 |
| `Logs` | `ObservableCollection<string>` | 保留的日志行。 |
| `CurrentEntry` | `CompileSegment?` | 当前执行的分段。 |
| `NodeIndex` | `int` | 当前节点在其链内的下标；默认 `-1`。 |
| `BranchKey` | `object?` | 当前分支键。 |
| `Attempt` | `int` | 过图趟数。 |
| `IsRunning` | `bool` | 是否有运行在进行。 |
| `Status` | `string` | 默认 `"Idle"`；引擎写 `Running` / `Paused` / `Completed` / `Stopped`。 |
| `CurrentOrder` | `int` | 当前执行节点的编译期 `Order`；默认 `-1`。 |
| `Data` | `object?` | 链式载荷（接口上那个可写的 `new Data`）。 |
| `Sender` / `Receiver` | `IWorkflowSlotViewModel?` | 槽位端点。编译运行下恒为 `null` —— 引擎驱动的是图而不是边。 |
| `IsCompilePhase` | `bool` | 恒为 `false`。 |

### 决策状态

| 名称 | 类型 | 说明 |
|---|---|---|
| `Target` | `IWorkflowNodeViewModel?` | 可选，本轮希望抵达的节点（结果/终端运行）。 |
| `TargetReached` | `bool` | 匹配的节点真被驱动时置位。 |
| `RedirectRequested` | `bool` | 本次驱动是否报过任何东西。getter 读的是 `ReportedLevel is not null`；赋 `true` 按最重的读法算，即错误。 |
| `EndedWithError` | `bool` | 流程提前结束，状态码 `-1`。 |
| `PendingRedirectTarget` | `int?` | 引擎请求的重定向目标 Order。 |
| `ActiveRedirectTarget` | `int?` | 本趟的重定向目标 Order；首趟为 `null`。 |
| `Outcome` | `RunOutcome` | 上一次运行如何收尾；在此之前是 `RunOutcome.Unknown`。 |

### 方法

| 成员 | 签名 | 说明 |
|---|---|---|
| `Next` | `int Next()` | 经 `Interlocked.Increment` 返回下一个序号。 |
| `Log` | `void Log(string entry)` | 追加 `"{NN}. {entry}"`。 |
| `Error` | `void Error(string message)` | 追加 `"{NN}. [Error] {message}"` 并把上报级别置为 `Error`。 |
| `Warn` | `void Warn(string message)` | 追加 `"{NN}. [Warning] {message}"` 并把上报级别置为 `Warning`。 |
| `ErrorAsync` | `Task ErrorAsync(string message)` | 先 `Error(message)`，再以 `ExecutionReportLevel.Error` 与 `CancellationToken.None` 等待已配置的 `ErrorSink`。 |
| `WarnAsync` | `Task WarnAsync(string message)` | 同上，级别 `ExecutionReportLevel.Warning`。 |
| `Set` / `TryGet` | `void Set(string key, object?)` / `bool TryGet(string key, out object?)` | 共享变量黑板，键比较不分大小写（`StringComparer.OrdinalIgnoreCase`）。写入时空/空白键被忽略。 |
| `RegisterOutput` | `void RegisterOutput(IWorkflowNodeViewModel node, object? value)` | 以节点引用身份为键存 `(Attempt, value)`。同时是「该节点本轮成功」的信号：它会被移到补偿列表末尾，而不是记两条。 |
| `ResetOutputs` | `void ResetOutputs()` | 清空产物登记表与已完成列表。每次 `RunAsync` 开头调用一次。 |
| `CollectGroupedInputs` | `IReadOnlyDictionary<IWorkflowNodeViewModel, object?> CollectGroupedInputs(IEnumerable<IWorkflowNodeViewModel> inputNodes)` | 构建汇合字典，按来源数量预分配。只保留**本趟**登记的产物，或 `ActiveRedirectTarget` 之前契约保留的前缀（`来源 Order < target`）。 |
| `SnapshotLogs` | `string[] SnapshotLogs()` | `Logs` 在某一时刻的拷贝，可在运行仍在追加时安全枚举。 |

#### `RuntimeContext.SnapshotLogs`

**签名：** `public string[] SnapshotLogs()`

**返回：** `string[]` —— 在会话日志锁下取得的 `Logs` 拷贝。

**异常：** 无。

**示例（测试）：**

```csharp
// CompilerEx/RuntimeContextLogConcurrencyTests.cs
var context = new RuntimeContext { MaxRetainedLogs = 16 };
// 一个写入任务在循环记日志，同时这个读取方在跑
_ = context.SnapshotLogs().Length;          // 绝不能抛
Assert.IsTrue(context.SnapshotLogs().Length <= 16);
```

**说明：** `ObservableCollection<T>` 不是线程安全的。没有这把锁时，读取方（`Enumerable.ToList`）会先读 `Count` 再 `CopyTo`，中间任何一次 `Add` / `RemoveAt` 都会让目标数组不够大 —— 抛 `ArgumentOutOfRangeException: Source array was not long enough ... (Parameter 'sourceArray')`。凡是不在运行自身线程上的调用，都要用 `SnapshotLogs()`；直接枚举活的 `Logs` 只在驱动线程上安全。

### 事件

#### `RuntimeContext.LogWriteFailed`

**签名：** `public event EventHandler<LogWriteFailedEventArgs>? LogWriteFailed;`

当已配置的 `LogWriter` 抛出时触发。该行仍会留在 `Logs` 里，运行照常继续 —— 诊断永远不改变运行做什么。`LogWriteFailedEventArgs` 暴露 `string Line`（写不进去的那一行）与 `Exception Error`（写入器抛出的东西）。

### 宿主能力属性

这些是 2026-09-27 的接缝。全部默认为「关」，全关时运行的表现与它们存在之前一模一样 —— 同样的日志行、同样的驱动次数。每一项的完整说明见`执行契约`与`检查点`。

| 名称 | 类型 | 默认 | 设置后的效果 |
|---|---|---|---|
| `ExecutionGate` | `IExecutionGate?` | `null` | 每个节点前等待一次；让宿主能握住一轮长运行。门关着时 `Status` 为 `"Paused"`，放开后回到 `"Running"`。 |
| `Observer` | `IExecutionObserver?` | `null` | 接收运行的每条时间线观察。 |
| `RetryPolicy` | `INodeRetryPolicy?` | `null` | 决定**抛出**异常的节点能不能再来一次。 |
| `ErrorSink` | `IExecutionErrorSink?` | `null` | 把每次失败作为记录收到，而不只是日志行。 |
| `Compensation` | `IExecutionCompensation?` | `null` | 得知失败/取消的运行已经驱动过哪些节点，最近的在前。 |
| `CheckpointStore` | `IExecutionCheckpointStore?` | `null` | 每个节点成功后把运行的位置写到哪里。 |
| `LogWriter` | `ILogWriter?` | `null` | 把运行的行导向内存 `Logs` 之外的地方。 |
| `MaxRetainedLogs` | `int?` | `null` | 限制 `Logs` 保留多少行（先丢最旧的）。`0` 表示一行不留，而 `LogWriter` 仍收到每一行。 |
| `MaxParallelBranches` | `int?` | `null` | 限制一次扇出同时有多少分支在飞。`null` = 不限；`1` = 整个组串行。 |

> **为什么它们不在 `IRuntimeContext` 上。** 给那个接口加成员会破坏每一个外部实现，而它们全是宿主的**策略**而非会话状态：`MaxParallelBranches` 与 `MaxRetainedLogs` 说的是宿主更愿意怎么做，那六个能力对象是它选择接入的接缝。引擎经私有的 `Session()` 转型到这个具体类去读，`Session()` 同时会拆开扇出分支的 `BranchRuntimeContext` —— 于是门与观察者在并行组**内部**仍然有效，而不是恰好在一张宽图最耗时间的地方静默失效。自带 `IRuntimeContext` 实现的宿主则直接得到不限流、无观察、2026-09-27 之前的行为。

---

## `IGroupData` / `GroupData`

| 类型 | 说明 |
|---|---|
| `public interface IGroupData : IReadOnlyDictionary<IWorkflowNodeViewModel, object?>` | 汇合契约。键 = 来源节点（引用身份），值 = 该节点本轮产物。消费方用 `context.Data is IGroupData g` 识别。 |
| `public readonly struct GroupData : IGroupData` | 引擎在驱动汇合点之前构造并装箱进 `IRuntimeContext.Data` 的结构体。索引器对未登记的来源抛 `KeyNotFoundException`；安全读法用 `TryGetValue`。 |

**示例（测试）：**

```csharp
// CompilerEx/RuntimeEngineRunTests.cs — JoinWithTwoUpstreams_ReceivesGroupDataKeyedBySourceNode
var group = (IGroupData)joinPayload;
Assert.AreEqual(2, group.Count);
Assert.IsTrue(group.TryGetValue(a, out var va) && Equals(va, "AV"));
Assert.IsTrue(group.TryGetValue(b, out var vb) && Equals(vb, "BV"));
```

**说明：** 只有当节点的编译身份登记了多于一个 `InputNodes` 时引擎才注入 `GroupData`；单输入节点保持裸的链式载荷。**Demo：** `PythonHelper.BuildInputPayload`（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/PythonHelper.cs`）在 `ctx.Data is IGroupData` 时把脚本载荷重建为 `{ 输入端口名: 来源产物 }`。
