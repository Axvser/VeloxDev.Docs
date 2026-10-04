# 工作流系统 — 执行实现

随执行契约一起发布的实现。每个接缝都有一个委托形式供已经写好逻辑的宿主使用，而真正需要行为的那两个 —— 暂停门与重试策略 —— 有具体的类。

源码：`Runtime/Model/ExecutionGates.cs`、`ExecutionObservers.cs`、`ErrorSinks.cs`、`Compensations.cs`。日志写入器与重试策略在`下一页`。

## 谁配谁

| 契约 | 实现 |
|---|---|
| `IExecutionGate` | `DelegateExecutionGate`、`ManualExecutionGate` |
| `IExecutionObserver` | `DelegateExecutionObserver` |
| `IExecutionErrorSink` | `DelegateExecutionErrorSink` |
| `IExecutionCompensation` | `DelegateExecutionCompensation` |
| `ILogWriter` | `DelegateLogWriter`、`TextWriterLogWriter` |
| `INodeRetryPolicy` | `ExponentialBackoffRetry` |
| `IExecutionCheckpointStore` | `InMemoryCheckpointStore`（Core）、`FileCheckpointStore`（`VeloxDev.Core.Extension`） |

---

## `DelegateExecutionGate`

**签名：** `public sealed class DelegateExecutionGate(Func<CancellationToken, Task> wait) : IExecutionGate`

给已经有逻辑的宿主的一行式写法。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `DelegateExecutionGate(Func<CancellationToken, Task> wait)` | `wait` 为 `null` 时抛 `ArgumentNullException`。 |
| `WaitAsync` | `Task WaitAsync(CancellationToken)` | 调用 `_wait(cancellationToken)`。 |

---

## `ManualExecutionGate`

**签名：** `public sealed class ManualExecutionGate : IExecutionGate`

宿主亲手开关的门：`Pause` 把它握在下一个节点边界，`Resume` 放它走。可从任何线程释放 —— 包括运行所在的那个。

| 成员 | 类型 | 说明 |
|---|---|---|
| `IsPaused` | `bool` | 运行当前是否被握住。 |
| `Pause()` | `void` | 在下一个节点边界握住运行。已暂停时幂等。 |
| `Resume()` | `void` | 放过被握住的运行。没被握住时是无操作。 |
| `WaitAsync(CancellationToken)` | `Task` | 门开着时返回已完成的任务；否则等在被停放的门上。 |

**异常：** 令牌触发时 `WaitAsync` 抛 `OperationCanceledException` —— 取消是抛出而不是返回，因为一个「门没开却回来了」的调用方会继续驱动，那正是「停下」的反面。

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
public ManualExecutionGate Gate { get; } = new();

// 一次运行绝不带着上一次留下的暂停开始：门是宿主的手，而每次 Run 都是新的一轮。
context.ExecutionGate = Gate;
```

**实测行为（测试 —— `CompilerEx/ExecutionGateTests.cs`，并在随库实现上复现）：**

| 断言 | 值 |
|---|---|
| 握住期间 `b.Calls` | 空 —— 被握住的运行不得驱动下一个节点 |
| 握住期间 `context.IsRunning` | `true` —— 暂停不是停止 |
| 握住期间 `context.Status` | `"Paused"` |
| `Resume` 之后 `context.Status` | `"Completed"` |

**说明：**

- 构造方式沿用本仓库既有的「停在这里直到有人说走」（`VeloxDev.Core.Timing.TimeSourceCore`）：一个**只在**门关着时存在的 `TaskCompletionSource<bool>`，以替换而非就地完成的方式换新，且在锁**外**完成。后两条不是风格 —— 持锁完成会重入可能立刻回来要同一把锁的延续，而在调用方线程上阻塞等待会让 UI 驱动的运行死锁。也不轮询布尔量：靠标志自旋的运行会烧掉它本该让出的线程。
- 开着的门不花代价：`WaitAsync` 返回已完成的任务，且不分配。
- 被宿主取消的暂停运行会结束而不是挂住：`Status = "Stopped"`，`Outcome = RunOutcome.Cancelled`。

---

## `DelegateExecutionObserver`

**签名：** `public sealed class DelegateExecutionObserver(Action<ExecutionObservation> observe) : IExecutionObserver`

给要接面板或计数器的宿主的一行式写法。`OnObservedAsync` 调用 `_observe(observation)` 并返回 `Task.CompletedTask` —— 每条观察调用一次，在驱动运行的线程上。构造函数在 `observe` 为 `null` 时抛 `ArgumentNullException`。

---

## `DelegateExecutionErrorSink`

**签名：** `public sealed class DelegateExecutionErrorSink(Action<ExecutionError> observe) : IExecutionErrorSink`

给只做计数或存储的宿主的一行式写法。`OnErrorAsync` 调用 `_observe(error)` 并返回 `Task.CompletedTask`。构造函数在 `observe` 为 `null` 时抛 `ArgumentNullException`。

**示例（Demo）：** `new DelegateExecutionErrorSink(Diagnostics.Add)`，其中 `Diagnostics` 是一个 `ObservableCollection<ExecutionError>`。

---

## `DelegateExecutionCompensation`

**签名：** `public sealed class DelegateExecutionCompensation(Action<NodeCompensation> compensate) : IExecutionCompensation`

给「每个节点撤一件事」的宿主的一行式写法。`CompensateAsync` 调用 `_compensate(compensation)` 并返回 `Task.CompletedTask` —— 每个成功驱动的节点一次，最近的在前。构造函数在 `compensate` 为 `null` 时抛 `ArgumentNullException`。

## 子页

| 页面 | 内容 |
|---|---|
| [日志写入器与重试策略](01_日志写入器与重试/index.md) | `DelegateLogWriter`、`TextWriterLogWriter`、`ExponentialBackoffRetry` |
