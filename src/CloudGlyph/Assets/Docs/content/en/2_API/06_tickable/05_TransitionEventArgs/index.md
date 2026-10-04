# `TransitionEventArgs`

Namespace `VeloxDev.TimeLine`. Assembly `VeloxDev.Core`.

```csharp
public sealed class TransitionEventArgs : TimeLineEventArgs
```

Source: `Src/Core/VeloxDev.Core/TimeLine/TransitionEventArgs.cs`.

A failure/signal payload shared by the transition system. It lives in the `TimeLine` folder and derives from `TimeLineEventArgs`, which is why it is listed here — it is part of the same argument family, but it is not produced by the tickable feature and no `TickManager` API mentions it.

#### Property: `TransitionEventArgs.Stage`

**Signature:**
`public string? Stage { get; init; }`

**Returns:** `string?` — which callback or stage reported the event. The source documents the expected values as `"Update"`, `"Finally"` and `"Sampling"`.

**Notes:**
- `init`-only, so it can be set in an object initializer but not afterwards.

#### Property: `TransitionEventArgs.Message`

**Signature:**
`public string? Message { get; init; }`

**Returns:** `string?` — a human-readable description of the event. May be `null`.

#### Property: `TransitionEventArgs.Exception`

**Signature:**
`public Exception? Exception { get; init; }`

**Returns:** `Exception?` — the exception the event is reporting, when there is one. May be `null`, which is the normal case for a non-failure signal.

#### Property: `TransitionEventArgs.Handled`

**Signature:**
`public virtual bool Handled { get; set; }`

**Returns:** `bool` — inherited unchanged from `TimeLineEventArgs`, `false` by default. This type does not override it.

**Example:**
```text
// Source: Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs (lines 11-23)
var args = new TransitionEventArgs();
Assert.IsFalse(args.Handled);

args = new TransitionEventArgs { Handled = true };
Assert.IsTrue(args.Handled);

// The init-only members, used the same way:
var reported = new TransitionEventArgs { Stage = "Update", Message = "requested rate is negative" };
```

**Notes:**
- `sealed`, so it cannot be extended to carry more.
- See the transition feature's API reference for the call sites that raise it; nothing in the tickable feature constructs or consumes one.
