# MVVM — Concurrency, Cancellation and Lifecycle

`VeloxDev.MVVM.VeloxCommand` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the runtime behind every generated command. It derives from `CommandPipeline<object?, object?>` and is thread-safe and UI-agnostic: it serializes or parallelizes executions, supports cooperative cancellation per run, and reports every transition through a lifecycle-event stream.

## 1. The eight lifecycle events

Every event is typed `CommandEventHandler` (`void CommandEventHandler(CommandEventArgs e)`). `CommandEventArgs` exposes `Parameter`, `EventType` and `Exception` publicly; its per-execution `CancellationTokenSource` is internal.

| Event | Meaning |
| --- | --- |
| `Created` | an execution request was accepted |
| `Enqueued` | capacity is full; the request waits in the FIFO queue |
| `Dequeued` | a queued request left the queue and is about to run |
| `Started` | the wrapped method began |
| `Completed` | the method returned normally |
| `Failed` | the method threw; `e.Exception` holds it (and only this stage carries one) |
| `Canceled` | the run was cancelled, or the request was refused |
| `Exited` | the run left the active set |

`CanExecuteChanged` is the standard `ICommand` event and is raised separately.

**Sequences:**

- immediate: `Created → Started → Completed → Exited`
- queued: `Created → Enqueued`, then when a slot frees `Dequeued → Started → Completed → Exited`
- refused by a lock: `Created → Canceled` only — never `Started`, never `Exited`
- cancelled while running: `Created → Started → Canceled → Exited`

An execution reports at most **one** `Canceled`: `Interrupt` / `Clear` report promptly, and the body's later `OperationCanceledException` is suppressed.

**Expected result:** `Started` fires before the body and `Completed` after it; a body exception raises `Failed` (not `Completed`); `e.Exception` stays `null` on every other stage, including `Exited`.

## 2. Serial vs parallel execution

Capacity comes from the attribute's `semaphore` (default `1`).

- `_active.Count < capacity` → the run starts immediately.
- otherwise → the request is enqueued (`Enqueued`) and started later (`Dequeued`) when a slot frees.

A second trigger while the first runs is **queued, not dropped or coalesced**. `ChangeSemaphore(n)` adjusts the cap and immediately drains whatever fits.

**Expected result:** ten triggers at capacity 1 run ten times sequentially; at capacity 3, three overlap. A capacity below 1 throws `ArgumentOutOfRangeException` from the constructor and from both `ChangeSemaphore` overloads.

## 3. Per-run cancellation

Each run whose body takes a `CancellationToken` gets its own source, disposed when that execution ends — including a queued call dropped by `Clear`. An `OperationCanceledException` surfaces as `Canceled`, never `Failed`.

For shapes without a token the runtime still tracks the run but cannot stop the body: `Canceled` is raised and the run is removed, while the body continues to completion.

**Expected result:** a body awaiting `Task.Delay(Timeout.Infinite, ct)` reports `Canceled` on interrupt; the equivalent parameter-only body reports `Canceled` too, but its own code keeps running.

## 4. Lock, interrupt, clear, continue

| API (sync / async) | Effect |
| --- | --- |
| `Lock()` / `LockAsync()` | enter the force-locked state: `CanExecute` is `false` and new requests are refused (`Created → Canceled`); running work is untouched |
| `Unlock()` / `UnlockAsync()` | leave the locked state and start whatever the queue can hold |
| `Interrupt()` / `InterruptAsync()` | cancel the running executions; a command that was already locked stays locked |
| `Clear()` / `ClearAsync()` | drop the whole queue (`Dequeued` then `Canceled` per pending item) and cancel the active executions |
| `Continue()` / `ContinueAsync()` | start pending work — a no-op while locked |
| `ChangeSemaphore(n)` / `ChangeSemaphoreAsync(n)` | change the capacity (`< 1` throws) and start pending work |
| `Notify()` | raise `CanExecuteChanged` so bound controls re-run the predicate |

The synchronous members are fire-and-forget conveniences over their `Async` twins. The spelling is **`Unlock`**, not `UnLock`.

**Expected result:** after `Lock()`, `Execute(null)` produces `Created → Canceled` and the body never runs; `Clear()` empties a saturated queue; `Notify()` after a state change enables a previously disabled bound button.

## 5. Threads, dispatch and broken subscribers

- **Thread-safe.** Internal state is guarded by a private `SemaphoreSlim(1,1)`, and internal awaits use `ConfigureAwait(false)`. No user code runs while that lock is held.
- **`EventContext`** — events are raised inline by default, on whatever thread the pipeline is on. Setting it to a UI `SynchronizationContext` posts them there in lifecycle order. Posting is asynchronous: an event can reach its handler after the raising call returned.
- **`HandlerException`** — a subscriber that throws never disturbs the command; the exception is reported through the static `VeloxCommand.HandlerException` event and otherwise discarded. This also covers `CanExecuteChanged` subscribers.
- **`Dispose()`** — releases the internal lock. Use it only at teardown, once nothing is in flight. Disposal is final.

**Expected result:** with `EventContext` unset a handler runs on the pipeline's thread; with it set handlers run on the context's thread in order. A throwing handler still yields `Completed`, and the exception appears on `HandlerException` if subscribed.

## Run declaration

- ⚠️ Not actually run in this documentation pass — statically verified against `MVVM/CommandPipeline{TParam,TResult}.cs` and its test coverage in `Src/Core/VeloxDev.Core.Test/MVVM/` (`VeloxCommandLifecycleTests`, `VeloxCommandCancellationTests`, `VeloxCommandControlTests`, `VeloxCommandEventContextTests`, `VeloxCommandDiagnosticsTests`).
