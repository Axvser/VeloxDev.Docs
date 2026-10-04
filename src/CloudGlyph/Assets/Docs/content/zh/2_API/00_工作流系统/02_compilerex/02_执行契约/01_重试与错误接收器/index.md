# 工作流系统 — 重试策略与错误接收器

两个关于「出问题」的接缝：`INodeRetryPolicy` 决定抛出异常的节点能不能再来一次，`IExecutionErrorSink` 把每次失败作为记录收到，而不只是日志行。

源码：`Runtime/Contracts/INodeRetryPolicy.cs`、`Runtime/Contracts/IExecutionErrorSink.cs`。

---

## `INodeRetryPolicy`

#### `INodeRetryPolicy.NextRetryAsync`

**签名：** `Task<TimeSpan?> NextRetryAsync(NodeFailure failure, CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `failure` | `NodeFailure` | 失败的节点、它抛了什么、这是第几次重试、失败那次耗时多久。 |
| `cancellationToken` | `CancellationToken` | 运行的令牌。引擎在等待期间也遵守它。 |

**返回：** `Task<TimeSpan?>` —— 下一次尝试前的等待时长，或 `null` 把这次失败交回引擎原有的路径。

**异常：**

| 异常 | 条件 |
|---|---|
| `OperationCanceledException` | 向上传播 —— 在决策期间取消运行即结束整轮。 |
| 其它任何异常 | 按「不再重试」处理：策略的 bug 不该顶替节点本来的失败。会记一行 `[Retry] {node} was not retried: the policy failed to decide ({message})`。 |

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
// publish 节点的第一次投递是刻意失败的；这就是让它过的那一环。
context.RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 200, factor: 2.0);
```

**说明：**

- **只有抛出的异常会被重试。** 调用 `IRuntimeContext.Error` 或 `IRuntimeContext.Warn` 的节点是在做刻意的重定向请求 —— 那是节点自己要的控制流，不是值得再试一次的失败（`ExecutionRetryTests.ANodeThatAsksForARedirect_IsNotRetried`）。
- **重试不是一趟。** `IRuntimeContext.Attempt` 数的是过图趟数，同时是产物登记表的戳 —— 所以重试绝不能推进它。重试编号是策略自己的，进日志时是 `[Retry n]`。
- 节点会从**同一个输入**重新驱动，而不是接着失败那次留下的半成品继续。
- **取消从不重试。** 两次尝试之间的等待遵守运行的令牌（`ExecutionRetryTests.CancellingDuringTheRetryWait_EndsTheRun`）。
- 返回 `null` 会把失败留在引擎的路径上：`IRedirectable` 节点走重定向，否则流程结束。**永远返回等待时长的策略会无限重试** —— 运行没有别的上限；用 `NodeFailure.RetryNumber` 自己收口。
- 重试期间不写 `[Error]` 行 —— 「将要被重试的一次尝试还不是错误」—— 但会写 `[Retry 1]` 行。

### `NodeFailure`

**签名：**

```csharp
public readonly record struct NodeFailure(
    IWorkflowNodeViewModel Node,
    Exception Error,
    int RetryNumber,
    TimeSpan Elapsed);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `Node` | `IWorkflowNodeViewModel` | 失败的节点。 |
| `Error` | `Exception` | 它抛出的异常。 |
| `RetryNumber` | `int` | 本次决策针对第几次重试 —— 第一次为 `1`。 |
| `Elapsed` | `TimeSpan` | 失败那次耗时多久。 |

---

## `IExecutionErrorSink`

接收编译运行记录的每一次失败。配置在 `RuntimeContext.ErrorSink`。

#### `IExecutionErrorSink.OnErrorAsync`

**签名：** `Task OnErrorAsync(ExecutionError error, CancellationToken cancellationToken)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `error` | `ExecutionError` | 记录：哪个节点、哪个相位、什么异常、第几趟、什么级别。 |
| `cancellationToken` | `CancellationToken` | **引擎**上报时是运行的令牌；**节点**自己发的记录为 `CancellationToken.None`，它不携带令牌 —— 报告是一条记录，不是可被打断的工作。 |

**返回：** `Task`。await 才是重点：它让宿主的记录保持运行产生的顺序，也让节点知道它的报告落地了。

