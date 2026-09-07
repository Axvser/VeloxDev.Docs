# MonoBehaviour — `TransitionEventArgs`

命名空间 `VeloxDev.TimeLine`。与过渡系统共享的标记型事件参数类型。

```csharp
namespace VeloxDev.TimeLine;

public sealed class TransitionEventArgs : TimeLineEventArgs
{
}
```

#### `TimeLineEventArgs.Handled`（继承）

**签名：**

`public virtual bool Handled { get; set; }`

**返回：** `bool` — 自 `TimeLineEventArgs` 原样继承。

**说明：**

- `TransitionEventArgs` 不新增任何成员，仅作为标记类型。`Handled` 默认 `false`，可置为 `true`（由 `TimeLineEventArgsTests.TransitionEventArgs_Handled_DefaultFalse` 与 `TimeLineEventArgsTests.TransitionEventArgs_Handled_SetTrue` 验证）。

**源码：**

`Src/Core/VeloxDev.Core/TimeLine/TransitionEventArgs.cs`
