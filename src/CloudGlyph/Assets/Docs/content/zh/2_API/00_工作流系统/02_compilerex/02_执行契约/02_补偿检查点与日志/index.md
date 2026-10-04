# 工作流系统 — 补偿、检查点与日志写入器

三个以某种方式「活过一轮运行」的接缝：`IExecutionCompensation`（收尾不佳的运行已经做了什么）、`IExecutionCheckpointStore`（运行的位置保存在哪）、`ILogWriter`（它的行去哪）。

源码：`Runtime/Contracts/IExecutionCompensation.cs`、`Runtime/Contracts/IExecutionCheckpointStore.cs`、`Runtime/Contracts/ILogWriter.cs`。

---

## `IExecutionCompensation`

得知失败或取消的运行已经驱动过哪些节点，好让宿主撤销它在意的那些。配置在 `RuntimeContext.Compensation`。

#### `IExecutionCompensation.CompensateAsync`

**签名：** `Task CompensateAsync(NodeCompensation compensation, CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `compensation` | `NodeCompensation` | 节点及其产物，外加它的编译序号。 |
| `cancellationToken` | `CancellationToken` | 供清理使用的令牌。它**不是**运行的令牌 —— 取消之后调用时运行那个已经取消了。引擎恒传 `CancellationToken.None`。 |

**返回：** `Task`。**最近的在前**调用，本轮每个成功过的节点一次，且只在运行以 `RunOutcome.Failed` 或 `RunOutcome.Cancelled` 收尾时 —— 完成的运行不补偿任何东西。

**异常：** 没有任何能停下其余的异常。抛出的补偿会被记日志（`[Compensation] {node} was not compensated: {message}`），剩下的节点照旧清理 —— 最初那次失败仍是头条。

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
context.Compensation = new DelegateExecutionCompensation(
    c => Controller.RuntimeContext?.Log($"[Compensation] undo {NameOf(c.Node)} (attempt {c.Order})"));
```

**说明：**

- **引擎什么都不回滚，而且做不到。** 一个节点的副作用是它自己的 —— 它写下的属性、它启动的进程、它留下的文件 —— 只有宿主知道哪些可逆。所以引擎把成果交出去，到此为止。
- **树的撤销栈不是替代品。** 它只记模型结构变更（节点自己的属性写入与脚本的文件效果从未被提交），它是一条没有运行边界的扁平栈 —— 所以一次失败不能只回卷本轮的那些条目而不吃掉用户的 —— 而且它不保证链条完整。
- 被驱动两次的节点（重定向重跑）只出现**一次**，位置是它最近一次成功的位置：「一轮结束时还立着的效果，是这个节点最近一次成功留下的那个」。由 `ExecutionCompensationTests.AfterARedirect_ASkippedPrefixNode_IsStillHandedBack_AndAReDrivenNodeOnlyOnce` 钉住。
- 被重定向作为契约保留前缀跳过的节点仍会被交还 —— 它本轮驱动过，仍在清理的范围内。

### `NodeCompensation`

**签名：**

```csharp
public readonly record struct NodeCompensation(
    IWorkflowNodeViewModel Node,
    object? Output,
    int Order);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel` | 跑过的节点。 |
| `Output` | `object?` | 它返回的东西，按登记给下游的形式。 |
| `Order` | `int` | 节点的编译序号；没有时为 `-1`。 |

**实测顺序（测试 —— `ExecutionCompensationTests`）：** `s → a → b` 链在 `a` 里被取消，交还的顺序是 `["a", "s"]`，产物是 `["A", "S"]`。

---

## `IExecutionCheckpointStore`

保存运行位置的地方，好让后来的运行接手。配置在 `RuntimeContext.CheckpointStore`；不配置时引擎从不写。

#### `IExecutionCheckpointStore.SaveAsync`

