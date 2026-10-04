# 工作流系统 — 日志写入器与重试策略

两个承载真正行为（而不是转发给委托）的实现：`TextWriterLogWriter`（文件版 `ILogWriter`）与 `ExponentialBackoffRetry`（默认 `INodeRetryPolicy`）。

源码：`Runtime/Model/LogWriters.cs`、`Runtime/Model/RetryPolicies.cs`。

---

## `DelegateLogWriter`

**签名：** `public sealed class DelegateLogWriter(Action<string> write) : ILogWriter`

给测试与已经有接收器的宿主的一行式写法。`Write` 调用 `_write(line)` —— 每行一次，在驱动运行的线程上。构造函数在 `write` 为 `null` 时抛 `ArgumentNullException`。

---

## `TextWriterLogWriter`

**签名：** `public sealed class TextWriterLogWriter : ILogWriter, IDisposable`

一个追加到 `System.IO.TextWriter` 的 `ILogWriter` —— 最常见的场景是以追加方式打开的文件。

| 成员 | 类型 | 说明 |
|---|---|---|
| 构造函数 | `TextWriterLogWriter(TextWriter writer)` | 包装一个已有写入器，本实例**不会**关闭它。`writer` 为 `null` 时抛 `ArgumentNullException`。 |
| `For(string path)` | `static TextWriterLogWriter` | 以追加方式打开（或创建）`path`，UTF-8 **不带**字节序标记。返回的实例拥有该流。 |
| `Path` | `string?` | 本写入器追加的文件，绝对路径；包装宿主已有 `TextWriter` 时为 `null`。 |
| `Write(string line)` | `void` | 追加一行并**刷写**，好让读文件的宿主不必等缓冲就能看到。 |
| `Dispose()` | `void` | 刷写；本实例打开的文件会被关闭 —— 借来的 `TextWriter` 留给它的主人。 |

#### `TextWriterLogWriter.For`

**签名：** `public static TextWriterLogWriter For(string path)`

| 参数 | 类型 | 说明 |
|---|---|---|
| `path` | `string` | 日志文件。它所在的目录必须已存在。 |

**返回：** `TextWriterLogWriter` —— 拥有该流的写入器；dispose 它会刷写并关闭。

**异常：** 目录不存在时由底层 `FileStream` 抛 `FileNotFoundException` / `DirectoryNotFoundException`。（demo 之所以在打开写入器之前先建好 scratch 目录，正是因为这一点。）

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
_logWriter ??= TextWriterLogWriter.For(Scratch(LogPath));
context.LogWriter = _logWriter;
// 以及在 Dispose() 里：
_logWriter?.Dispose();
```

**实测行为**（在随库实现上复现）：

```text
[9] logfile: path=C:\Users\Axvse\AppData\Local\Temp\veloxqs-run.log
[9] logfile: fileLines=3 retained=2 snapshot=2
[9] retained: 02. BiasNode | 03. PrinterNode
[9] file head: 01. TickerNode
```

文件里有全部三行，而 `MaxRetainedLogs = 2` 只在内存里保留了最新的两行 —— 写入器是全保真的记录，`Logs` 是它的有界视图。`CompilerLogWriterTests.MaxRetainedLogs_KeepsTheNewestLines_AndTheWriterLosesNothing` 与 `TextWriterLogWriter_For_AppendsWithoutABom` 钉住同一份契约。

**说明：**

- **谁开的流谁关。** 建立在别人递进来的 `TextWriter` 上的写入器永不关闭那个写入器 —— 宿主会一直用它跨轮追加。`For` 建的那个自己开了文件，所以 dispose 它会刷写并关闭。两种 dispose 都会刷写。
- 暴露 `Path` 是为了让宿主能告诉别人日志去了**哪里**，而不必顺带交出写入器：一个被要求读取某轮日志的 Agent 需要一个可以打开的路径，它没有别的办法得知。
- 它在驱动运行的线程上被调用 —— 通常是宿主的 UI 线程。在意的话就把它（或它拿到的 `TextWriter`）包进你自己的队列。

---

## `ExponentialBackoffRetry`

**签名：** `public sealed class ExponentialBackoffRetry : INodeRetryPolicy`

把失败的节点重试固定次数，每轮等待翻倍。宿主想要重试但不想自己写策略时得到的默认实现。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `ExponentialBackoffRetry(int maxAttempts = 3, double baseDelayMs = 200, double factor = 2.0, double maxDelayMs = 5000)` | — |
| `MaxAttempts` | `int` | 一个节点总共能尝试多少次，**含第一次**。 |
| `NextRetryAsync` | `Task<TimeSpan?> NextRetryAsync(NodeFailure failure, CancellationToken ct)` | 返回等待时长；次数用尽后返回 `null`。 |

**构造函数参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `maxAttempts` | `int` | 总共尝试多少次，含第一次 —— `3` 意思是「试、重试、重试」。下限钳到 `1`。 |
| `baseDelayMs` | `double` | 第一次重试前的等待，毫秒。下限钳到 `0`。 |
| `factor` | `double` | 每次等待乘多少。下限钳到 `1`。 |
| `maxDelayMs` | `double` | 单次等待的上限，好让长串重试保持有界。下限钳到 `baseDelayMs`。 |

**等待公式：**

$$
d_k = \min\left(\text{baseDelayMs} \cdot \text{factor}^{\,k-1},\; \text{maxDelayMs}\right) \quad \text{第 } k \text{ 次重试},\; k = 1, 2, \dots
$$

**返回：** `Task<TimeSpan?>` —— 当 `failure.RetryNumber >= MaxAttempts` 时为 `null`。

**异常：** 不抛。引擎会捕获抛异常的策略并按「不再重试」处理。

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
context.RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 200, factor: 2.0);
```

**实测行为**（在随库实现上以 `maxAttempts: 3, baseDelayMs: 1` 复现）：

```text
[8] retry: status=Completed data=ok drives=3 attempt=1 outcome=Completed
[8] retry logs: 01. FlakyNode | 02. [Retry 1] FlakyNode: flaky #1 | 03. [Retry 2] FlakyNode: flaky #2
```

节点抛了两次，第三次驱动成功；`Attempt` 保持为 `1`，因为重试不是一趟过图。

**说明：**

- 等待是纯粹的延时：引擎把节点失败交给策略，它回一个 `TimeSpan`，所以这里没有任何检查异常的东西。想要「重试超时但不要重试校验错误」的宿主自己写 —— 决策只有一个方法。
- `maxAttempts == 1` 表示「不重试」：第一次失败的 `RetryNumber` 已经是 `1`，策略立刻停。
