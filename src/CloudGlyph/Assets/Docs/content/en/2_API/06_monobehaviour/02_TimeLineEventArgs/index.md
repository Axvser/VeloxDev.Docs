# MonoBehaviour — `TimeLineEventArgs`

```csharp
public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
}
```

#### `TimeLineEventArgs.Handled`

**Signature:**
`public virtual bool Handled { get; set; }`

**Returns:** `bool` — `true` short-circuits the remaining behaviours of the current frame phase.

**Notes:**
- Default `false` (verified by `TimeLineEventArgsTests`).
