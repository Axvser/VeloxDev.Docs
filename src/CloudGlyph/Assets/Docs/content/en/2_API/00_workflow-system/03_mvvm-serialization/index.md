# Workflow System — Namespace: `VeloxDev.MVVM.Serialization`

Three serializers and one fluent options builder, all in `VeloxDev.Core.Extension`. Core has no serializer of its own, which is why the compiled-graph and checkpoint documents live here rather than beside the types they write.

Sources: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`, `CompiledGraphEx.cs`, `CheckpointEx.cs`.

---

## `ComponentModelEx` — whole-tree JSON

Newtonsoft based. Base settings: `TypeNameHandling.Auto`, `PreserveReferencesHandling.Objects`, `ReferenceLoopHandling.Ignore`, `NullValueHandling.Include`, `DefaultValueHandling.Include`, `WritablePropertiesOnlyResolver`, `DictionaryKeyConverter`.

| Method | Signature |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)` where `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)` (+ options overload) |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)` (+ options overload) |
| Async | `SerializeAsync`, `DeserializeAsync` |
| Streaming | `SerializeToUtf8Bytes`, `DeserializeFromUtf8Bytes`, `SerializeToTextWriterAsync`, `DeserializeFromTextReaderAsync`, `SerializeToStreamAsync`, `DeserializeFromStreamAsync` |
| Options | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)/WithExcludedPropertyTypes(...)` |

