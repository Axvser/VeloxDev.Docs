# MonoBehaviour — `ThreadSafeFrameEventArgs`

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    public new bool Handled { get; set; }
}
```

#### `ThreadSafeFrameEventArgs.Handled`

**Signature:**
`public new bool Handled { get; set; }`

**Returns:** `bool` — lock-protected, safe to read/write across the Update and FixedUpdate threads.

**Notes:**
- Backed by a `lock` inside the property accessors (verified by `TimeLineEventArgsTests.ThreadSafeFrameEventArgs_Handled_ThreadSafe`).
