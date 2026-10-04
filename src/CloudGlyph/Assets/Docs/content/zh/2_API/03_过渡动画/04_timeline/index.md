# 过渡动画 — 命名空间：`VeloxDev.TimeLine`

过渡系统从 `VeloxDev.TimeLine` 命名空间只继承一个类型：`TimeLineEventArgs`，它是每一种过渡载荷的抽象基类。它由其他由时间轴驱动的系统（`Tickable` 特性）共享，并随 [TimeLineEventArgs](../../06_Tickable/02_TimeLineEventArgs/index.md) 完整记录。过渡专属的载荷 —— `TransitionEventArgs`、带类型的 `TransitionEventArgs<TStage, TValue>` 以及 `WarnStage` / `ErrorStage` 枚举 —— 已**移出**本命名空间，进入 `VeloxDev.TransitionSystem`；它们记录在[事件参数](../00_transitionsystem/04_过渡事件参数/index.md)。本命名空间的其余部分（`TickManager`、`TickableAttribute`、`FrameEventArgs`）属于 `tickable` 特性。

源码：`Src/Core/VeloxDev.Core/TimeLine/TimeLineEventArgs.cs`。

### 类：`TimeLineEventArgs`

```csharp
namespace VeloxDev.TimeLine;

public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; } = false;
    public TimeSpan DeltaTime { get; internal set; } = TimeSpan.Zero;
    public TimeSpan TotalTime { get; internal set; } = TimeSpan.Zero;
}
```

| 成员 | 说明 |
|---|---|
| `Handled` | 时间轴的终止开关 —— 默认 `false`，为 `true` 即结束正在运行的时间轴。唯一可写的成员。 |
| `DeltaTime` | 距上一帧的时间。`internal` setter；解释器每个采样写一次。 |
| `TotalTime` | 自当前段开工以来的累计（不随趟重置 —— 「第几趟」由 `TransitionEventArgs.Loop` 回答）。`internal` setter。 |

**说明：**
- `TransitionEventArgs` 派生自它，也就是 `ITransitionInterpreter<TPriorityCore>.Args` 暴露出来的对象；整趟运行共用一个实例，每帧被重新盖章。
- 在效果事件处理器里置 `e.Handled = true` 会短路采样循环：解释器抛出 `OperationCanceledException`，随后触发 `Canceled`，再触发 `Finally`（见 [abstractions](../01_abstractions/01_引擎/index.md)）。取消一个 `CancellationTokenSource` 效果相同。
- 诊断通道是分开的：运行降级后继续的 stage，引擎经 `TransitionEventArgs<WarnStage, string>` 触发 `Warn`；失败的 stage 经 `TransitionEventArgs<ErrorStage, Exception>` 触发 `Error`。在任一处理器里置 `Handled = true` 即请求终止这趟运行。见[事件参数](../00_transitionsystem/04_过渡事件参数/index.md)。
- *由以下测试验证：* `TimeLineEventArgsTests`、`SamplingLoopTests`（`HandledBeforeStart_CancelsAndFiresFinally`）、`TransitionDiagnosticsTests`。
