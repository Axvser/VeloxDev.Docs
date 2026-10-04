# Workflow System — Complexity of Compilation and Execution

KaTeX for the asymptotic bounds; every figure is grounded in the cited source. All of it lives in `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/`.

## Compilation (`CompilerViewModel.CompileAsync`)

Compilation is a remembered decomposition. With $V$ nodes and $E$ edges (connections):

$$
T_{\text{compile}} = O(V + E)
$$

- **Root** (`CompileGraphAsync`, lines 59-249): walks downstream from the controller. `CompileState.Visited` guarantees each node is processed once; each node enumerates its output slots' `Targets`, and every edge runs the sender's `AccessAsync` static gate (`GetValidTargetsAsync` lines 414-447) — rejected edges are dropped, so invalid edges only cost one `AccessAsync` call each. Linear runs fold into a `ChainSegment`; routers expand each route key recursively (`BranchSegment`, each option a child `CompiledGraph`); plain-node fan-out and multi-key fan-outs become `ParallelSegment`s whose branches are each a sub-graph. Order is a monotonically continuous counter (`Offset` is carried into downstream graphs, not reset to zero), and join registration is $O(\text{inputs})$ per join point. Static pruning (`MarkStoppedBranch` lines 281-295) walks a skipped branch's topology once to stamp `Order = -1`; it too is `Visited`-guarded.
- **Terminal** (`CompilerViewModel.Reverse.cs`): `BuildAncestorConeAsync` (lines 33-74) is a reverse BFS over `Sources` with the same per-edge `AccessAsync` gate — $O(V + E)$ over the cone. `CompileConeAsync` (lines 82-134) derives the entry frontier, then delegates to the same forward walk restricted to the cone; routers keep real `BranchSegment` semantics with only the in-cone branch compiled (`RestrictRouteToCone` lines 303-325).

Space is $O(V + E)$ for the segment trees plus the visited set and cone.

## Compiled-graph outline (`CompiledOutline.Of`)

One depth-first walk, one row per segment, with each chain's label built by joining node type names:

$$
T_{\text{outline}} = O(V + E_s), \qquad S_{\text{outline}} = O(E_s)
$$

$E_s$ = the number of segments. It is computed **once** — a compiled graph is frozen after compilation, so nothing has to keep a flat view in step with it. The label join over a chain of $N$ nodes is $O(N)$ string concatenation, so the total is still $O(V)$.

## Sequential Execution (`RuntimeEngine.RunAsync`)

`RunAsync` (lines 52-128) iterates a graph's segments one pass at a time; the per-segment cost is the sum of its driven nodes:

| Segment | Cost |
|---|---|
| `ChainSegment` | $O(N_{\text{chain}})$ — one pass over the linear segment, awaiting each `ReceiveAsync` and writing `context.Data` |
| `BranchSegment` | $O(N_{\text{branch}})$ — a static branch is chosen by the compile-time locked `CompileKey` in $O(1)$ (option scan); a dynamic branch pays one `ResolveRouteKey` plus a linear scan over `Options` |
| `ParallelSegment` | $\sum_{\text{branches}} O(N_{\text{branch}})$ — branches are **started concurrently** but the wall-clock saving is only real for I/O-bound branches, because they share one thread |

Each `DriveAsync` (lines 412-506) is $O(1)$ bookkeeping plus the node's own work: it injects the session into `IRuntimeAware` nodes, sets `CurrentOrder`, and when the node is a multi-input join point it boxes the grouped inputs into an `IGroupData` by calling `CollectGroupedInputs` — a dictionary build over the registered input sources, $O(\text{inputs})$, pre-sized to avoid reallocations.

Over the whole graph with $N$ driven nodes:

$$
T_{\text{execute}} = \sum_{i=1}^{N} T_{\text{work}}(i) = O(N)
$$

in the number of nodes (wall-clock time is dominated by node workloads, e.g. `Task.Delay` in demos).

### Fan-out with a concurrency cap

A `ParallelSegment` with $B$ branches and cap $c$ runs in $\lceil B/c \rceil$ waves; the semaphore costs $O(1)$ per branch (one `WaitAsync` / `Release` pair):

$$
T_{\text{fan-out}} = \frac{1}{c}\sum_{j=1}^{B} T_{\text{branch}}(j) \quad (\text{bounded by } \lceil B/c \rceil \text{ waves}), \qquad S_{\text{fan-out}} = O(B)
$$

`c = null` means $c = B$ (fully overlapped); `c = 1` degenerates to the sequential cost. The space is the per-branch `BranchRuntimeContext` array plus one `Task<bool>` per branch — note that **all $B$ tasks are created up front** (`new Task<bool>[count]`), so the cap bounds concurrent *work*, not the number of started tasks.

### Redirect

Redirects re-run the whole graph toward a target Order, skipping the contract-preserved prefix (`Order < target`); with at most 50 redirects (`MaxRedirects`):

$$
T_{\text{redirect}} = O(50 \cdot N)
$$

Each pass also re-walks the segment list, so the constant includes the segment count.

