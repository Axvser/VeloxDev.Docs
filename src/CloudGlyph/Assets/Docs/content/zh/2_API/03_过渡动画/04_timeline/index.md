# 过渡动画 — 命名空间：`VeloxDev.TimeLine`

过渡系统的事件实参类型（源：`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`、`TransitionEventArgs.cs`）。`TimeLineEventArgs` 由其他由时间轴驱动的系统共享（`Tickable` 特性）；`TransitionEventArgs` 是过渡专属的。本命名空间的其余部分（`TickManager`、`TickableAttribute`、`FrameEventArgs`）属于 `tickable` 特性。

### 类：`TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
}
```

**说明：** `Handled` 是时间轴的终止开关 —— 默认 `false`，`true` 结束正在运行的时间轴。它被 `TransitionEventArgs` 继承，后者的实例作为 `ITransitionInterpreter<TPriorityCore>.Args` 呈现。

### 类：`TransitionEventArgs : TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public sealed class TransitionEventArgs : TimeLineEventArgs
{
    public string? Stage { get; init; }
    public string? Message { get; init; }
    public Exception? Exception { get; init; }
}
```

| 成员 | 说明 |
|---|---|
| `Stage` | 哪个回调或阶段报告的 —— `"Update"`、`"Finally"`、`"Sampling"`、`"Prepare"`、`"Run"` 等。 |
| `Message` | 降级阶段（一次 `Warn`）的人类可读文本。 |
| `Exception` | 失败阶段（一次 `Error`）逃逸出来的异常。 |

**说明：**
- 传给每个 `ITransitionEffectCore` 事件处理器（`EventHandler<TransitionEventArgs>`）与触发器（`InvokeAwake` … `InvokeFinally`、`InvokeWarn`、`InvokeError`）的密封事件实参类型。
- 在 effect 事件处理器里把 `e.Handled` 置 `true` 会短路采样循环：解释器抛 `OperationCanceledException`，随后触发 `Canceled`，再触发 `Finally`（见 [abstractions](../01_abstractions/01_引擎/index.md)）。取消的 `CancellationTokenSource` 效果相同。
- 三个描述性成员是 `init` 专用的，为**诊断**通道填充：一趟降级但仍继续时引擎触发 `Warn`（某帧被丢弃、某路径因目标运行时类型不符被跳过、属性无采样器、`Awake` 被拒绝），某阶段失败时触发 `Error`（回调、采样器、宿主派发或 `Prepare` 抛异常）。经 `Warn` / `Error` 处理器触发时置 `Handled = true` 即终止该趟。七个生命周期事件让这三个成员保持 `null`。
- *核验：* `SamplingLoopTests`（`HandledBeforeStart_CancelsAndFiresFinally`）、`TransitionEffectCoreTests`（`Events_AreInvoked`）、`TransitionDiagnosticsTests`。
