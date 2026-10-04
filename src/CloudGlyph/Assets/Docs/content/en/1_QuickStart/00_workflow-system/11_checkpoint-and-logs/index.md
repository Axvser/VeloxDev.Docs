# Workflow System — Checkpoints and Log Files

Two things that outlive a run's memory: a checkpoint store writes the run's place down after each node succeeds, and a log writer keeps every line even when the in-memory collection is capped.

## 1. Capture a checkpoint

Compile the graph from `Compile & run forward`, then attach an in-memory store and stop the run after its first node:

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

**Expected result:** `attempt=1 outputs=1 shape=<guid>/<guid>/<guid>` — one output for the single node that succeeded, and a `Shape` naming every node the graph drives (three here, by `RuntimeId`).

**Notes:** the engine writes the run's **current** state, not a history — a store holds one latest checkpoint. A store that throws is reported (`[Checkpoint] …`) and ignored: a place you cannot write down is not a reason to stop working.

## 2. Resume from it

```csharp
var resumed = new RuntimeContext();
await new RuntimeEngine().RunAsync(rootGraph, resumed, CancellationToken.None, saved);

Console.WriteLine($"{resumed.Status} data={resumed.Data} outcome={resumed.Outcome}");
```

**Expected result:** `Completed data=tick->bias->print Completed` — the nodes the checkpoint records as done are **not** driven again; the run picks up where it left off and finishes the chain.

**Notes:** `resumeFrom` is the fourth argument of `RunAsync`. Nodes already recorded as done are skipped by **node identity**, not by `Order` — a fan-out's branches have interleaved orders, so an order threshold would wrongly skip untouched siblings.

## 3. A checkpoint belongs to one graph

Resuming onto a graph whose shape differs is **refused**, not guessed at:

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

**Expected result:**

```text
The checkpoint does not belong to this graph status=Idle
```

The refusal happens **before the session is touched**: `Status` is still `"Idle"` and nothing was driven. This is the intended behavior — a graph that went through serialization has all-new `RuntimeId`s, so those genuinely are different node objects. `ExecutionCheckpoint.Rekey(saved, otherGraph)` is the host's explicit opt-in when it knows the two graphs are the same structure.

## 4. Divert the log to a file and cap what stays in memory

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

**Expected result:**

```text
fileLines=3 retained=2
```

The file holds all three lines; `Logs` kept only the newest two. The writer is the full-fidelity record, the in-memory collection is the bounded view a host can leave in memory — the writer loses nothing.

**Notes:** read the file **after** disposing the writer. `TextWriterLogWriter.For` opens it with `FileShare.Read`, so a `File.ReadAllLines` while it is still open collides with the writer's write handle and throws `IOException`.

## 5. Read the log safely from another thread

A run keeps appending while a UI or an Agent reads. `Logs` is an `ObservableCollection<T>`, which is not thread-safe — enumerating it live can throw `ArgumentOutOfRangeException: Source array was not long enough`. Take a snapshot instead:

```csharp
string[] lines = capped.SnapshotLogs();
Console.WriteLine($"{lines.Length} lines: {string.Join(" | ", lines)}");
```

**Expected result:** `2 lines: 02. BiasNode | 03. PrinterNode` — with `MaxRetainedLogs = 2`, the two newest lines, in order.

## 6. Where this lives in the real repository

`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` uses the file-backed store and writer:

```csharp
Checkpoints = new FileCheckpointStore(CheckpointPath);        // a JSON file
primary.CheckpointSource = ct => Checkpoints.LoadAsync(ct);
// in ConfigureRun:
_logWriter ??= TextWriterLogWriter.For(Scratch(LogPath));
context.LogWriter = _logWriter;
context.CheckpointStore = Checkpoints;
// and Dispose() disposes the writer — whoever opened the file closes it
```

The controller passes the checkpoint to the engine: `await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);` — and `ResumeCommand` is the UI entry point, gated on `session.HasCheckpoint`.

Tests: `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/ExecutionCheckpointTests.cs`, `CompilerLogWriterTests.cs`, `RuntimeContextLogConcurrencyTests.cs`; plus `VeloxDev.Core.Extension.Test/Serialization/ExecutionCheckpointSerializationTests.cs` for the file store.

Go to `Parallel fan-out and the compiled outline`.
