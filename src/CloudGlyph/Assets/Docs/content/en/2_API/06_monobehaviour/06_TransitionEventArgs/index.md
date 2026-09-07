# MonoBehaviour — `TransitionEventArgs`

Namespace `VeloxDev.TimeLine`. A marker event-arguments type shared with the transition system.

```csharp
namespace VeloxDev.TimeLine;

public sealed class TransitionEventArgs : TimeLineEventArgs
{
}
```

#### `TimeLineEventArgs.Handled` (inherited)

**Signature:**
`public virtual bool Handled { get; set; }`

**Returns:** `bool` — inherited unchanged from `TimeLineEventArgs`.

**Notes:**

- `TransitionEventArgs` adds no members; it is a marker type. `Handled` is `false` by default and can be set to `true` (verified by `TimeLineEventArgsTests.TransitionEventArgs_Handled_DefaultFalse` and `TimeLineEventArgsTests.TransitionEventArgs_Handled_SetTrue`).

**Source:**

`Src/Core/VeloxDev.Core/TimeLine/TransitionEventArgs.cs`
