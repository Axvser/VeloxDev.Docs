# MVVM — `CommandEventArgs`

`VeloxDev.MVVM.CommandEventArgs` (`Src/Core/VeloxDev.Core/MVVM/CommandEventArgs.cs`) is the payload carried by every non-generic command lifecycle event. `CommandEventArgs<TParam, TResult>` derives from it and adds the typed parameter and result.

## Class: `CommandEventArgs`

**Signature**

```csharp
public class CommandEventArgs(
    object? parameter,
    CommandEventType type,
    Exception? ex = null,
    CancellationTokenSource? cts = null)
{
    public virtual object? Parameter { get; } = parameter;
    public Exception? Exception { get; } = ex;
    public CommandEventType EventType { get; } = type;

    // internal — not part of the public surface
    internal CancellationTokenSource? Cts { get; set; }
    internal CancellationTokenSource? TakeCts();
    internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }
    internal bool TryMarkCancelReported();
    internal void Complete(CommandOutcome outcome, Exception? exception, object? result = null);

    public CommandEventArgs With(CommandEventType newType, Exception? ex = null);
}
```

**Sealed:** no — `CommandEventArgs<TParam, TResult>` derives from it.

##### Properties

| Name | Type | Access | Description |
| --- | --- | --- | --- |
| `Parameter` | `object?` | get (virtual) | The argument passed to `Execute` / `ExecuteAsync`. Every stage of one execution carries the same value. Reading it boxes a value type; the typed subclass overrides it. |
| `Exception` | `Exception?` | get | The failure that ended the execution, on `Failed` only; `null` on every other stage, including `Exited`. |
| `EventType` | `CommandEventType` | get | The stage this instance reports. |
| `Cts` | `CancellationTokenSource?` | **internal** get / set | The execution's cancellation source; `null` when the body never receives a token. Not public: the command disposes it when the execution ends. |

##### Methods

###### `CommandEventArgs.With`

**Signature:**
`CommandEventArgs With(CommandEventType newType, Exception? ex = null)`

| Parameter | Type | Description |
| --- | --- | --- |
| `newType` | `CommandEventType` | The stage to report. |
| `ex` | `Exception?` | The failure the new instance should carry. When omitted, the receiver's own failure is kept. |

**Returns:** `CommandEventArgs` — a new instance that keeps `Parameter` and `Cts`.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandEventArgsTests.cs
var boom = new InvalidOperationException("boom");
var other = new InvalidOperationException("other");
var args = new CommandEventArgs(null, CommandEventType.Failed, ex: boom);

Assert.AreSame(boom, args.With(CommandEventType.Exited).Exception);
Assert.AreSame(other, args.With(CommandEventType.Exited, other).Exception);
```

**Notes:**

- `With` never mutates the receiver; it projects onto a new instance.
- The command projects from the execution's origin instance, which is created without an exception, so `Failed` is the only stage that comes out carrying one.
- The copy `With` produces does **not** carry the internal `Completion` slot — a copy must not be able to complete the awaiting caller.

##### Internal members

| Member | Signature | Purpose |
| --- | --- | --- |
| `Cts` | `internal CancellationTokenSource? Cts { get; set; }` | The execution's cancellation source. |
| `TakeCts` | `internal CancellationTokenSource? TakeCts()` | `Interlocked.Exchange(ref _cts, null)` — exactly one caller wins and owns disposal. |
| `Completion` | `internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }` | The wait slot; only `ExecuteAndWaitAsync` attaches one. |
| `TryMarkCancelReported` | `internal bool TryMarkCancelReported()` | First caller wins, so one execution reports at most one `Canceled`. |
| `Complete` | `internal void Complete(CommandOutcome outcome, Exception? exception, object? result = null)` | Finishes the wait exactly once; a no-op when nobody is waiting. |

## The typed subclass

`CommandEventArgs<TParam, TResult>` is `sealed`. It adds:

| Member | Signature | Description |
| --- | --- | --- |
| `TypedParameter` | `TParam` | The argument in its own type; throws `InvalidCastException` if an `object?`-shaped entry point carried something else. |
| `TypedResult` | `TResult` | What the body returned, once the execution finished. |
| `Parameter` | `override object?` | The argument boxed only when actually read. |
| `With` | `new CommandEventArgs<TParam, TResult> With(...)` | Projects within the typed domain (covariant returns are unavailable on the older targets). |

See `16_typed-commands`.

## Notes

- The same physical execution is described by several `CommandEventArgs` instances over its lifetime, from `Created` through `Exited`.
- Because `Cts` is internal, a consumer that needs to cancel a run uses `Interrupt` / `Clear`.
