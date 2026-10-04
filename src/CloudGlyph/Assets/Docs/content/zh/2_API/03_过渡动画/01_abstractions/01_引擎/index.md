# 过渡动画 — 抽象层：引擎

命名空间 `VeloxDev.TransitionSystem.Abstractions`，位于 `VeloxDev.Core` 程序集（源：`TransitionSystem/Interpolator.cs`、`SamplerSet.cs`、`TransitionEffect.cs`、`TransitionScheduler.cs`、`TransitionInterpreter.cs`、`TransitionHostBase.cs`、`TransitionRun.cs`、`TransitionDiagnostics.cs`、`ReusableTimerWait.cs`）。构建器与状态容器见 [builder](../00_构建器/index.md)，属性路径见 [paths](../02_路径/index.md)。

### 抽象类：`InterpolatorCore`

```csharp
public abstract class InterpolatorCore
{
    static InterpolatorCore();   // 播下默认注册表

    public static bool TryGetInterpolator(Type type, out ISampler? sampler);
    public static bool RegisterInterpolator(Type type, ISampler sampler);
    public static bool UnregisterInterpolator(Type type, out ISampler? sampler);

    public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect);   // 基类返回 null

    public virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(
        object target, IFrameState state, ITransitionEffectCore effect, ITransitionHost<TPriorityCore> host);
}
```

| 成员 | 说明 |
|---|---|
| `RegisterInterpolator` | 以**后写胜出**（`AddOrUpdate`）安装采样器 —— 无条件、原子。返回 `true`。 |
| `UnregisterInterpolator` | 移除条目，经 `sampler` 报出。 |
| `TryGetInterpolator` | 为*属性*类型解析采样器：先精确类型，再最近优先的基类，最后接口。 |
| `CreateScheduler` | 本平台用什么调度器给 `target` 做动画，供只把目标当作 `object` 的调用方使用；本平台承载不了 `effect` 时返回 `null`。 |
| `Prepare<TPriorityCore>` | 把已声明状态归一化为可运行的 `SamplerSet<TPriorityCore>`。 |

**关于注册表：** 字典本身是**私有**的，只经上面三个成员触达。它像 `TimerCore` 持有其工厂那样被持有，而不是做成公开属性：能触达字典的调用方可以整体替换它（丢掉静态构造函数安装的每一项默认）或清空它，这两件都不是注册 API 该允许的。键从不外发。静态构造函数播下 `double`、`float`、`int`、`long`、`System.Drawing.Point/PointF/Size/SizeF/Color/Rectangle/RectangleF`，以及（仅在非 `netstandard2.0` 编译时）`System.Numerics.Vector2/Vector3/Vector4/Quaternion`。

**关于 `TryGetInterpolator` 的解析顺序：** 查找不是精确匹配。先试精确类型；再最近优先走基类链；然后是该类型的接口，多个接口命中时取全名按序（ordinal）最小者。接口排最后、其决胜规则显式写死，因为反射自身的顺序未被规定。之所以要走这条链，是因为框架属性常常声明为适配器注册类型的子类 —— 一个声明为 `LinearGradientBrush` 的属性对 WPF 注册的 `Brush` —— 所以只做精确匹配会让它不被动画、并被报为不可采样。这对你自己的一次注册意味着：注册**通用**类型（一旦基类或接口被注册，具体类型的注册就是冗余的）；通用注册必须能处理整个家族，因为这条链会把子类交给它；查找是按*属性类型*做的，所以声明为 `LinearGradientBrush` 的路径会找到 `Brush` 采样器。这条链每个属性每次动画走一次，位于 `Prepare` 内 —— 绝不逐帧。*核验：* `InterpolatorCoreTests`（`TryGetInterpolator_FallsBackToABaseClass`、`_PrefersTheNearestBaseClass`、`_FallsBackToAnInterface`、`_PrefersABaseClassOverAnInterface`、`_WithTwoMatchingInterfaces_IsDeterministic`）。

