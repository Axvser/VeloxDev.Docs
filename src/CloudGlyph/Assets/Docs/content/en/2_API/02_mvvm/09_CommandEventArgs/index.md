# MVVM — `CommandEventArgs`

`VeloxDev.MVVM.CommandEventArgs` (`Src/Core/VeloxDev.Core/MVVM/VeloxCommand.cs`) is the payload carried by every command lifecycle event. `VeloxCommand` is the only producer; it is handed to `CommandEventHandler` subscribers and stored in the command's internal pending/active queues.

## Class: `CommandEventArgs`

**Signature**

```csharp
public sealed class CommandEventArgs(
    object? parameter,
    CommandEventType type,
    Exception? ex = null,
    CancellationTokenSource? cts = null)
{
    public object? Parameter { get; } = parameter;
    public Exception? Exception { get; } = ex;
    public CommandEventType EventType { get; } = type;

    // internal — not part of the public surface
    internal CancellationTokenSource? Cts { get; set; }
    internal CancellationTokenSource? TakeCts();
    internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }
    internal bool TryMarkCancelReported();
    internal void Complete(CommandOutcome outcome, Exception? exception);

    public CommandEventArgs With(CommandEventType newType, Exception? ex = null);
}
```

**Sealed:** yes.

##### Properties

| Name | Type | Access | Description |
|---|---|---|---|
| `Parameter` | `object?` | get | The argument passed to `Execute` / `ExecuteAsync`. Every stage of one execution carries the same value. |
| `Exception` | `Exception?` | get | The failure that ended the execution, on `Failed` only; `null` on every other stage, including `Exited`. |
| `EventType` | `CommandEventType` | get | The stage this instance reports. |
| `Cts` | `CancellationTokenSource?` | **internal** get / set | The execution's cancellation source; `null` when the command's body never receives a token. Deliberately not public: the command disposes it when the execution ends, so exposing it would let a handler read a source that is expiring. |

##### Methods

###### `CommandEventArgs.With`

**Signature:**
`CommandEventArgs With(CommandEventType newType, Exception? ex = null)`

| Parameter | Type | Description |
|---|---|---|
| `newType` | `CommandEventType` | The stage to report. |
| `ex` | `Exception?` | The failure the new instance should carry. When omitted, the receiver's own failure is kept instead. Optional. |

**Returns:** `CommandEventArgs` — a new instance that keeps `Parameter` and `Cts`, and takes the given exception or falls back to the receiver's.

**Example:**

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandEventArgsTests.cs, lines 36-46
var boom = new InvalidOperationException("boom");
var other = new InvalidOperationException("other");
var args = new CommandEventArgs(null, CommandEventType.Failed, ex: boom);

Assert.AreSame(boom, args.With(CommandEventType.Exited).Exception,
    "With projects the whole instance, so an omitted failure falls back to the receiver's");
Assert.AreSame(other, args.With(CommandEventType.Exited, other).Exception);
```

```csharp
// Source: Test — Src/Core/VeloxDev.Core.Test/MVVM/CommandEventArgsTests.cs, lines 14-25
using var cts = new CancellationTokenSource();
var args = new CommandEventArgs("payload", CommandEventType.Created, cts: cts);

var next = args.With(CommandEventType.Started);

Assert.AreEqual("payload", next.Parameter, "every stage of one execution carries the same argument");
Assert.AreSame(cts, next.Cts, "and the same cancellation source");
```

**Notes:**

- `With` never mutates the receiver; it projects onto a new instance.
- The command itself never hits the exception fallback: it projects from the execution's origin instance, which is created without an exception and never mutated, so `Failed` is the only stage that comes out carrying one.
- The copy `With` produces does **not** carry the internal `Completion` slot — a copy must not be able to complete the awaiting caller.

##### Internal members

These are declared on the type but are not usable from consumer code:

| Member | Signature | Purpose |
|---|---|---|
| `Cts` | `internal CancellationTokenSource? Cts { get; set; }` | The execution's cancellation source. |
| `TakeCts` | `internal CancellationTokenSource? TakeCts()` | `Interlocked.Exchange(ref _cts, null)` — exactly one caller wins, and that caller owns disposal. |
| `Completion` | `internal TaskCompletionSource<CommandCompletion>? Completion { get; set; }` | The wait slot; only `ExecuteAndWaitAsync` attaches one. |
| `TryMarkCancelReported` | `internal bool TryMarkCancelReported()` | First caller wins, so one execution reports at most one `Canceled`. |
| `Complete` | `internal void Complete(CommandOutcome outcome, Exception? exception)` | Finishes the wait exactly once; a no-op when nobody is waiting. |

## Notes

- The same physical execution is described by several `CommandEventArgs` instances over its lifetime, from `Created` through to `Exited`, each produced by `With`.
- Because `Cts` is internal, a consumer that needs to cancel a run must go through `Interrupt` / `Clear` rather than reaching for the token source.
