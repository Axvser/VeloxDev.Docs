# Workflow System — Checkpointing

The run's place as an object: `ExecutionCheckpoint`, the in-memory store that keeps it, and the internal fan-out facade that makes a session's capabilities work inside a parallel group.

Sources: `Runtime/Model/ExecutionCheckpoints.cs`, `Runtime/Model/BranchRuntimeContext.cs`.

---

## `ExecutionCheckpoint`

**Signature:** `public sealed class ExecutionCheckpoint`

A run's place: what it has already driven, what those nodes produced, and enough of the run's own state to carry on from there. Written by `RuntimeEngine.RunAsync` after each node succeeds when a `IExecutionCheckpointStore` is configured, and handed back to it as the `resumeFrom` argument.

##### Properties

| Name | Type | Description |
|---|---|---|
| `Attempt` | `int` | The pass the run was on when this was taken — `IRuntimeContext.Attempt`. |
| `ActiveRedirectTarget` | `int?` | The redirect target that pass was working with, if any. |
| `Data` | `object?` | The chained payload at the moment of the snapshot. An `IGroupData` is stored as a plain `Dictionary<string, object?>` keyed by node key. |
| `Outputs` | `Dictionary<string, object?>` | What each completed node produced, keyed by its checkpoint key. |
| `Shape` | `List<string>` | The graph's nodes in drive order — the fingerprint a resume checks itself against. |
| `Types` | `List<string>` | The node **types** behind `Shape`, in the same order. Empty on a checkpoint written before this member existed, which makes a re-key fall back to counting nodes only. |

##### Methods

#### `ExecutionCheckpoint.Rekey`

**Signature:** `public static ExecutionCheckpoint Rekey(ExecutionCheckpoint checkpoint, CompiledGraph target)`

| Parameter | Type | Description |
|---|---|---|
| `checkpoint` | `ExecutionCheckpoint` | The place, as it was written. |
| `target` | `CompiledGraph` | The graph to fit it to. |

**Returns:** `ExecutionCheckpoint` — a new checkpoint filed under `target`'s identities. The input is untouched.

**Exceptions:**

| Exception | Condition |
|---|---|
| `ArgumentNullException` | `checkpoint` is `null`. |
| `InvalidOperationException` | The two graphs are not the same structure — a different node count, or (when `Types` was written) a different node type at some position. |

**Notes:**

- **Why it exists.** A checkpoint is filed by `IWorkflowIdentifiable.RuntimeId`, and a graph that came back from serialization has fresh ones — so resuming onto it is refused by `RunAsync`. That refusal is right: those really are different node objects. `Rekey` is the host's opt-in that says *I know they are, and here is the mapping* — positional, because the traversal order is the one thing the same structure always shares.
- **What it checks is structure, not identity**: the same node count and the same node types in the same drive order. That catches a different graph; it cannot catch a same-shaped graph whose parts were renamed into other types that happen to line up. A migration between two *versions* of a graph is the host's to write.
- A checkpoint's own shape cannot be changed by re-keying: `Shape` becomes `target`'s keys and `Types` becomes `target`'s type names. A payload dictionary keyed by node key is re-keyed with it.

### Node identity inside a checkpoint

The engine files each node under `IWorkflowIdentifiable.RuntimeId` when the node has one, and otherwise under `"{TypeName}#{index}"`. The consequence to remember: a graph that went through a serialization round trip has **all-new `RuntimeId`s**, so its fingerprint will not match and a resume onto it is refused — which is the intended behavior, because those genuinely are different node objects. `ExecutionCheckpoint.Rekey` is the explicit way to say otherwise.

### `Shape` and a refused resume

`RunAsync` compares `Shape` against the graph's own node keys **before touching the session**. On mismatch it throws `InvalidOperationException` and leaves the session alone: `Status` is still `"Idle"` and `IsRunning` is `false`. Pinned by `ExecutionCheckpointTests.ACheckpointTakenOverAnotherGraph_IsRefused_AndTheSessionIsLeftAlone`, and reproduced against the shipped library:

