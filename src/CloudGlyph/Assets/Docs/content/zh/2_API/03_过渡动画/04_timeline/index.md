# Transition — 命名空间：`VeloxDev.TimeLine`

过渡系统的事件参数类型（源码：`Src/Core/VeloxDev.Core/TimeLine/*.cs`）。`TimeLineEventArgs` 与其它时间线驱动系统（如 MonoBehaviour）共用；`TransitionEventArgs` 是过渡专属。

### 类：`TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
}
```

**说明：** `Handled` 是时间线的总开关——默认 `false`，设为 `true` 结束正在运行的时间线。它被 `TransitionEventArgs` 继承，后者实例以 `ITransitionInterpreterCore.Args` 暴露。

### 类：`TransitionEventArgs : TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public sealed class TransitionEventArgs : TimeLineEventArgs
{
}
```

**说明：**
- 传给每个 `ITransitionEffectCore` 事件处理器（`EventHandler<TransitionEventArgs>`）与调用器（`InvokeAwake` … `InvokeFinally`）的空密封事件参数类型。
- 在效果事件处理器内把 `e.Handled` 设为 `true` 会短路采样循环：解释器抛 `OperationCanceledException`，触发 `Canceled` 再触发 `Finally`（见 [01_abstractions](../01_abstractions/index.md)）。取消的 `CancellationTokenSource` 效果相同。
- *验证依据：* `SamplingLoopTests`（`HandledBeforeStart_CancelsAndFiresFinally`）、`TransitionEffectCoreTests`（`Events_AreInvoked`）。