## Checkpointing

| Operation | Time | Space |
|---|---|---|
| `ExecutionCheckpoint.NodesOf(graph)` (once per run) | $O(V)$ | $O(V)$ |
| `RuntimeContext.Snapshot()` (after each success) | $O(R)$ — $R$ = registered outputs, ≤ $V$ | $O(R)$ |
| `SaveAsync` on `InMemoryCheckpointStore` | $O(1)$ (a reference swap under a lock) | $O(R)$ retained |
| `SaveAsync` on `FileCheckpointStore` | $O(R)$ — JSON write, serialised behind a semaphore | $O(R)$ |
| `RequireSameShape` (once per resume) | $O(\min(V, |\text{Shape}|))$ | $O(1)$ |
| `Restore` (once per resume) | $O(V)$ | $O(V)$ |
| `ExecutionCheckpoint.Rekey` (host-called) | $O(V + R)$ | $O(V + R)$ |

The snapshot cost is why the checkpoint is written **after each node** rather than after each pass: $O(R)$ per node against $O(V) \cdot$ nodes if recomputed wholesale.

`Snapshot()` is not free at scale if the payloads are large: it stores each completed output, and for a join it rewrites an `IGroupData` into a plain dictionary, costing $O(\text{inputs})$ per group payload.

## Host-capability overhead

Every seam is a `null` check plus, when configured, one call. With $N$ driven nodes:

| Seam | Per-node cost when configured |
|---|---|
| `IExecutionGate` | $O(1)$ — an `IsCompleted` check on an open gate (no allocation, no `Status` write); a `TaskCompletionSource` wait only while closed |
| `IExecutionObserver` | 2 calls per successful node (`NodeStarted`, `NodeSucceeded`) + 1 per branch + 2 per run |
| `INodeRetryPolicy` | 1 call **per thrown exception**, plus a `Task.Delay` |
| `IExecutionErrorSink` | 1 call per failure, 2 for a node throw (the node's own record, then the engine's decision) |
| `IExecutionCheckpointStore` | 1 snapshot + 1 save per successful node |
| `IExecutionCompensation` | 1 call per successfully driven node, but **only** when the outcome is `Failed` or `Cancelled` — 0 on a completed run |
| `ILogWriter` | $O(1)$ per line, inside `AppendLog` — counted in the node's own work |

With all of them unset the total added cost is $N$ null checks: the run behaves exactly as it did before the layer existed, which is the stated contract.

### Bounded and unbounded logs

`Logs` grows by $O(1)$ per line by default. With `MaxRetainedLogs = m`, the retention trim inside `AppendLog` is:

$$
T_{\text{trim}} = O(1) \text{ amortized per line}, \qquad S_{\text{Logs}} = O(m)
$$

Because at most one line is added per call, at most one `RemoveAt(0)` is needed — the `while` loop runs once. `SnapshotLogs()` is $O(|\text{Logs}|)$ with an array allocation, and is the only sanctioned way to read `Logs` across threads.

## Memory Usage Summary

| Structure | Space | Basis |
|---|---|---|
| `CompiledGraph` + segments | $O(V + E)$ | segment trees + visited set + cone |
| `CompiledOutline` rows | $O(E_s)$ | one row per segment |
| Runtime output registry | $O(\text{driven nodes})$ | pass-stamped `RegisterOutput` table |
| Completed-this-run list (for compensation) | $O(\text{successes})$ | one entry per node, moved not duplicated on a re-drive |
| Fan-out branch contexts | $O(B)$ | one `BranchRuntimeContext` + one task per branch |
| `ExecutionCheckpoint` | $O(V + R)$ | shape + types + outputs |
| `Logs` | $O(\text{lines})$, or $O(m)$ capped | `ObservableCollection<string>` + optional trim |
| Serialized graph snapshot | $O(P_{\text{graph}})$ | writer stops at the graph boundary |

## Summary Table

| Operation | Time | Space | Basis |
|---|---|---|---|
| Compile (`CompilerViewModel`, Root / Terminal) | $O(V+E)$ | $O(V+E)$ | remembered decomposition + reverse cone + visited set |
| `CompiledOutline.Of` | $O(V + E_s)$ | $O(E_s)$ | one depth-first walk, computed once |
| Execute segments (`RuntimeEngine`) | $O(N)$ | $O(N)$ | one pass over segments; join aggregation $O(\text{inputs})$ |
| Fan-out with cap $c$ over $B$ branches | $\lceil B/c \rceil$ waves | $O(B)$ | semaphore per group, all tasks started up front |
| Redirect worst case | $O(50 \cdot N)$ | $O(N)$ | `MaxRedirects = 50` |
| Snapshot + save a checkpoint | $O(R)$ | $O(R)$ | per successful node |
| Resume (`RequireSameShape` + `Restore`) | $O(V)$ | $O(V)$ | shape compare + output re-registration |
| Host capabilities, all unset | $O(N)$ null checks | $O(1)$ | the pre-2026-09-27 behavior, exactly |