**关于 `CreateScheduler`：** 主题系统赖以运行的接缝。一次主题切换横跨多种运行时类型的目标，因此 Core 无法命名 `Transition<T>` 的类型实参，而构成一个调度器的宿主 / 解释器 / 调度器优先级是只有平台知道的那一件事。基类返回 `null`；每个适配器重写它并交出自己参数化的调度器（见 [adapter-provided/effect-interpolator](../../03_适配器提供/01_效果插值器/index.md)）。`null` 对「本平台未接入」与「这个 effect 不属于本平台」都是诚实答案 —— 后者正是调度器自己运行前所做强制转换的镜像 —— 调用方于是不带动画地完成切换，而不是启动一次什么都画不出来的运行。重写必须返回 `TransitionSchedulerCore<...>.FindOrCreate` 给它的那个实例，绝不自建：只有那条路径才把调度器登记在目标名下，而那次登记正是后来的 `Transition.Pause` / `Seek` / `Exit(target)` 所读的。*核验：* 七个适配器的 `PlatformAdapters/Interpolator.cs`；`ThemeManager` / `RunSwitch`。

**关于 `Prepare<TPriorityCore>`：** 对每个已声明值，它先把路径绑到目标（`TransitionProperty.BindTo` —— 冻结的索引实参在此解析一次、对着目标，那是目标存在的第一个时刻；无可冻结的路径返回自身，所以常见情形零分配），再经 `host.Run<object?>(target, ...)` 读当前值。无效路径（`TransitionProperty.UnreadablePath`）被**跳过并经 effect 的 `Warn` 报出**，而不是当作 null 参与插值。采样器解析顺序：(1) `state.Interpolators` 中的逐属性自定义采样器；(2) 按 `PropertyType` 查注册表；(3) 实现 `ISampleable` 的*结构体*值类型 → 内部 `StructAssembler`（成员采样器必须全部解析，否则跳过）。什么都解析不到的属性经 `Warn` 报出并跳过。随后调用一次 `sampler.NormalizeStart(current, newValue, options)` / `NormalizeEnd(...)`，逐条存 `(property, sampler, normalizedStart, normalizedEnd, options)`。适配器派生 `Interpolator : InterpolatorCore`，在静态构造函数里注册平台类型，并重写 `CreateScheduler`。*核验：* `InterpolatorCoreTests`、`TransitionSchedulerPrepareTests`。

### 类：`SamplerSet<TPriorityCore>`

```csharp
public sealed class SamplerSet<TPriorityCore>
{
    public SamplerSet(ITransitionHost<TPriorityCore> host);
    public bool CanSetValue();
    public void Apply(object target, double t, TPriorityCore priority = default!);
}
```

**说明：** 类型形参是宿主的调度器优先级（或 `NonPriority`），作为类型形参承载而不是 `object?`，使 `Apply` 把优先级**不装箱**地交给宿主 —— 之前的 `object?` 形参在每个动画的每一帧上装箱一个 `DispatcherPriority`。构造函数对 null 宿主抛 `ArgumentNullException`。`CanSetValue()` 返回 `host.IsAlive`。`Apply` 把逐属性更新编组到 UI 线程：动画已取消或应用已不存活时立即返回（过期帧守卫，使已排队的帧绝不可能覆盖一次重置），每个目标缓存一个闭包、经 `Interlocked` 读的字段传缓动时间（每采样零闭包分配），解析该趟钉住的线程（无 run 的调用方回退到 `host.ThreadFor(target)`），再经 `host.Post` 投递。在 UI 线程上，它逐个跑条目里的 `sampler.InsertFrame(...)`；抛异常的采样器经 `Error` 报一次并安静结束该趟，而不是以帧率抛。*核验：* `SamplerSetTests`、`FramePathAllocationTests`。

### 类：`TransitionEffectCore` / `TransitionEffectCore<TPriorityCore>`

默认描述符实现。默认值：`FPS = 60`、`Duration = 0`、`IsAutoReverse = false`、`LoopTime = 0`、`Ease = Eases.Default`。

