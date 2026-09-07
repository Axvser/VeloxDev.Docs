# MonoBehaviour — `ThreadSafeFrameEventArgs`

命名空间 `VeloxDev.TimeLine`。`FrameEventArgs` 的子类，其 `Handled` 标志可在 Update 与 FixedUpdate 线程间安全地并发读写。

```csharp
namespace VeloxDev.TimeLine;

public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    public new bool Handled { get; set; }
}
```

### `ThreadSafeFrameEventArgs.Handled`

**签名：**

`public new bool Handled { get; set; }`

**返回：** `bool` — 受 `lock` 保护的 `Handled` 值，跨线程读写均为原子操作。

**说明：**

- 用 `new` 关键字隐藏从 `TimeLineEventArgs` 继承的 `virtual Handled`；访问器在每次 get / set 时对私有对象加锁。
- 其余成员（`DeltaTime`、`TotalTime`、`CurrentFPS`、`TargetFPS`）原样继承自 `FrameEventArgs`。
- 线程安全由 `TimeLineEventArgsTests.ThreadSafeFrameEventArgs_Handled_ThreadSafe` 验证（100 个并发任务读写而不抛异常）。

**源码：**

`Src/Core/VeloxDev.Core/TimeLine/ThreadSafeFrameEventArgs.cs`
