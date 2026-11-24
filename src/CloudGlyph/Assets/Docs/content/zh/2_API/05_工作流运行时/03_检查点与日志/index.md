# 检查点与日志

检查点是运行的位置，在每个节点成功后写入。日志写入器在内置集合之外分流运行日志行。两者都可选，且配置在 `RuntimeContext` 上。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## IExecutionCheckpointStore

**签名：** `interface IExecutionCheckpointStore`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken cancellationToken)` | `Task` | 替换已保存状态。 |
| `LoadAsync(CancellationToken cancellationToken)` | `Task<ExecutionCheckpoint?>` | 读取最后保存的状态；从未保存时为 null。 |

一个 store 对应一次运行：它保留最新状态，不是历史。配置了 store 的运行会在每个成功节点后、从驱动内部写入；两个扇出分支因此可能并发保存，文件实现必须自行串行写入。`LoadAsync` 是宿主的调用——引擎从不自行加载；宿主把检查点传给 `RunAsync`。

## ExecutionCheckpoint

**签名：** `[Archivable] sealed class ExecutionCheckpoint`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Attempt` | `int` | 快照所在的趟次。 |
| `ActiveRedirectTarget` | `int?` | 该趟的重定向目标（若有）。 |
| `Data` | `object?` | 链式载荷；`GroupData` 存为按节点键索引的字典。 |
| `Outputs` | `Dictionary<string, object?>` | 已完成节点产物，按节点键。 |
| `Shape` | `List<string>` | 按驱动顺序的图节点键——恢复指纹。 |
| `Types` | `List<string>` | 与 `Shape` 同序的节点类型。 |
| `Rekey(ExecutionCheckpoint checkpoint, CompiledGraph target)` | `ExecutionCheckpoint` | 把检查点重归档到同一结构的新节点身份上。 |

`Rekey` 用于从序列化返回的图——那里每个 `RuntimeId` 都是新的。它检查节点数与按驱动顺序的节点类型，而不是身份；结构不同时抛 `InvalidOperationException`。输入不被修改。

键是 `IRuntimeIdentifiable.RuntimeId`，没有身份的节点用 `"{TypeName}#{index}"`。来自另一张图的检查点会在触碰会话前被 `RunAsync` 拒绝。

## InMemoryCheckpointStore

**签名：** `sealed class InMemoryCheckpointStore : IExecutionCheckpointStore`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `HasCheckpoint` | `bool` | 是否保存过。 |
| `SaveAsync(ExecutionCheckpoint, CancellationToken)` | `Task` | 在锁下保存实例。 |
| `LoadAsync(CancellationToken)` | `Task<ExecutionCheckpoint?>` | 返回已存实例。 |
| `Clear()` | `void` | 丢弃已存状态。 |

存的是交进来的实例；打算之后修改它的宿主应先交副本。

## ILogWriter

**签名：** `interface ILogWriter`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Write(string line)` | `void` | 收到一条已格式化行，含前缀。 |

行按发生顺序到达，`Logs` 以同序收到同样的行。写入发生在驱动运行的线程上，通常是宿主的同步上下文。写入器不能改变语义：无论它对文本做什么，`Error`/`Warn` 仍标记运行。

## LogWriteFailedEventArgs

**签名：** `sealed class LogWriteFailedEventArgs(string line, Exception error) : EventArgs`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Line` | `string` | 未能写入的行；它仍在 `Logs` 里。 |
| `Error` | `Exception` | 写入器抛出的异常。 |

经 `RuntimeContext.LogWriteFailed` 触发；行被丢弃，运行继续。

## DelegateLogWriter

**签名：** `sealed class DelegateLogWriter(Action<string> write) : ILogWriter`

包装同步动作；null 抛 `ArgumentNullException`。

## TextWriterLogWriter

**签名：** `sealed class TextWriterLogWriter : ILogWriter, IDisposable`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `TextWriterLogWriter(TextWriter writer)` | 构造函数 | 包装既有写入器且不关闭它；null 抛 `ArgumentNullException`。 |
| `For(string path)` | `TextWriterLogWriter` | 以追加方式打开或创建文件，UTF-8 无 BOM；返回的写入器拥有流。 |
| `Path` | `string?` | `For` 实例的绝对日志路径；借用写入器为 null。 |
| `Write(string line)` | `void` | 追加并刷新。 |
| `Dispose()` | `void` | 刷新；`For` 实例还会关闭文件。 |

`Path` 的存在让宿主能告诉其他组件日志去了哪里，而无需交出写入器。

## 示例

```csharp
var store = new InMemoryCheckpointStore();
var first = new RuntimeContext { Data = "seed", CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, first, CancellationToken.None);

var place = await store.LoadAsync(CancellationToken.None);
Console.WriteLine($"{place!.Shape.Count} {place.Outputs.Count} {place.Attempt}");

var resumed = new RuntimeContext { Data = "seed", CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, resumed, CancellationToken.None, place);

using var writer = TextWriterLogWriter.For(Path.Combine(Path.GetTempPath(), "run.log"));
var logged = new RuntimeContext { Data = "seed", LogWriter = writer };
await new RuntimeEngine().RunAsync(graph, logged, CancellationToken.None);
```