| 成员 | 类型 / 签名 |
|---|---|
| 属性 | `virtual int FPS`、`virtual TimeSpan Duration`、`virtual bool IsAutoReverse`、`virtual int LoopTime`、`virtual IEaseCalculator Ease`（均为 `{ get; set; }`） |
| 事件 | `virtual event EventHandler<TransitionEventArgs>` —— `Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally`、`Warn`、`Error` |
| 触发器 | `virtual void InvokeAwake/InvokeStart/InvokeUpdate/InvokeLateUpdate/InvokeCompleted/InvokeCancled/InvokeFinally/InvokeWarn/InvokeError(object sender, TransitionEventArgs e)` |
| `Clone` | `ITransitionEffectCore Clone()` |

**说明：** 事件由 `WeakDelegate`（`VeloxDev.WeakTypes`）承载，因此短命的事件拥有者不会泄漏；`Clone` 深拷贝事件后备存储并复制所有属性（含 `Warn` / `Error` 与 `Priority`）。`InvokeCancled` 是真实成员名。`InvokeWarn` / `InvokeError` 先写一行 `Debug.WriteLine` 再触发事件，且刻意**不**调 `Debug.Fail` —— 那会在无交互宿主中直接终止进程，而那正是本通道要防的事。裸基类本身实现 `ITransitionEffect<NonPriority>`（其 `NonPriority` 优先级恒为 `default`），因此无优先级的适配器可直接用它；子类 `TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>` 增加 `virtual TPriorityCore Priority { get; set; }` 与 `new ITransitionEffect<TPriorityCore> Clone()`。*核验：* `TransitionEffectCoreTests`、`TransitionDiagnosticsTests`。

### 抽象类：`TransitionSchedulerCore`

```csharp
public abstract class TransitionSchedulerCore : ITransitionSchedulerCore
{
    public static ConditionalWeakTable<object, ITransitionSchedulerCore> MutualSchedulers { get; protected set; }
    public static ConditionalWeakTable<object, ConcurrentDictionary<ITransitionSchedulerCore, byte>> NoMutualSchedulers { get; internal set; }

    public static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler);
    public static bool RemoveMutualScheduler(object source);
    public static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers);
    public static bool RemoveNoMutualScheduler(object source);

    protected readonly SemaphoreSlim _gate = new(1, 1);
    public virtual WeakReference<object>? TargetRef { get; protected set; }

    public abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**说明：** `MutualSchedulers` 按目标缓存一个*互斥*调度器（`ConditionalWeakTable`，随目标回收）；`NoMutualSchedulers` 把一次性的*非互斥*调度器按目标存成一个并发**集合**（动画从多个线程各自登记 / 注销，普通 `List` 会丢条目，`Exit` 就会漏掉一个活着的运行）。另一张 `ConditionalWeakTable`（`GetTargetLock`）串行化一个目标的**控制面** —— 「进入」（建 token 并登记动画）对「离开」（取消其上一切存活者）；它只在同步记账期间持有，绝不跨过动画主体。

一个泛型子类参数化具体宿主 / 解释器：

```csharp
public class TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>
    : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore>
    where THost : ITransitionHost<TPriorityCore>, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()
{
    protected static readonly THost host = new();

    public static ITransitionScheduler<TPriorityCore> FindOrCreate<T>(T source, bool CanMutualTask = true) where T : class;

    public virtual Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default);
    public virtual Task<SamplerSet<TPriorityCore>?> ExecuteCapturing(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default);
    public virtual Task Replay(SamplerSet<TPriorityCore> frameSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default);
}
```

| 成员 | 说明 |
|---|---|
| `FindOrCreate(source, CanMutualTask)` | 缓存的互斥调度器（经 `GetValue` 原子安装），或一个携带源的 `WeakReference` 的全新非互斥调度器。 |
| `Execute` | 跑一趟已准备好的动画：在 UI 线程上 await `Awake` 的派发（是 await 而不是发了就算，使 `Awake` 在 `Prepare` 读目标之前完成 —— 它可经 `Args.Handled` 否决动画，并可把目标置入该动画的起始状态），准备 `SamplerSet`，登记该 run，再把集合交给一个全新解释器。`_gate` 串行化执行；**代计数器**让仍排在门后的 run 在某次 `Exit` 先落地时放弃。 |
| `ExecuteCapturing` | 同上，但把它准备的那套帧集交还调用方，好让调用方对同一端点重跑同一段。 |
| `Replay(frameSet, effect, cts)` | 用某段当初准备的那套帧集再跑一遍。目标**不**重读、`Awake` **不**重触发；`Start`、`Update`、`LateUpdate`、`Completed` 与诊断完全照常触发，因此一次重放与一趟一样可观测。这一对是链的 `Repeat` 循环所依赖的东西。 |

每个动画为其**整个生命期**（含分段之间的 `Await` 间隔）登记自己的 `CancellationTokenSource`，因此 `Exit()` 能取消一个当前并未在执行分段、而是在两段之间空转的 run。`Exit()` 先推进代计数器、抽干被跟踪的 run，随后在**任何锁之外**取消它们。*核验：* WPF 演示 `RepeatMutual` / `ExitAll`、`TransitionSchedulerExitTests`、`TransitionSchedulerAwakeTests`、`NoMutualSchedulerRegistryTests`、`ChainRepeatTests`、`AUTO TEST` `LoadModes_MatchTheLibrarySemantics`。

### 抽象类：`TransitionInterpreterCore`

```csharp
public abstract class TransitionInterpreterCore : IDisposable
{
    protected CancellationTokenSource? cts;
    public virtual TransitionEventArgs Args { get; set; }

