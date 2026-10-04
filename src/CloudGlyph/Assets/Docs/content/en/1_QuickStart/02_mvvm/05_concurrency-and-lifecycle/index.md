# MVVM — Concurrency, Cancellation and Lifecycle

`VeloxDev.MVVM.VeloxCommand` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the runtime behind every generated command. It is a thread-safe, UI-agnostic async command: it serializes or parallelizes executions, supports cooperative cancellation per run, and reports every transition through a lifecycle-event stream.

## 1. The eight lifecycle events

Every event is typed `CommandEventHandler` — `void CommandEventHandler(CommandEventArgs e)`. `CommandEventArgs` exposes `Parameter`, `EventType` and `Exception` publicly; its per-execution `CancellationTokenSource` is **`internal`** and is not part of the public surface (see the API reference for the full member list).

| Event | Meaning |
|---|---|
| `Created` | an execution request was accepted |
| `Enqueued` | capacity is full — the request is waiting in the FIFO queue |
| `Dequeued` | a queued request left the queue and is about to run |
| `Started` | the wrapped method actually began |
| `Completed` | the method returned normally |
| `Failed` | the method threw — `e.Exception` holds it (and only this stage carries one) |
| `Canceled` | the run was cancelled, or the request was refused |
| `Exited` | the run finished and left the active set |

`CanExecuteChanged` is the standard `ICommand` event and is raised separately.

**Sequences:**

- immediate: `Created → Started → Completed → Exited`
- queued: `Created → Enqueued` … then, when a slot frees, `Dequeued → Started → Completed → Exited`
- refused by a lock: `Created → Canceled` only — never `Started`, never `Exited`
- cancelled while running: `Created → Started → Canceled → Exited`

An execution reports at most **one** `Canceled`. Both `Interrupt`/`Clear` and the body's own `OperationCanceledException` would like to report one; the first to arrive wins, so a handler that counts `Canceled` per execution counts one.

**Expected result:** subscribing `cmd.Started += e => ...` and `cmd.Completed += e => ...` observes `Started` before the body runs and `Completed` after it returns; an exception inside the body raises `Failed` with `e.Exception` instead of `Completed`; `e.Exception` stays `null` on every other stage, including `Exited` — do not treat `Exited` as a success signal.

## 2. Serial vs parallel execution

