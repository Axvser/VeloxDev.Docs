# 运行时会话

会话既是引擎写入的 `IRuntimeContext`，也是每个节点收到的 `ITaskContext`。`RuntimeContext` 是具体默认实现；可选能力放在它身上而不放在接口上，这样增加它们不会破坏外部实现。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## IRuntimeContext

**签名：** `interface IRuntimeContext : ITaskContext`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Uid` | `Guid` | 唯一运行会话标识。 |
| `Sequence` | `int` | 下一个日志序号。 |
| `Logs` | `ObservableCollection<string>` | 已格式化日志行。 |
| `CurrentEntry` | `CompileSegment?` | 当前执行的段。 |
| `NodeIndex` | `int` | 当前节点在链内索引。 |
| `BranchKey` | `object?` | 当前分支键。 |
| `Attempt` | `int` | 过图趟数；重定向加一，重试不加。 |
| `IsRunning` | `bool` | 是否正在运行。 |
| `Status` | `string` | `Idle`、`Running`、`Paused`、`Completed` 或 `Stopped`。 |
| `CurrentOrder` | `int` | 当前节点的编译固定顺序；停止时为 `-1`。 |
| `Target` | `INodeComponent?` | 调用方希望到达的节点。 |
| `TargetReached` | `bool` | `Target` 实际被驱动后置位。 |
| `Data` | `object?` | 链式载荷；接口在 `IContext.Data` 之上增加了 setter。 |
| `RedirectRequested` | `bool` | 本次驱动是否报告了任何问题。 |
| `EndedWithError` | `bool` | 流程是否因失败提前结束。 |
| `PendingRedirectTarget` | `int?` | 引擎请求的重定向目标顺序。 |
| `ActiveRedirectTarget` | `int?` | 本趟的重跑目标顺序。 |
| `Log(string entry)` | `void` | 写入普通行。 |
| `Error(string message)` | `void` | 写 `[Error]` 并标记运行停止/重定向。 |
| `Warn(string message)` | `void` | 写 `[Warning]`；运行带值继续。 |
| `ErrorAsync(string message)` / `WarnAsync(string message)` | `Task` | 行，加上宿主的 `IExecutionErrorSink` 记录。 |
| `Set(string key, object? value)` / `TryGet(string key, out object? value)` | `void` / `bool` | 共享变量（键不区分大小写）。 |
| `RegisterOutput(INodeComponent node, object? value)` | `void` | 登记节点本趟产物。 |
| `ResetOutputs()` | `void` | 清空产物表；每次 `RunAsync` 调用一次。 |
| `CollectGroupedInputs(IEnumerable<INodeComponent> inputNodes)` | `IReadOnlyDictionary<INodeComponent, object?>` | 本趟有效的产物，按源节点键。 |

## RuntimeContext

**签名：** `sealed partial class RuntimeContext : IRuntimeContext`

实现上述全部成员。额外公开成员：

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `IsCompilePhase` | `bool` | 恒为 `false`。 |
| `Target` / `TargetReached` | | 目标跟踪。 |
| `MaxParallelBranches` | `int?` | 并发扇出分支上限；null 表示不限。 |
| `PendingRedirectTarget` / `ActiveRedirectTarget` | `int?` | 重定向记账。 |
| `Next()` | `int` | 原子自增并返回序号。 |
| `LogWriter` | `ILogWriter?` | 在 `Logs` 之外分流日志行。 |
| `MaxRetainedLogs` | `int?` | 内存视图上限；null 全保留，`0` 不保留。 |
| `ExecutionGate` | `IExecutionGate?` | 节点之间的暂停点。 |
| `Observer` | `IExecutionObserver?` | 运行时间线接收者。 |
| `RetryPolicy` | `INodeRetryPolicy?` | 决定抛出的失败是否重试。 |
| `ErrorSink` | `IExecutionErrorSink?` | 结构化失败接收者。 |
| `HostRedirect` | `Func<IRuntimeContext, INodeComponent, INodeComponent?>?` | 未实现 `IRedirectable` 的节点的回退钩子。 |
| `Compensation` | `IExecutionCompensation?` | 获知失败/取消运行驱动过的节点。 |
| `CheckpointStore` | `IExecutionCheckpointStore?` | 保存运行位置的地方。 |
| `Outcome` | `RunOutcome` | 对 `Status` + `EndedWithError` 的精确解读。 |
| `LogWriteFailed` | `EventHandler<LogWriteFailedEventArgs>` | `LogWriter` 抛异常时触发。 |
| `SnapshotLogs()` | `string[]` | 时点副本，运行追加时也可安全读取。 |

`Outcome` 在运行结束前为 `Unknown`。它只在具体 `RuntimeContext` 上设置；宿主自带的 `IRuntimeContext` 实现保留自己的状态，拿不到它。

## 能力解析

引擎只从具体 `RuntimeContext`（或扇出 `BranchRuntimeContext` 背后的会话）读取可选能力。自己实现 `IRuntimeContext` 的宿主因此只得到纯执行加日志，得不到门、观察者、重试、接收器、补偿、检查点或宿主重定向。`MaxParallelBranches` 与 `LogWriter` 遵循同一条规则。

`HostRedirect` 只为未实现 `IRedirectable` 的节点询问。节点自报的非法目标会被记录并忽略，流程继续；宿主的非法回答会结束流程，因为试图安排运行却给出不可能目标的宿主有 bug。

## 日志与线程

`Logs` 是受内部锁保护的 `ObservableCollection<string>`。运行可能在你枚举时追加，因此在运行线程之外请用 `SnapshotLogs()` 而不是枚举 `Logs`。

行格式：`"{sequence:00}. {text}"`，并在适用处带 `[Error]`、`[Warning]`、`[Retry n]`、`[Checkpoint]`、`[Compensation]`、`[ErrorSink]` 标记。写入器在保留检查**之前**收到行，并在驱动运行的线程上被调用。

## 示例

```csharp
var session = new RuntimeContext
{
    Data = "seed",
    MaxRetainedLogs = 100,
    MaxParallelBranches = 4,
};

session.Log("before run");
Console.WriteLine(string.Join("\n", session.SnapshotLogs()));   // 01. before run
Console.WriteLine(session.Outcome);                             // Unknown

session.Set("region", "eu");
Console.WriteLine(session.TryGet("REGION", out var region) + " " + region); // True eu
```