    protected virtual FramePacerCore? CreateFramePacer(object target, IThreadAffinity affinity);   // 默认 null
    protected virtual void ArmNextFrame(Action continuation, TimeSpan interval, CancellationToken cancellationToken);

    public virtual void Exit();
    public virtual void Dispose();   // 取消活动 CancellationTokenSource

    protected Task ExecuteSamplingLoopAsync<TPriorityCore>(object target, SamplerSet<TPriorityCore> frameSet,
        ITransitionEffectCore effect, CancellationTokenSource cts, Action<double> apply);
}
```

| 成员 | 说明 |
|---|---|
| `CreateFramePacer(target, affinity)` | 宿主自己的帧节奏器，或 null（表示用默认线程池定时器）。每次运行**至多调用一次**，在循环的第一帧之前，且仍在循环启动的那个线程上同步调用 —— 因此实现也可以捕获当前线程的 dispatcher。宿主应从 `affinity.ThreadFor(target)` 推出节奏器：与写路径不一致的节奏器会把每一帧变成一次派发。`ThreadRef.None` 与 null 都是受支持的答案。 |
| `ArmNextFrame(continuation, interval, token)` | 安排下一帧：已取消的 token 立即运行续体，否则在宿主给了节奏器时经它、没给时经一个复用的 `ReusableTimerWait`（整条循环一个 `Timer`，整个动画一次取消登记，而不是每帧一次）。不得阻塞，且必须**恰好一次**调用续体 —— 一个干脆不再回调的实现会让循环永久停摆。 |

两个泛型子类把循环接到采样集的 `Apply`：
- `TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore>`（约束 `TTransitionEffectCore : ITransitionEffect<TPriorityCore>`）—— 施加 `easedT => frameSet.Apply(target, easedT, effect.Priority)`。
- `TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter<NonPriority>`（约束 `TTransitionEffectCore : ITransitionEffectCore`）—— 施加 `easedT => frameSet.Apply(target, easedT)`；无优先级宿主保持在无优先级路径上采样，因此 `NonPriority` 每帧零成本。

**采样循环语义**（`ExecuteSamplingLoopAsync`）：由时间轴驱动的连续采样，不是帧泵。归一化时间是当前趟的锚点与动画 `ITimeSource` 之间的距离 —— `Task.Delay` 绝不是计时来源，其不精确不影响正确性。让出间隔上限为 `1000 / FPS` 毫秒（`FPS` 是最大采样率，不是帧栅格）：这约束分配率，并在系统定时器分辨率很细时阻止循环淹没 UI 渲染线程。每趟算原始时间、缓动它（**不夹取** —— `Back` 与 `Elastic` 靠离开 `[0, 1]` 定义），然后 `InvokeUpdate` → `apply(easedT)` → `InvokeLateUpdate`；每趟最后一帧是**精确端点**（`t >= 1` → 正向缓动 `1` / 反向 `0`），不依赖 `Ease(1)` 是否恰为 `1`。时间轴未推进时，循环先画出冻结位置，再在 `WaitWhileStalledAsync` 上**停摆**，因此暂停或冻结的动画完全不耗定时器唤醒（速率为 0 会冻结时间轴而不暂停它，循环对它也停摆）。`Start` 在循环前触发一次；`IsAutoReverse` 追加一趟反向；`LoopTime` 重复（`int.MaxValue` = 永远），而趟计数器是从 run 读来而不是私有持有的，因此 `Seek` 能移动它。正常完成触发 `Completed`；取消 —— 取消的 `cts` **或** `Args.Handled = true` → `OperationCanceledException` —— 触发 `Canceled`；`Finally` 在每条结束路径上触发，且循环自身的资源（节奏器与复用的等待）在嵌套 `finally` 里释放，使抛异常的回调无法泄漏一个宿主定时器。**异常绝不离开本方法**：回调、采样器或宿主抛出会结束该趟并经 `Error` 报出，然后该趟沿正常取消路径回卷，使 `Canceled` 与 `Finally` 仍然触发。*核验：* `SamplingLoopTests`、`FramePacerTests`、`ReusableTimerWaitTests`、`TransitionDiagnosticsTests`。

### 类：`TransitionHostBase<TPriorityCore>`

适配器宿主派生的基类：`ThreadDispatcherBase<TPriorityCore>` 外加一个 `ApplicationState` 存活标志。与宿主契约一起记录 —— 见 [host](../../00_transitionsystem/03_宿主/index.md)。

### 内部支撑类型（非公开 API）

此处记录，因为其行为可观测，尽管类型是 `internal`：

- **`TransitionRun`** —— 一次运行中的动画：结束它的 token、它锚定的 `ITimeSourceControl`、当前趟开始的时间轴位置（`PassAnchor`）、趟计数器（`Cycle`），以及它把帧投递到的 `ThreadRef`（由调度器一次性钉死，因为写路径跑在采样循环的线程上，而那个线程对一个「答案取决于调用方」的宿主没有答案 —— 例如 Blazor 回路的 renderer）。`PassAnchor` 与 `Cycle` 都是单个 `long` 字段，各由一个原子操作移动。
- **`TransitionDiagnostics`** —— 报告一趟降级与失败的阶段：一行 `Debug`，以及有人在监听时的 effect 的 `Warn` / `Error` 事件。两个通道都不向调用方抛异常，且每个 `stage` 每个实例**至多报一次**，因为它们大多是逐帧的事实。在实参上置 `Handled` 的处理器即要求终止该趟。
- **`ReusableTimerWait`** —— 整条循环一个 `Timer`、每次等待重新武装，且整个循环一次取消登记而不是每次等待一次。`await Task.Delay(interval, token)` 每次等待都建一个全新的 `DelayPromise` 并登记一个全新的取消回调；采样循环每个动画每帧等待一次，所以这曾是这条本来零分配路径上的最后一块分配 —— `ReusableTimerWaitTests` 量出了差别。它最终用的就是 `Task.Delay` 也会用的那个 `Timer`，因此改变的是等待的成本而不是它何时落地。停摆中的等待在释放时是被**放行**而不是被丢弃：丢弃会让循环悬在那里，再没有任何东西能唤醒它。
