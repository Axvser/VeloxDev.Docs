# 过渡动画 — 契约：效果、调度器、解释器、节奏

命名空间 `VeloxDev.TransitionSystem`。这些接口描述时间描述符、按目标的执行协调器、采样循环运行器，以及决定循环下一帧何时发生的抽象基类。每个泛型接口都把宿主的调度器优先级作为**类型参数**；宿主没有优先级的适配器（MAUI、WinForms、Razor）填 `NonPriority`。不存在无优先级的接口变体。

这些类型被交给的宿主与线程契约 —— `ITransitionHost<TPriorityCore>`、`IThreadDispatcher<TPriorityCore>`、`ThreadRef` —— 记录在 [host](../03_宿主/index.md)。

### 接口：`ITransitionEffectCore`

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `FPS` | `int FPS { get; set; }` | **最大采样率上限**，默认 `60`。让出间隔为 `1000 / FPS` 毫秒。计时由时间轴驱动的连续采样 —— `FPS` 约束的是循环多久采一次，*不是*帧栅格。 |
| `Duration` | `TimeSpan Duration { get; set; }` | 名义单趟时长；默认 `0`（零时长趟只采一次并直跳终点）。 |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` | 为 `true` 时每趟之后跟一趟反向。 |
| `LoopTime` | `int LoopTime { get; set; }` | 首趟之后重复的趟数；`int.MaxValue` = 无限循环。 |
| `Ease` | `IEaseCalculator Ease { get; set; }` | 施加在原始归一化时间上的缓动曲线。 |
| 事件 | `EventHandler<TransitionEventArgs>` | `Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally`、`Warn`、`Error`。 |
| 触发器 | `void Invoke*(object sender, TransitionEventArgs e)` | `InvokeAwake`、`InvokeStart`、`InvokeUpdate`、`InvokeLateUpdate`、`InvokeCompleted`、`InvokeCancled`、`InvokeFinally`、`InvokeWarn`、`InvokeError`（拼错的 `InvokeCancled` 是真实成员名）。 |
| `Clone` | `ITransitionEffectCore Clone()` | 深拷贝，同时克隆（弱）事件后备存储。 |

**说明：**
- 正常一趟的事件顺序：调度器在准备之前于 UI 线程触发 `Awaked`，随后循环触发一次 `Start`，然后每个采样触发 `Update` / `LateUpdate`，最后一趟之后触发 `Completed`。被取消的一趟触发 `Canceled`，而**每一条**结束路径（完成或取消）都触发 `Finally`。
- `Warn` 与 `Error` 是**诊断**通道，不是生命周期通道：当一趟降级但仍继续时（`Warn`：某一帧被丢弃、某条路径因目标运行时类型不符被跳过、属性无采样器、`Awake` 被拒绝），或某个阶段失败时（`Error`：回调、采样器、宿主派发或 `Prepare` 抛异常），引擎经 `Abstractions.TransitionDiagnostics` 触发它们。每个阶段每次运行**至多报告一次**，因此一个采不到值的属性不会以帧率刷屏。在 `Warn` / `Error` 实参上把 `Handled` 置 `true` 即要求终止该趟（`TransitionEventArgs.Stage` / `Message` / `Exception` 描述它 —— 见 [timeline](../../04_timeline/index.md)）。
- *核验：* `TransitionEffectCoreTests`（`Defaults_AreCorrect`、`Events_AreInvoked`、`Clone_CopiesProperties`、`EventRemove_StopsFiring`）、`SamplingLoopTests`（事件顺序断言）、`TransitionDiagnosticsTests`。

### 接口：`ITransitionEffect<TPriorityCore>`

在 `ITransitionEffectCore` 上增加带类型的优先级与协变克隆：

```csharp
public interface ITransitionEffect<TPriorityCore> : ITransitionEffectCore
{
    TPriorityCore Priority { get; set; }
    new ITransitionEffect<TPriorityCore> Clone();
}
```

**说明：** 适配器的 effect 设置具体优先级默认值（如 WPF/Avalonia 的 `DispatcherPriority.Render`、WinUI 的 `DispatcherQueuePriority.High`）；循环把 `Priority` 透传给采样集的 `Apply`。

### 接口：`ITransitionSchedulerCore`

```csharp
public interface ITransitionSchedulerCore
{
    Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**说明：**
- `Execute` 在调度器的目标上跑一趟已准备的动画：它 await `Awaked` 的派发（于是 `Awake` 在任何读取目标之前完成），准备 `SamplerSet<TPriorityCore>`，再交给解释器。`SemaphoreSlim` 门在**互斥**调度器上串行化执行（第二个动画会取消第一个）；`externCts` 让调用方提供自己的取消源。
- `Exit()` 取消该调度器当前跟踪的所有动画。
- 带类型的变体收窄 effect 形参：
  - `ITransitionScheduler<TPriorityCore> : ITransitionSchedulerCore` —— `Execute(InterpolatorCore, IFrameState, ITransitionEffect<TPriorityCore>, CancellationTokenSource? externCts = default)`。
  - `ITransitionScheduler : ITransitionSchedulerCore` —— 标记（无新成员）。
- 泛型实现由 `Abstractions.TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>` 提供，它额外的公开成员 `ExecuteCapturing` 与 `Replay` 支撑链的循环（见 [abstractions](../../01_abstractions/index.md)）。
- *核验：* `SamplingLoopTests`；WPF 演示 `RepeatMutual`（新的互斥动画取消前一个）；`AUTO TEST` `LoadModes_MatchTheLibrarySemantics`（并发与互斥登记的差别）。

### 接口：`ITransitionInterpreter<TPriorityCore>`

```csharp
public interface ITransitionInterpreter<TPriorityCore> : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, SamplerSet<TPriorityCore> samplerSet,
        ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts);
    void Exit();
}
```

**说明：**
- `Args` 是解释器驱动的事件实参实例；把 `Args.Handled` 置 `true` 会短路时间轴（循环抛 `OperationCanceledException` → `Canceled` + `Finally`）。
- `Execute` 针对已准备的 `SamplerSet<TPriorityCore>` 跑采样循环。`Exit()`（即 `Dispose` 的别名）取消当前活动的 `CancellationTokenSource`。
- 解释器是**单一、带优先级**的接口：没有调度器优先级的适配器实例化 `ITransitionInterpreter<NonPriority>`（其 `SamplerSet<NonPriority>` 不携带优先级地施加帧）。不存在非泛型变体。
- 具体循环行为位于 `Abstractions.TransitionInterpreterCore`（见 [abstractions](../../01_abstractions/index.md)）。
- *核验：* `SamplingLoopTests`（`DurationZero_JumpsToEnd_AndCompletes`、`HandledBeforeStart_CancelsAndFiresFinally`）。

### 类：`FramePacerCore`

决定采样循环下一帧何时发生，并持有保证其安全的记账。

```csharp
public abstract class FramePacerCore : IDisposable
{
    public void Schedule(Action continuation, TimeSpan interval, CancellationToken cancellationToken);
    protected abstract void Arm(TimeSpan interval);
    protected abstract void Disarm();
    protected void Fire();
    public virtual void Dispose();
}
```

| 成员 | 说明 |
|---|---|
| `Schedule(continuation, interval, token)` | 安排 `continuation` 只运行**一次**，不早于从此刻起的 `interval`，或在 `token` 被取消时立即运行。挂起的续体是被**替换**而不是排队（一个循环拥有一个 pacer，每帧重新武装）。已取消的 token 立即运行续体。 |
| `Arm(interval)` | 子类钩子：启动或重新武装等待，使其在 `interval` 之后完成一次。每帧调用一次，且总在续体发布之后；间隔每次都重新读取，因为 effect 的 `FPS` 可能中途改变。 |
| `Disarm()` | 子类钩子：结束等待。必须容忍未武装时调用，且不得分配（每帧调用）。 |
| `Fire()` | 等待完成时子类调用它 —— 从宿主定时器的 tick，或从中央循环自身的帧。先 disarm，再恰好调用一次挂起的续体。 |
| `Dispose()` | 结束等待并**放行**挂起的续体（调用它），因为等待一个永不调用的续体的循环会永久搁浅。 |

**说明：**
- 做成抽象类而非接口，是为了让记账只有一处：一个两次调用续体的 pacer 会双倍采样，一个从不调用它的 pacer 会让循环永久停摆 —— 无异常、无帧。两种失败从宿主侧都看不见。
- 默认等待用线程池定时器（`Abstractions.ReusableTimerWait`），因此续体在定时器触发的那个线程上恢复：自定义 awaiter **不会**被编组回 `SynchronizationContext`。拥有 UI 线程的宿主改为重写 `Arm` / `Disarm` 在该线程上等待（`TransitionInterpreterCore.CreateFramePacer`），于是续体一开始就在那里被调用 —— effect 的 `Update` / `LateUpdate` 回调理应在 UI 线程上，属性写入也无需每帧一次派发就直达目标。改为等待既有的中央帧循环而不是自己的定时器是同一形状：arm 表示向该循环注册，disarm 表示离开它。
- *核验：* `FramePacerTests`（`Src/Core/VeloxDev.Core.Test/TransitionSystem/FramePacerTests.cs`）、`ReusableTimerWaitTests`，以及各适配器的 pacer 重写（`Src/Adapters/VeloxDev.WPF/PlatformAdapters/TransitionInterpreter.cs` 及其同类）。
