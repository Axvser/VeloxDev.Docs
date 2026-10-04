# Workflow System — 检查点与日志文件

两样活过一轮运行内存的东西：检查点存储在每个节点成功后把运行位置写下来，日志写入器则在内存集合被限制时仍保留每一行。

## 1. 捕获一份检查点

先编译出 `04_编译与运行` 里那张图，然后挂上内存存储，并让运行在第一个节点之后停下：

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

**预期结果：** `attempt=1 outputs=1 shape=<guid>/<guid>/<guid>` —— 唯一成功过的那个节点一条产物，而 `Shape` 点出图会驱动的每个节点（这里是三个，按 `RuntimeId`）。

**说明：** 引擎写的是运行的**当前**状态，不是历史 —— 一个存储里只有一份最新检查点。抛异常的存储会被上报（`[Checkpoint] …`）并忽略：一份写不下来的位置，不是停下来的理由。

## 2. 从它恢复

```csharp
var resumed = new RuntimeContext();
await new RuntimeEngine().RunAsync(rootGraph, resumed, CancellationToken.None, saved);

Console.WriteLine($"{resumed.Status} data={resumed.Data} outcome={resumed.Outcome}");
```

**预期结果：** `Completed data=tick->bias->print Completed` —— 检查点记录为完成的节点**不会**被再次驱动；运行从断点接着把链跑完。

**说明：** `resumeFrom` 是 `RunAsync` 的第四个参数。已完成节点按**节点身份**跳过，而不是按 `Order` 跳过 —— 扇出各分支的 Order 是交错的，用一个阈值会错误地跳过没跑过的兄弟。

## 3. 一份检查点属于一张图

往一张形状不同的图上恢复会被**拒绝**，而不是猜：

```csharp
var otherGraph = copyGraphs[0];               // 从反序列化副本编译出来的图
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

拒绝发生在**碰会话之前**：`Status` 仍是 `"Idle"`，一个节点都没驱动。这正是想要的行为 —— 经过序列化的图全是新 `RuntimeId`，那些确实就是不同的节点对象。`ExecutionCheckpoint.Rekey(saved, otherGraph)` 是宿主在确信两张图同结构时的显式选择。

## 4. 把日志导到文件，并限制内存保留量

```csharp
var logPath = Path.Combine(Path.GetTempPath(), "veloxqs-run.log");
if (File.Exists(logPath)) File.Delete(logPath);

RuntimeContext capped;
using (var writer = TextWriterLogWriter.For(logPath))
{
    capped = new RuntimeContext { LogWriter = writer, MaxRetainedLogs = 2 };
    await new RuntimeEngine().RunAsync(rootGraph, capped, CancellationToken.None);
}   // 先 dispose —— 写入器还把文件占着
Console.WriteLine($"fileLines={File.ReadAllLines(logPath).Length} retained={capped.Logs.Count}");
```

**预期结果：**

```text
fileLines=3 retained=2
```

文件里有全部三行；`Logs` 只留下最新的两行。写入器是全保真的记录，内存里的集合是宿主可以留在内存中的有界视图 —— 写入器一行都没丢。

**说明：** 要在 dispose 写入器**之后**再读那个文件。`TextWriterLogWriter.For` 以 `FileShare.Read` 打开它，所以在它还开着时 `File.ReadAllLines` 会和写入器的写句柄冲突并抛 `IOException`。

## 5. 从别的线程安全地读日志

运行还在追加时，UI 或 Agent 可能正在读。`Logs` 是 `ObservableCollection<T>`，它不是线程安全的 —— 直接枚举活集合可能抛 `ArgumentOutOfRangeException: Source array was not long enough`。改用快照：

```csharp
string[] lines = capped.SnapshotLogs();
Console.WriteLine($"{lines.Length} lines: {string.Join(" | ", lines)}");
```

**预期结果：** `2 lines: 02. BiasNode | 03. PrinterNode` —— `MaxRetainedLogs = 2` 下最新那两行，顺序不变。

## 6. 真实仓库里它在哪

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` 用的是文件版存储与写入器：

```csharp
Checkpoints = new FileCheckpointStore(CheckpointPath);        // 一个 JSON 文件
primary.CheckpointSource = ct => Checkpoints.LoadAsync(ct);
// ConfigureRun 里：
_logWriter ??= TextWriterLogWriter.For(Scratch(LogPath));
context.LogWriter = _logWriter;
context.CheckpointStore = Checkpoints;
// 而 Dispose() 会 dispose 写入器 —— 谁开的文件谁关
```

控制器把检查点交给引擎：`await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);` —— `ResumeCommand` 是 UI 的入口，以 `session.HasCheckpoint` 为启用条件。

测试：`Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionCheckpointTests.cs`、`CompilerLogWriterTests.cs`、`RuntimeContextLogConcurrencyTests.cs`；文件存储另有 `VeloxDev.Core.Extension.Test/Serialization/ExecutionCheckpointSerializationTests.cs`。

下一步见 `12_并行与大纲`。