Execution is bounded by a concurrency capacity (`_maxConcurrency`, from the attribute's `semaphore`, default `1`):

- `_active.Count < capacity` → the run starts immediately.
- otherwise → the request is enqueued (`Enqueued`) and started later (`Dequeued`) when an active run exits.

With the default capacity every trigger runs exactly once, in FIFO order — a second trigger while the first is running is **queued, not dropped or coalesced**. `ChangeSemaphore(n)` adjusts the cap at run time and immediately drains whatever fits.

**Expected result:** firing ten executions at a capacity-1 command whose body takes 100 ms yields ten sequential body runs; at capacity 3, three overlap. Raising the cap later starts the queued backlog. A capacity below 1 is rejected: the constructor and `ChangeSemaphoreAsync` throw `ArgumentOutOfRangeException`, and the synchronous `ChangeSemaphore` validates before dispatching for the same reason.

## 3. Per-run cancellation

Each run of a method that takes a `CancellationToken` gets its **own** `CancellationTokenSource`, disposed when that execution ends — including a queued call that `Clear` drops before it ever runs. Tokens are never shared across queued runs, and an `OperationCanceledException` surfaces as `Canceled`, never as `Failed`.

For method shapes *without* a token (parameterless bodies, `void` bodies, `Task M(object?)`) the runtime still tracks the run but cannot stop the body: `Canceled` is raised and the run is removed, yet the body keeps going until it returns.

**Expected result:** a body that awaits `Task.Delay(Timeout.Infinite, ct)` raises `Canceled` when interrupted; the equivalent parameter-only body raises `Canceled` too, but its own code continues to completion.

## 4. Lock, interrupt, clear, continue

| API (sync / async) | Effect |
|---|---|
| `Lock()` / `LockAsync()` | enter the force-locked state: `CanExecute` returns `false` and new requests are refused (`Created → Canceled`); running work is untouched |
| `Unlock()` / `UnlockAsync()` | leave the locked state and start whatever the queue can now hold |
| `Interrupt()` / `InterruptAsync()` | cancel the currently running executions; a command that was already locked stays locked |
| `Clear()` / `ClearAsync()` | drop the whole queue (`Dequeued` then `Canceled` per pending item) and cancel the active executions |
| `Continue()` / `ContinueAsync()` | start pending work — a no-op while locked |
| `ChangeSemaphore(n)` / `ChangeSemaphoreAsync(n)` | change the capacity (`< 1` throws) and start pending work |
| `Notify()` | raise `CanExecuteChanged` so bound controls re-run the `CanExecute` predicate |

The synchronous members are fire-and-forget conveniences over their `Async` twins. Note the spelling: the member is **`Unlock`**, not `UnLock`.

The WPF demo shows both calling styles — `FreeCommand` (fire-and-forget) next to `FreeCommandAsync` (awaitable) — against `MinusCommand`.

**Expected result:** after `MinusCommand.Lock()`, `MinusCommand.Execute(null)` produces `Created → Canceled` and the body never runs; `MinusCommand.Clear()` empties a saturated queue and leaves the command unlocked; `Notify()` after a state change flips a disabled bound button to enabled.

## 5. Threads, dispatch and broken subscribers

- **Thread-safe:** all internal state (`_pendingQueue`, `_active`, `_isForceLocked`, `_maxConcurrency`) is guarded by a private `SemaphoreSlim(1,1)`, and internal awaits use `ConfigureAwait(false)`. No user code runs while that lock is held, so a handler that blocks on the command cannot deadlock it.
- **`EventContext`** — by default events are raised inline, on whatever thread the pipeline is on, so a handler that touches UI must dispatch itself. Setting `EventContext` to the UI framework's `SynchronizationContext` makes the command post them there instead, in lifecycle order. Posting is asynchronous: an event can reach its handler after the call that raised it returned.
- **`HandlerException`** — a subscriber that throws never disturbs the command, and the exception is swallowed. `VeloxCommand.HandlerException` is a static event that reports those failures (this holds for `CanExecuteChanged` subscribers too). With nothing subscribed the behaviour is exactly as if the event did not exist, and a hook that itself throws is discarded rather than propagated.
- **`Dispose()`** — releases the command's internal lock. Use it only at teardown, once nothing is in flight; a command that is merely dropped needs no disposal. Disposal is final.

**Expected result:** with `EventContext` unset, a UI-touching handler runs on the pipeline's thread; with it set, handlers run on the context's thread in lifecycle order; a handler that throws produces `Completed` (not `Failed`) and, if `HandlerException` is subscribed, reports the exception there.

## Run declaration

- ✅ Partially executed on 2026-10-01. The lifecycle and lock behaviour was exercised against a scratch console project built with a Debug project reference to `VeloxDev.Core` (`dotnet run -c Debug`, recorded output):

  ```text
  Increment -> Completed (Succeeded=True)
  Decrement -> Completed
  status: IsBusy=False, Active=0, Pending=0
  while locked -> Refused
  ```

  The third and fourth lines are the observable consequence of sections 2 and 4: the counter is idle after both commands finish, and a call issued while `LockAsync()` is held is refused.

- Event ordering, the single-`Canceled` rule, disposal of the per-execution source, and the `EventContext` posting path were **not** executed in this pass. They are transcribed from `VeloxCommand.cs` and are pinned by `Src/Core/VeloxDev.Core.Test/MVVM/` (`VeloxCommandLifecycleTests`, `VeloxCommandCancellationTests`, `VeloxCommandDisposalTests`, `VeloxCommandEventContextTests`, `VeloxCommandDiagnosticsTests`, `VeloxCommandControlTests`, `VeloxCommandConcurrencyTests`, `VeloxCommandLockInvariantTests`).