```text
[7] refused on a serialized copy: The checkpoint does not belong to this graph status=Idle
```

**Async caveat for file-backed stores:** a checkpoint is plain JSON, and JSON has one integer type. An `int` that went in comes back as a `long`, a `float` as a `double`, and no setting changes that — a primitive is written as a bare JSON value with no type tag — so a node that pattern-matches a payload on `int` will not match after a resume through a file. The store that keeps the object graph as it is (`InMemoryCheckpointStore`) has no such gap.

---

## `InMemoryCheckpointStore`

**Signature:** `public sealed class InMemoryCheckpointStore : IExecutionCheckpointStore`

The checkpoint store that keeps the place in memory — enough for a run that pauses and resumes inside one process, and the default a host gets when it asks for checkpointing without wanting to write files.

| Member | Signature | Description |
|---|---|---|
| `HasCheckpoint` | `bool` | Whether anything has been saved. |
| `SaveAsync` | `Task SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken ct)` | Replaces what was saved. Returns a completed task. |
| `LoadAsync` | `Task<ExecutionCheckpoint?> LoadAsync(CancellationToken ct)` | Returns the last saved checkpoint, or `null`. |
| `Clear()` | `void` | Drops what was saved — for a host whose run is finished and whose place is no longer worth keeping. |

**Exceptions:** none.

**Notes:** concurrent saves are serialised with a lock, because the engine can have two fan-out branches saving at once. The checkpoint handed in is kept **as it is**, so a host that plans to mutate one afterwards should hand over a copy.

**Example (Test — `CompilerEx/ExecutionCheckpointTests.cs`; reproduced against the shipped library):**

```csharp
var store = new InMemoryCheckpointStore();
var context = new RuntimeContext { CheckpointStore = store };
await new RuntimeEngine().RunAsync(graph, context, ct, null);
var saved = await store.LoadAsync(CancellationToken.None);
// saved.Shape has one entry per node the graph drives; saved.Data is the last node's output.
```

For a store that outlives the process, use `FileCheckpointStore` from `VeloxDev.Core.Extension` — see `mvvm-serialization`.

---

## `BranchRuntimeContext` *(internal)*

`internal sealed class BranchRuntimeContext(IRuntimeContext session) : IRuntimeContext`. Not part of the public surface; documented because it explains two behaviors that are otherwise invisible.

A fan-out's branches run concurrently, so the state a branch writes between an `await` and the node that reads it back must not be shared with its siblings. It cannot be made flow-local with an `AsyncLocal<T>`: a node calls `Error` deep inside its own frame and the engine reads that flag several frames further up, and an `AsyncLocal` write does not travel back out to the caller — the first attempt at this change failed exactly there, and the engine's existing redirect/prefix tests caught it.

So each branch gets its own object instead:

| Private to the branch | Forwarded to the session |
|---|---|
| `Data`, `ReportedLevel` / `RedirectRequested`, `PendingRedirectTarget`, `CurrentNode` | identity (`Uid`), progress (`Attempt`, `NodeIndex`, `Status`, `CurrentOrder`, `CurrentEntry`, `BranchKey`), `Logs`, the shared variables (`Set` / `TryGet`), the output registry (`RegisterOutput` / `ResetOutputs` / `CollectGroupedInputs`) |

Two consequences worth knowing as a caller:

- **Logs are forwarded, not buffered.** The run's lines must read in the order they happened, interleaved branches included, so a file-backed `ILogWriter` and `IRuntimeContext.Logs` tell exactly the same story. That is also what keeps the host's single session meaningful (the UI still binds one session).
- **A `Warn` inside a branch marks the branch, not the session.** `CompilerLogWriterTests.ABranchsWarn_MarksTheBranch_NotTheSession` asserts `session.RedirectRequested == false` while the branch's warning still appears in `Logs` — the session's own `CurrentNode` belongs to whichever branch was driven last.

`IsCompilePhase` is not forwarded: it is a constant `false`. A linear chain still injects the host's session object itself, which is what `EntrySemanticsTests.OneRunSession_IsInjectedAsTheSameInstance_ToEveryNode` pins.