**签名：** `Task SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `checkpoint` | `ExecutionCheckpoint` | 要保存的状态。对引擎而言它是不可变的 —— 它是一份快照。 |
| `cancellationToken` | `CancellationToken` | 运行的令牌。 |

**返回：** `Task`。

**异常：** 抛出的存储会被**上报并忽略** —— 一行 `[Checkpoint] the run's place was not saved: {message}` 日志，运行照常继续。「一份写不下来的位置，不是停下来的理由。」由 `ExecutionCheckpointTests.AStoreThatThrows_DoesNotStopTheRun` 钉住。

#### `IExecutionCheckpointStore.LoadAsync`

**签名：** `Task<ExecutionCheckpoint?> LoadAsync(CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `cancellationToken` | `CancellationToken` | 调用方的令牌。 |

**返回：** `Task<ExecutionCheckpoint?>` —— 检查点；从未保存过任何东西时为 `null`。

**说明：**

- **一个存储，一次运行。** 引擎写的是运行的**当前**状态 —— 不是历史 —— 所以一个存储里只有一份最新的 `ExecutionCheckpoint`。保存多轮运行位置的宿主就保存多个存储，或者在自己的实现里按 `IRuntimeContext.Uid` 分键。
- **每个节点成功后写入，从驱动内部写。** 扇出的分支是交错的，所以即使这里没有东西跑在第二个线程上，也可能同时有两次保存。写文件的实现必须自己串行化写入。`FileCheckpointStore` 正是用 `SemaphoreSlim` 做的。
- **`LoadAsync` 是宿主的调用，不是引擎的。** `RuntimeEngine.RunAsync` 通过 `resumeFrom` 参数接收它该从哪继续；何时存在一份值得继续的检查点由宿主决定。demo 的控制器为此持有一个 `CheckpointSource` 委托。
- 随库实现：`InMemoryCheckpointStore`（Core，见`检查点`）与 `FileCheckpointStore`（`VeloxDev.Core.Extension`，见 `MVVM 序列化`）。

---

## `ILogWriter`

编译运行的日志行去哪（除 `IRuntimeContext.Logs` 之外）。

#### `ILogWriter.Write`

**签名：** `void Write(string line)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `line` | `string` | 一行已格式化、含前缀的日志，与它在 `IRuntimeContext.Logs` 里出现的样子完全一致。 |

**返回：** 无。

**异常：** 抛异常的写入器**不会**触及运行。`RuntimeContext.AppendLog` 跑在节点帧里，所以逃出去的异常会表现为一次*节点*失败，引擎会把它读成重定向请求。取而代之的是在 `RuntimeContext.LogWriteFailed` 上上报这次失败，该行被丢弃。

**示例（Demo / 测试）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
_logWriter ??= TextWriterLogWriter.For(Scratch(LogPath));
context.LogWriter = _logWriter;
```

**说明：**

- **行按实际发生的顺序到达**，而扇出的分支是交错的，所以在意分组的写入器必须自己分组。`IRuntimeContext.Logs` 收到**同样顺序**的同样的行，这使得两个视图可以逐行对照（`CompilerLogWriterTests.AWriter_ReceivesExactlyWhatLogsReceived_InTheSameOrder`）。
- **写入发生在驱动运行的那个线程上** —— 通常是宿主的 `SynchronizationContext`。因此同步碰文件系统的写入器会把那次 IO 放在那个线程上；在意的话就把行入队，再到后台线程上排空。
- **写入器不是过滤器，也不能改变语义**：无论写入器拿文本做什么，`Error` 与 `Warn` 仍然把该轮标记为需要重定向（`CompilerLogWriterTests.AWriter_DoesNotChangeWarnSemantics`）。
- 与 `RuntimeContext.MaxRetainedLogs` 配对使用：写入器是全保真的记录，内存里的集合是宿主可以留在内存中的有界视图。

### `LogWriteFailedEventArgs`

**签名：** `public sealed class LogWriteFailedEventArgs(string line, Exception error) : EventArgs`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Line` | `string` | 写不进去的那一行。无论如何它都在 `IRuntimeContext.Logs` 里。 |
| `Error` | `Exception` | 写入器抛出的东西。 |

在 `RuntimeContext.LogWriteFailed` 上触发，好让一个坏掉的接收器「可见」而不只是「安静」—— 该行仍被丢弃，运行仍然继续。