**异常：** 没有任何能到达运行的异常。抛异常的接收器会被吞掉并写进运行的日志（`[ErrorSink] the failure was not recorded: {message}`）—— 上报一次失败不能自己添一条失败。由 `ExecutionErrorSinkTests.AThrowingErrorSink_DoesNotTurnAWarningIntoAFailure` 钉住。

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
// Diagnostics 是一个 ObservableCollection<ExecutionError> —— 接收器就是它的 Add。
context.ErrorSink = new DelegateExecutionErrorSink(Diagnostics.Add);
```

**说明：**

- 运行已经把每一条都写成日志行了；接收器是给想要**数据**形态的宿主 —— 好计数、好存储、好在面板上展示。引擎刻意不做分类：一个失败意味着什么由宿主说了算，所以它拿到字段自己决定。
- **两条入口。** 引擎上报它自己看见的（节点抛出、宿主契约放弃、重定向上限、取消），节点则通过 `ErrorAsync` / `WarnAsync` 上报。调用**同步**的 `Error` / `Warn` 的节点只写日志，这是刻意的 —— 那两个方法必须保持不阻塞。

### `ExecutionError`

**签名：**

```csharp
public readonly record struct ExecutionError(
    ExecutionFailurePhase Phase,
    IWorkflowNodeViewModel? Node,
    string Message,
    Exception? Error,
    int Attempt,
    int Order,
    ExecutionReportLevel Level = ExecutionReportLevel.Error);
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `Phase` | `ExecutionFailurePhase` | 来自哪里。 |
| `Node` | `IWorkflowNodeViewModel?` | 涉及的节点；运行级失败为 `null`。 |
| `Message` | `string` | 引擎记录的消息。 |
| `Error` | `Exception?` | 有异常时的异常。 |
| `Attempt` | `int` | 运行的趟号。 |
| `Order` | `int` | 节点的编译序号；没有时为 `-1`。 |
| `Level` | `ExecutionReportLevel` | 除非节点报的是警告，否则是 `Error`。引擎自己记录的一切都是错误。 |

### `ExecutionFailurePhase`

**签名：** `public enum ExecutionFailurePhase`

| 成员 | 值 | 含义 |
|---|---|---|
| `Node` | 0 | 节点抛出，或经 `IRuntimeContext.Error` 请求重定向。 |
| `Router` | 1 | 路由器在运行期解析路由键时抛出。 |
| `Redirect` | 2 | 节点在解析「重定向到哪里」时抛出（宿主实现的 `IRedirectable`）。 |
| `Run` | 3 | 运行自身失败 —— 重定向上限，或结束它的取消。 |

### `ExecutionReportLevel`

**签名：** `public enum ExecutionReportLevel { Warning = 0, Error = 1 }`

| 成员 | 值 | 含义 |
|---|---|---|
| `Warning` | 0 | 节点调用了 `Warn` / `WarnAsync`：值得知道，但没出问题。 |
| `Error` | 1 | 节点调用了 `Error` / `ErrorAsync`、抛出异常，或引擎自己放弃了。 |

**说明：** 引擎自己的记录永远不会带 `Warning`。被取消的运行会报一条 `Run` 相位、`Node == null`、带 `OperationCanceledException` 的记录，并且刻意**不**写 `[Error]` 日志行 —— 宿主停掉自己的运行不是失败，加一行 `[Error]` 会让以后读 `Logs` 的人以为出过错。

**按场景的记录相位（测试证据 —— `CompilerEx/ExecutionErrorSinkTests.cs`、`EngineHostContractFailureTests.cs`）：**

| 场景 | 记录数 | 相位 |
|---|---|---|
| 节点抛出，且没有 `IRedirectable` 能安置它 | 2 —— 节点自己的失败，然后是引擎「流程到此结束」的决定 | `Node`，随后 `Node` 且 `Error == null` |
| 节点调用 `ErrorAsync` | 2 —— 节点的记录，然后是引擎的 | `Node` |
| 节点调用 `WarnAsync` | 1 | `Node`，`Level == Warning` |
| 路由器抛出 | 1 | `Router` |
| `IRedirectable.ResolveRedirectAsync` 抛出 | 1 | `Redirect` |
| 宿主取消运行 | 1 | `Run`，`Node == null`，`Error` 是那个 `OperationCanceledException` |
| 超出重定向上限 | 1 | `Run` |
