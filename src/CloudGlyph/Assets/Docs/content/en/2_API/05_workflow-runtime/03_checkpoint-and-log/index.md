# Checkpoint and log

A checkpoint is the run's place, written after each node succeeds. A log writer diverts the run's lines beyond the in-memory collection. Both are optional and configured on `RuntimeContext`.

Namespace: `VeloxDev.Core.WorkflowSystem.CompilerEx`.

## IExecutionCheckpointStore

**Signature:** `interface IExecutionCheckpointStore`

| Member | Type | Description |
| --- | --- | --- |
| `SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken cancellationToken)` | `Task` | Replaces the saved state. |
| `LoadAsync(CancellationToken cancellationToken)` | `Task<ExecutionCheckpoint?>` | Reads the last saved state; null when nothing was saved. |

One store, one run: the store keeps the latest state, not a history. A run with a store writes after each successful node, from inside the drive; two fan-out branches can therefore save concurrently, so a file-backed implementation must serialise its own writes. `LoadAsync` is the host's call — the engine never loads on its own; the host passes the checkpoint to `RunAsync`.

## ExecutionCheckpoint

**Signature:** `[Archivable] sealed class ExecutionCheckpoint`

| Member | Type | Description |
| --- | --- | --- |
| `Attempt` | `int` | The pass the snapshot was taken on. |
| `ActiveRedirectTarget` | `int?` | The pass's redirect target, if any. |
| `Data` | `object?` | The chained payload; a `GroupData` is stored as a dictionary keyed by node key. |
| `Outputs` | `Dictionary<string, object?>` | Completed node outputs keyed by node key. |
| `Shape` | `List<string>` | The graph's node keys in drive order — the resume fingerprint. |
| `Types` | `List<string>` | The node types behind `Shape`, same order. |
| `Rekey(ExecutionCheckpoint checkpoint, CompiledGraph target)` | `ExecutionCheckpoint` | Re-files a checkpoint onto the same structure with new node identities. |

`Rekey` is for a graph that came back from serialization, where every `RuntimeId` is new. It checks node count and node types in drive order, not identity, and throws `InvalidOperationException` when the structure differs. The input is untouched.

Keys are `IRuntimeIdentifiable.RuntimeId`, or `"{TypeName}#{index}"` for a node without one. A checkpoint from a different graph is refused by `RunAsync` before the session is touched.

## InMemoryCheckpointStore

**Signature:** `sealed class InMemoryCheckpointStore : IExecutionCheckpointStore`

| Member | Type | Description |
| --- | --- | --- |
| `HasCheckpoint` | `bool` | Whether anything has been saved. |
| `SaveAsync(ExecutionCheckpoint, CancellationToken)` | `Task` | Stores the instance under a lock. |
| `LoadAsync(CancellationToken)` | `Task<ExecutionCheckpoint?>` | Returns the stored instance. |
| `Clear()` | `void` | Drops the saved state. |

The stored instance is kept as handed in; a host that plans to mutate it should hand over a copy.

## ILogWriter

**Signature:** `interface ILogWriter`

| Member | Type | Description |
| --- | --- | --- |
| `Write(string line)` | `void` | Receives one already-formatted line, prefix included. |

Lines arrive in the order they happened, and `Logs` receives the same lines in the same order. Writes happen on the thread driving the run, normally the host's synchronization context. A writer cannot change semantics: `Error`/`Warn` still mark the run whatever the writer does with the text.

## LogWriteFailedEventArgs

**Signature:** `sealed class LogWriteFailedEventArgs(string line, Exception error) : EventArgs`

| Member | Type | Description |
| --- | --- | --- |
| `Line` | `string` | The line that could not be written; it is still in `Logs`. |
| `Error` | `Exception` | What the writer threw. |

Raised through `RuntimeContext.LogWriteFailed`; the line is dropped and the run continues.

## DelegateLogWriter

**Signature:** `sealed class DelegateLogWriter(Action<string> write) : ILogWriter`

Wraps a synchronous action; throws `ArgumentNullException` for a null delegate.

## TextWriterLogWriter

**Signature:** `sealed class TextWriterLogWriter : ILogWriter, IDisposable`

| Member | Type | Description |
| --- | --- | --- |
| `TextWriterLogWriter(TextWriter writer)` | constructor | Wraps an existing writer this instance will not close; throws `ArgumentNullException`. |
| `For(string path)` | `TextWriterLogWriter` | Opens or creates the file for append, UTF-8 without BOM; the returned writer owns the stream. |
| `Path` | `string?` | Absolute log path for a `For` instance; null for a borrowed writer. |
| `Write(string line)` | `void` | Appends the line and flushes. |
| `Dispose()` | `void` | Flushes and, for a `For` instance, closes the file. |

The `Path` member exists so a host can tell another component where the log went without handing over the writer.

## Example

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
