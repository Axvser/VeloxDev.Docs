# MonoBehaviour — `ThreadSafeFrameEventArgs`

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    public new bool Handled { get; set; }
}
```

#### `ThreadSafeFrameEventArgs.Handled`

**签名：**
`public new bool Handled { get; set; }`

**返回：** `bool` — 加锁保护，可在 Update 与 FixedUpdate 线程间安全读写。

**说明：**
- 属性访问器内部以 `lock` 实现（由 `TimeLineEventArgsTests.ThreadSafeFrameEventArgs_Handled_ThreadSafe` 验证）。
