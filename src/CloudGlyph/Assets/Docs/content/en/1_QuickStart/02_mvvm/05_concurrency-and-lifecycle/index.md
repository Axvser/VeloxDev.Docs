# MVVM — Concurrency, Cancellation & Lifecycle

`VeloxDev.MVVM.VeloxCommand` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the runtime behind every generated command. It is a thread-safe, UI-agnostic async command: it serializes or parallelizes executions, supports cooperative cancellation per run, and reports every transition through a lifecycle-event stream.

## 1. Lifecycle events

`IVeloxCommand` exposes eight events, all typed `CommandEventHandler` (delegate `void CommandEventHandler(CommandEventArgs e)`). `CommandEventArgs` carries `Parameter`, `EventType` (`CommandEventType`), `Exception` (on failure) and `Cts`.

| Event | Meaning |
|---|---|
| `Created` | an execution request was received |
| `Enqueued` | capacity is full — the request is waiting in the FIFO queue |
| `Dequeued` | a queued request left the queue and is about to run |
| `Started` | the wrapped method actually began |
| `Completed` | the method returned normally |
| `Failed` | the method threw (non-cancellation) — `e.Exception` holds it |
| `Canceled` | the run was cancelled (see below) |
| `Exited` | the run finished and left the active set |

`CanExecuteChanged` (the standard `ICommand` event) is raised separately after each execution request and after each run completes, so bound controls re-query `CanExecute`.

**Normal, capacity-free sequence:** `Created → Started → Completed → Exited`.
**Queued sequence:** `Created → Enqueued` … then when a slot frees `Dequeued → Started → Completed → Exited`.

**Expected result:** subscribing `cmd.Started += e => ...` and `cmd.Completed += e => ...` observes `Started` before the method body runs and `Completed` after it returns; an exception inside the body raises `Failed` (with `e.Exception`) instead of `Completed`.

## 2. Serial vs parallel execution (`semaphore`)

`ExecuteAsync` checks a concurrency budget (`_maxConcurrency`, from the attribute's `semaphore`, default `1`):

- `_active.Count < semaphore` → the run starts immediately.
- otherwise → the request is enqueued (`Enqueued`) and started later (`Dequeued`) when an active run exits.

So with `semaphore: 1` every trigger is executed exactly once, in FIFO order — a second trigger while the first is running is **queued, not lost or coalesced**. With `semaphore: 3` up to three bodies may run in parallel; the 4th enqueues.

**Expected result:** firing `Execute` ten times quickly on a `semaphore: 1` command whose body takes 100 ms yields ten sequential executions of the body; with `semaphore: 3` three overlap at a time. Raising `ChangeSemaphore(2)` later adjusts the budget live.

## 3. Per-run cancellation

Each run of a method that takes a `CancellationToken` gets its **own** `CancellationTokenSource` (created inside `ExecuteAsync`), so tokens are never shared across queued runs. The wrapper watches the body: an `OperationCanceledException` surfaces as a `Canceled` event, never as `Failed`.

For method signatures *without* a token the runtime still tracks the run but cannot cooperatively cancel the body — `Canceled` is raised and the run is dropped, yet the body itself keeps going until it returns.

**Expected result:** a body that `await Task.Delay(Timeout.Infinite, ct)` raises `Canceled` (not `Failed`) when its token is cancelled.

## 4. Lock / interrupt / clear / continue

| API (sync / async) | Effect |
|---|---|
| `Lock()` / `LockAsync()` | enters a force-locked state: `CanExecute` returns `false` and new requests are cancelled immediately; running work is untouched |
| `UnLock()` / `UnLockAsync()` | leaves the locked state and starts any queued work |
| `Interrupt()` / `InterruptAsync()` | locks, then cancels the currently running runs (`Canceled`) |
| `Clear()` / `ClearAsync()` | locks, drops the whole queue (`Dequeued` + `Canceled` per pending item) and cancels the active runs |
| `Continue()` / `ContinueAsync()` | starts pending work if not locked |
| `ChangeSemaphore(n)` / `ChangeSemaphoreAsync(n)` | changes the concurrency budget (ignored if `< 1`) and starts pending work |
| `Notify()` | raises `CanExecuteChanged` so bound controls re-run the `CanExecute` predicate |

The WPF demo shows both calling styles (`FreeCommand` fire-and-forget vs `FreeCommandAsync` awaitable).

**Expected result:** after `MinusCommand.Lock()`, `MinusCommand.Execute(null)` immediately produces a `Canceled` event and the body never runs; `MinusCommand.Clear()` empties a saturated queue; `Notify()` after a state change flips a disabled bound button to enabled (as in the properties/commands pages).

## 5. Thread & dispatch notes

- **Thread-safe runtime:** all internal state (`_pendingQueue`, `_active`, `_isForceLocked`, `_maxConcurrency`) is guarded by a private `SemaphoreSlim`; internal awaits use `ConfigureAwait(false)`. You may call `ExecuteAsync` / `LockAsync` / … from any thread, and `await` them from a UI thread without deadlock.
- **No auto-marshalling:** VeloxDev does not inject a dispatcher. Where a command body starts and where the events fire depends on the caller's context. Bound WPF/Avalonia commands start on the UI thread, so a body's own `await` continuations resume on that thread via its `SynchronizationContext`; a body that was started on a background thread (or whose awaited task completes on the pool) resumes there. If such a continuation touches UI-bound state, marshal it yourself with the host dispatcher (`Dispatcher.InvokeAsync` in WPF, Avalonia's `Dispatcher`).

**Expected result:** a command that does pure compute can run entirely on a background thread with no UI reference; a command that updates observable properties read by the UI completes those updates on the UI thread when it was invoked from the UI.

## Run declaration

- ⚠️ Statically verified only — no compilation or execution was run while writing this page. Event order and the lock/interrupt/clear/continue semantics come from `VeloxDev.Core/MVVM/VeloxCommand.cs`; the demo calling styles come from `Examples/MVVM/*/.../MainWindowViewModel.cs`.
