# MonoBehaviour — `TimeLineEventArgs`

命名空间 `VeloxDev.TimeLine`。TimeLine 系统派发的所有事件参数类型的抽象基类。它携带 `Handled` 标志——处理器可将其置为 `true` 以终止当前派发中剩余的处理。

```csharp
namespace VeloxDev.TimeLine;

public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
}
```

### `TimeLineEventArgs.Handled`

**签名：**

`public virtual bool Handled { get; set; }`

**返回：** `bool` — 默认 `false`；`true` 终止当前派发（帧阶段中剩余的行为被跳过）。

**说明：**

- 声明为 `virtual`：`FrameEventArgs` 原样继承，`ThreadSafeFrameEventArgs` 以加锁的 `new` 属性将其隐藏。
- 帧循环中管理器在每次行为调用后读取 `Handled`，为 `true` 即停止（见 `MonoBehaviourManager`）。
- 默认 `false`（由 `TimeLineEventArgsTests.FrameEventArgs_DefaultValues` 及 `TransitionEventArgs_Handled_*` 测试验证）。

**源码：**

`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`
