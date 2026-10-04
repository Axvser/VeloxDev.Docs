# `ThreadSafeFrameEventArgs`

命名空间 `VeloxDev.TimeLine`。程序集 `VeloxDev.Core`。

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
```

源码：`Src/Core/VeloxDev.Core/TimeLine/ThreadSafeFrameEventArgs.cs`。

`Handled` 属性由锁保护的 `FrameEventArgs`，供「从运行钩子的线程之外设置该标志」的宿主使用。

#### 属性：`ThreadSafeFrameEventArgs.Handled`

**签名：**
`public new bool Handled { get; set; }`

**返回：** `bool` —— 受锁保护的标志，默认 `false`。**异常：** 无。

**示例：**
```text
// 源码：Src/Core/VeloxDev.Core.Test/TimeLine/TimeLineEventArgsTests.cs（第 48-63 行）
var args = new ThreadSafeFrameEventArgs();
var tasks = new List<Task>();
for (int i = 0; i < 100; i++)
{
    tasks.Add(Task.Run(() =>
    {
        args.Handled = true;
        _ = args.Handled;
        args.Handled = false;
    }));
}
Task.WaitAll(tasks.ToArray());
// 没有异常 = 线程安全访问成立
```

**说明：**
- 声明用的是 **`new`**，不是 `override`。这是关键细节：基类的 `Handled` 是 `virtual`，但这个类型是遮蔽而不是重写。因此通过 `FrameEventArgs` 引用去读一个 `ThreadSafeFrameEventArgs`，解析到的是**基类那个未同步**的属性。要么用静态类型，要么这把锁白加。

```csharp
FrameEventArgs baseRef = new ThreadSafeFrameEventArgs();
baseRef.Handled = true;      // 写的是 FrameEventArgs.Handled —— 没有同步

ThreadSafeFrameEventArgs own = new ThreadSafeFrameEventArgs();
own.Handled = true;          // 写的是带锁的那个属性
```

- **帧循环从不构造这个类型。** `LoopChannel.CreateFrameEventArgs` 从 `_frameEventArgsPool` 取的是普通 `FrameEventArgs`，交给钩子的就是它。没有任何公开选项能让通道改用线程安全变体。它存在的意义是给「自建事件参数并自行派发」的宿主。
- 由于框架不使用它，它与池化、与 `Handled` 的每帧阶段重置、与固定泵的每步参数都没有任何交互。
- `DeltaTime`、`TotalTime`、`CurrentFPS`、`TargetFPS` 保持基类的 `internal` setter —— 这个线程安全类型没有增加任何可写的时间属性。