**Example** — save/load in the demo tree: `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, `Save` command (`var json = this.Serialize();`), and `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs` (`json.Deserialize<TreeViewModel>()` + `Layout.UpdateCommand.Execute(null)`).

---

## `SerializationOptions`

**Signature:** `public sealed class SerializationOptions`

A fluent builder that **mutates itself and returns `this`**, so the exclusions below are applied to the instance you pass in.

| Member | Signature | Notes |
|---|---|---|
| `Create()` | `static SerializationOptions Create()` | A fresh builder. |
| `WithIndented()` | `SerializationOptions` | `Formatting.Indented`. |
| `WithCompact()` | `SerializationOptions` | `Formatting.None`. |
| `WithTypeNameHandling(TypeNameHandling)` | `SerializationOptions` | Newtonsoft's `TypeNameHandling`. |
| `WithNullValueHandling(NullValueHandling)` | `SerializationOptions` | Newtonsoft's `NullValueHandling`. |
| `WithDefaultValueHandling(DefaultValueHandling)` | `SerializationOptions` | Newtonsoft's `DefaultValueHandling`. |
| `WithExcludedPropertyTypes(params Type[])` | `SerializationOptions` | Drops any property whose declared type is one of these — how `CompiledGraphEx` stops the writer following references out of a graph. |

---

## `CompiledGraphEx` — a compiled graph as a document

**Signature:** `public static class CompiledGraphEx`

| Member | Signature | Notes |
|---|---|---|
| `SerializeCompiledGraph` | `string SerializeCompiledGraph(this CompiledGraph graph, bool includeTree = false, SerializationOptions? options = null)` | Returns the document. Throws `ArgumentNullException` when `graph` is `null`. |
| `DeserializeCompiledGraph` | `CompiledGraph? DeserializeCompiledGraph(this string json)` | Reads a document written by the above. |

A compiled graph is an ordinary VeloxDev view model — segments holding nodes in observable collections, no slots and no links in its own shape — so it serializes with the same machinery a tree does. What it needs on top is a decision about **how far the document reaches**, because a node is the live canvas instance and its writable members point outward: `Parent` reaches the tree, and a slot's `Targets`/`Sources` reach every node connected to it. Serializing without a decision therefore costs the whole tree plus the whole connected component.

| Mode | `includeTree` | Keeps | Cost |
|---|---|---|---|
| **Snapshot** (default) | `false` | The segment structure plus each node's own state — what a deep copy, an archive or a list view wants. Drops `IWorkflowTreeViewModel` and `ObservableCollection<IWorkflowSlotViewModel>` properties. | Not re-mountable: the restored nodes have no `Parent`, so nothing re-collapses their geometry for the zoom and nothing marks the tree dirty when they move. |
| **With the tree** | `true` | Everything, so the restored graph can be put back on a canvas. | The size of the tree plus the connected component — and the nodes' `Parent` is a *second*, freshly constructed tree: the nodes come back wired to that copy, not to the one you have. |

Independently of the mode, a restored node gets a **fresh `RuntimeId`** (it is not a writable member) and carries **no compile identity** (`ICompileTimeAware.CompileContext` is not writable either). Branch keys are the exception that is repaired: an enum key comes back as its number from any round trip, so the compiler records the type beside it and it is restored on load — see `CompileKeyNormalizer`.

**Notes:** no exclusions are applied on the way **in**, deliberately: the filter exists to stop the *writer* following references out of the graph, and a reader follows nothing — a member the document does not contain simply stays as its constructor left it.

---

## `CheckpointEx` — a run's place as JSON

**Signature:** `public static class CheckpointEx`

| Member | Signature | Notes |
|---|---|---|
| `SerializeCheckpoint` | `string SerializeCheckpoint(this ExecutionCheckpoint checkpoint)` | JSON text, **indented** — it is a file a person may end up opening. Throws `ArgumentNullException` when `checkpoint` is `null`. |
| `DeserializeCheckpoint` | `ExecutionCheckpoint? DeserializeCheckpoint(this string json)` | The checkpoint, or `null` when the text is empty or is not a checkpoint (parse failures are swallowed). |

It goes through the same settings the rest of the library uses — the ones behind `ComponentModelEx` — rather than a private set of its own, so a checkpoint and the graph it belongs to are written the same way and a payload keeps its shape: a dictionary comes back as a dictionary rather than a `JObject`.

**Notes:**

- **Numbers do not keep their type, and that is measured, not assumed.** A payload is `object`, and JSON has one integer type: an `int` that went in comes back as a `long`, a `float` as a `double`. `TypeNameHandling.All` does not help — primitives are written as bare JSON values whatever the setting. The engine's own fields (`ExecutionCheckpoint.Attempt`, the keys, the shape) are exact; a node that pattern-matches a payload on `int` will not match after a resume. `InMemoryCheckpointStore` has no such gap.
- **A checkpoint is a plain document, not a view model**, which is why it does not go through `ComponentModelEx.Serialize` — that surface is constrained to `INotifyPropertyChanged`.

---

## `FileCheckpointStore`

**Signature:** `public sealed class FileCheckpointStore : IExecutionCheckpointStore`

A checkpoint store backed by one file, so a run's place outlives the process that took it.

| Member | Signature | Notes |
|---|---|---|
| constructor | `FileCheckpointStore(string path)` | Throws `ArgumentNullException` when `path` is `null` or whitespace. |
| `Path` | `string` | The file this store reads and writes. |
| `SaveAsync` | `Task SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken ct)` | Replaces the file's contents; the directory is created on the first save if it does not exist. |
| `LoadAsync` | `Task<ExecutionCheckpoint?> LoadAsync(CancellationToken ct)` | `null` when the file does not exist or does not parse. |

**Notes:**

- **One store, one file, one run.** Each save replaces the file's contents.
- The engine can have two fan-out branches saving at once (they interleave rather than run on separate threads, but an `await` is enough to overlap them), so writes are serialised behind a `SemaphoreSlim` — two writers on one file would otherwise be free to interleave their bytes. Serialization happens **outside** the gate, so only the I/O waits.
- Writes are synchronous (`File.WriteAllText`): this project has a single `netstandard2.0` target, which has no `WriteAllTextAsync`.

**Example (Demo):**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
Checkpoints = new FileCheckpointStore(CheckpointPath);
primary.CheckpointSource = ct => Checkpoints.LoadAsync(ct);
// and the controller hands it to the engine:
await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);
```

**Test evidence:** `VeloxDev.Core.Extension.Test/Serialization/ExecutionCheckpointSerializationTests.cs` — `FileCheckpointStore_KeepsThePlace_AcrossInstances`, `FileCheckpointStore_SaveReplacesWhatWasThere`.
