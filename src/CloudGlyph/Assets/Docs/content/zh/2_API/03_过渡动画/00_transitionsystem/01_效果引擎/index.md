# Transition — 契约：效果、调度器、解释器、UI 线程

命名空间 `VeloxDev.TransitionSystem`。这些接口描述时序描述符、按目标执行的协调器、采样循环运行器与 UI 线程编组。每个接口都有「优先级类型化」变体（供以调度器优先级编组的适配器使用：WPF、Avalonia、Jalium、WinUI）与非类型化变体（其余适配器）。

### 接口：`ITransitionEffectCore`

| 成员 | 类型 / 签名 | 说明 |
|---|---|---|
| `FPS` | `int FPS { get; set; }` | **最大采样率上限**，默认 `60`。让步间隔为 `1000 / FPS` ms。计时是 Stopwatch 驱动的连续采样——`FPS` 只是限制采样频率，**不是**帧网格。 |
| `Duration` | `TimeSpan Duration { get; set; }` | 名义上的单程长度；默认 `0`（零时长单程只采样一次并跳到终点）。 |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` | 为 `true` 时每程之后跟一段反向程。 |
| `LoopTime` | `int LoopTime { get; set; }` | 首程之后的重复次数；`int.MaxValue` = 无限循环。 |
| `Ease` | `IEaseCalculator Ease { get; set; }` | 应用于原始归一化时间的缓动曲线。 |
| 事件 | `EventHandler<TransitionEventArgs>` | `Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally`。 |
| 调用器 | `void Invoke*(object sender, TransitionEventArgs e)` | `InvokeAwake`、`InvokeStart`、`InvokeUpdate`、`InvokeLateUpdate`、`InvokeCompleted`、`InvokeCancled`、`InvokeFinally`（拼写 `InvokeCancled` 是真实成员名）。 |
| `Clone` | `ITransitionEffectCore Clone()` | 深拷贝，同时克隆（弱引用）事件后备存储。 |

**说明：**
- 正常运行的事件顺序：调度器在 UI 线程先触发 `Awaked` 再准备，循环先触发一次 `Start`，然后每采样一次 `Update` / `LateUpdate`，最后一程结束后触发 `Completed`。取消的运行触发 `Canceled`，并且**每条**结束路径（完成或取消）都会触发 `Finally`。
- *验证依据：* `TransitionEffectCoreTests`（`Defaults_AreCorrect`、`Events_AreInvoked`、`Clone_CopiesProperties`、`EventRemove_StopsFiring`）、`SamplingLoopTests`（事件顺序断言）。

### 接口：`ITransitionEffect<TPriorityCore>`

扩展 `ITransitionEffectCore`，加入类型化优先级与协变克隆：

```csharp
public interface ITransitionEffect<TPriorityCore> : ITransitionEffectCore
{
    TPriorityCore Priority { get; set; }
    new ITransitionEffect<TPriorityCore> Clone();
}
```

**说明：** 适配器效果会设置具体优先级默认值（如 WPF/Avalonia 为 `DispatcherPriority.Render`、WinUI 为 `DispatcherQueuePriority.High`）；循环把 `Priority` 透传给采样集的 `Apply`。

### 接口：`ITransitionSchedulerCore`

```csharp
public interface ITransitionSchedulerCore
{
    Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**说明：**
- `Execute` 在调度器的目标上运行一次准备好的动画：先在 UI 线程上 **await** 触发 `Awaked`（Awake 可否决动画、也可把目标置为动画起点），再 `Prepare` 出 `SamplerSet`，最后交给解释器。`SemaphoreSlim` 门控在**互斥**调度器上串行化执行（第二个动画会取消第一个）；`externCts` 允许调用方提供自己的取消源。
- `Exit()` 取消该调度器当前正在运行的动画。
- 类型化变体收窄效果参数：
  - `ITransitionScheduler<TPriorityCore> : ITransitionSchedulerCore` — `Execute(InterpolatorCore, IFrameState, ITransitionEffect<TPriorityCore>, CancellationTokenSource? externCts = default)`。
  - `ITransitionScheduler : ITransitionSchedulerCore` — 标记（无新成员）。
- 具体调度器基类 `Abstractions.TransitionSchedulerCore` 提供按目标的注册表与 `FindOrCreate`（见 [01_abstractions](../../01_abstractions/index.md)）。
- *验证依据：* `SamplingLoopTests`；WPF 示例 `RepeatMutual`（新的互斥动画取消上一次）。

### 接口：`ITransitionInterpreter<TPriorityCore>`

```csharp
public interface ITransitionInterpreter<TPriorityCore> : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, SamplerSet<TPriorityCore> samplerSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts);
    void Exit();
}
```

**说明：**
- 非泛型的 `ITransitionInterpreter` / `ITransitionInterpreterCore` 接口**已删除**；现在只有带优先级的这一支。
- `Args` 是解释器驱动的事件参数实例；把 `Args.Handled` 设为 `true` 会短路时间线（循环抛 `OperationCanceledException` → `Canceled` + `Finally`）。
- `Execute` 针对准备好的 `SamplerSet<TPriorityCore>` 运行 Stopwatch 驱动采样循环。`Exit()`（即 `Dispose` 的别名）取消当前 `CancellationTokenSource`。
- 具体循环行为在 `Abstractions.TransitionInterpreterCore` 及其两个泛型子类（见 [01_abstractions](../../01_abstractions/index.md)）。
- *验证依据：* `SamplingLoopTests`（`DurationZero_JumpsToEnd_AndCompletes`、`HandledBeforeStart_CancelsAndFiresFinally`）。

### 接口：`IUIThreadInspectorCore`、`IUIThreadInspector<TPriorityCore>`

```csharp
public interface IUIThreadInspectorCore
{
    bool IsAppAlive();
    bool IsUIThread();
    object? ProtectedGetValue(object target, ITransitionProperty property);
}

public interface IUIThreadInspector<TPriorityCore> : IUIThreadInspectorCore
{
    bool ProtectedInvoke(object target, Action action, TPriorityCore priority);
    Task<bool> ProtectedInvokeAsync(object target, Action action, TPriorityCore priority);
}
```

| 成员 | 说明 |
|---|---|
| `IsAppAlive` | 宿主应用是否仍存活（过期帧守卫：`SamplerSet.Apply` 在它为 false 时提前返回）。 |
| `IsUIThread` | 调用方是否已在 UI 线程上。 |
| `ProtectedInvoke` | 把 `action` 编组到 UI 线程（可用时使用目标自带的 dispatcher / control）。**返回 `bool`**——该 action 是否真的入队；宿主 dispatcher 已消失或目标还没有队列时为 `false`。 |
| `ProtectedInvokeAsync` | 与 `ProtectedInvoke` 相同，但只在 `action` **真的执行完**后才完成；专供每次动画一次、必须发生在帧开始之前的调用（效果的 Awake）。返回 `false` 表示从未入队。 |
| `ProtectedGetValue` | 沿链读取属性，必要时编组到 UI 线程。 |

**说明：**
- 非泛型接口 `IUIThreadInspector` **已删除**；无优先级的适配器（MAUI / WinForms / Razor）用 `NonPriority` 作为 `TPriorityCore`（见 [01_abstractions](../../01_abstractions/index.md)）。
- `IsAppAlive` / `IsUIThread` / `ProtectedGetValue` 由共享基接口 `IUIThreadInspectorCore` 声明；`ProtectedInvoke*` 在带优先级的接口上，且优先级以类型参数而非 `object?` 传递（热路径不装箱）。
- 各平台行为见 [03_adapter-provided/02_ui-inspector](../../03_适配器提供/02_UI线程检查器/index.md)。
