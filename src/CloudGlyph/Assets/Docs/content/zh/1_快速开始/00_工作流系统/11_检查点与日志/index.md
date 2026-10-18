# 工作流系统 — 检查点与日志文件

两样比运行内存活得更久的东西：检查点存储在每次节点成功后记下运行位置；日志写入器则在内存集合被限制时仍保留每一行。

## 1. 捕获检查点

编译「编译并运行」中的图，挂上内存存储，并在第一个节点后停止运行：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var store = new InMemoryCheckpointStore();
var cts = new CancellationTokenSource();
var partial = new RuntimeContext
{
    CheckpointStore = store,
    Observer = new DelegateExecutionObserver(o =>
    {
        if (o.Kind == ExecutionObservationKind.NodeSucceeded) cts.Cancel();
    }),
};

try
{
    await new RuntimeEngine().RunAsync(rootGraph, partial, cts.Token, null);
}
catch (OperationCanceledException) { }

var saved = await store.LoadAsync(CancellationToken.None);
Console.WriteLine($"attempt={saved!.Attempt} outputs={saved.Outputs.Count} shape={string.Join("/", saved.Shape)}");
```

**预期结果：** `attempt=1 outputs=1 shape=<guid>/<guid>/<guid>` —— 一个成功节点对应一条输出，`Shape` 按 `RuntimeId` 命名图驱动的每个节点（这里是三个）。

**说明：** 引擎写的是运行的**当前**状态，不是历史 —— 一个存储只保留一份最新检查点。抛异常的存储会被报告（`[Checkpoint] …`）并忽略：记不下来的位置不是停止工作的理由。

## 2. 从检查点恢复

```csharp
var resumed = new RuntimeContext();
await new RuntimeEngine().RunAsync(rootGraph, resumed, CancellationToken.None, saved);

Console.WriteLine($"{resumed.Status} data={resumed.Data} outcome={resumed.Outcome}");
```

**预期结果：** `Completed data=tick->bias->print Completed` —— 检查点记录为已完成的节点**不会**再次驱动；运行从停下的位置接上并走完链。

**说明：** `resumeFrom` 是 `RunAsync` 的第四个参数。已记录完成的节点按**节点身份**跳过，而不是按 `Order` —— 扇出分支的 Order 是交错的，按阈值会错误跳过尚未触碰的兄弟节点。

## 3. 检查点只属于一张图

恢复到形状不同的图上会被**拒绝**，而不是猜测：

```csharp
var otherGraph = copyGraphs[0];               // the graph compiled from the deserialized copy
var refused = new RuntimeContext();
try
{
    await new RuntimeEngine().RunAsync(otherGraph, refused, CancellationToken.None, saved);
}
catch (InvalidOperationException ex)
{
    Console.WriteLine($"{ex.Message.Split(':')[0]} status={refused.Status}");
}
```

**预期结果：**

```text
The checkpoint does not belong to this graph status=Idle
```

拒绝发生在**触碰会话之前**：`Status` 仍是 `"Idle"`，什么都没驱动。这是预期行为 —— 经过序列化的图拥有全新的 `RuntimeId`，那些确实已是不同的节点对象。`ExecutionCheckpoint.Rekey(saved, otherGraph)` 是宿主的显式选择，表示它知道两张图结构相同。

## 4. 把日志改道到文件并限制内存保留

```csharp
var logPath = Path.Combine(Path.GetTempPath(), "veloxqs-run.log");
if (File.Exists(logPath)) File.Delete(logPath);

RuntimeContext capped;
using (var writer = TextWriterLogWriter.For(logPath))
{
    capped = new RuntimeContext { LogWriter = writer, MaxRetainedLogs = 2 };
    await new RuntimeEngine().RunAsync(rootGraph, capped, CancellationToken.None);
}   // dispose first — the writer holds the file open
Console.WriteLine($"fileLines={File.ReadAllLines(logPath).Length} retained={capped.Logs.Count}");
```

**预期结果：**

```text
fileLines=3 retained=2
```

文件保留全部三行；`Logs` 只留最新两行。写入器是全保真记录，内存集合是宿主可以留在内存里的有限视图 —— 写入器不丢任何东西。

**说明：** 要在**释放写入器之后**读文件。`TextWriterLogWriter.For` 以 `FileShare.Read` 打开文件，写入器仍打开时 `File.ReadAllLines` 会与写句柄冲突并抛 `IOException`。

## 5. 从另一个线程安全读取日志

运行会持续追加，而 UI 或 Agent 同时在读。`Logs` 是 `ObservableCollection<T>`，并非线程安全 —— 实时枚举可能抛 `ArgumentOutOfRangeException: Source array was not long enough`。请取快照：

```csharp
string[] lines = capped.SnapshotLogs();
Console.WriteLine($"{lines.Length} lines: {string.Join(" | ", lines)}");
```

**预期结果：** `2 lines: 02. BiasNode | 03. PrinterNode` —— 在 `MaxRetainedLogs = 2` 下，最新两行按顺序保留。

## 6. 真实仓库中的位置

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 使用文件存储与写入器：

```csharp
Checkpoints = new FileCheckpointStore(CheckpointPath);        // a JSON file
primary.CheckpointSource = ct => Checkpoints.LoadAsync(ct);
// in ConfigureRun:
_logWriter ??= TextWriterLogWriter.For(Scratch(LogPath));
context.LogWriter = _logWriter;
context.CheckpointStore = Checkpoints;
// and Dispose() disposes the writer — whoever opened the file closes it
```

控制器把检查点交给引擎：`await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);` —— `ResumeCommand` 是 UI 入口，以 `session.HasCheckpoint` 为条件。

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionCheckpointTests.cs`、`CompilerLogWriterTests.cs`、`RuntimeContextLogConcurrencyTests.cs`；以及 `VeloxDev.Core.Extension.Test/Serialization/ExecutionCheckpointSerializationTests.cs` 覆盖文件存储。

前往「并行与大纲」。
