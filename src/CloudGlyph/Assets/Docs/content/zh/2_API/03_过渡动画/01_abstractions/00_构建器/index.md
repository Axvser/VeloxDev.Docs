# 过渡动画 — 抽象层：构建器与状态

命名空间 `VeloxDev.TransitionSystem.Abstractions`，位于 `VeloxDev.Core` 程序集（源：`Src/Core/VeloxDev.Core/TransitionSystem/Transition.cs`、`StateSnapshot.cs`、`State.cs`、`TransitionEx.cs`）。这里是流式构建器、分段链的根，以及已声明状态的容器。本命名空间其余部分见 [engine](../01_引擎/index.md) 与 [paths](../02_路径/index.md)。

### 类：`TransitionCore`

非泛型的根：不需要 `T` 的静态入口。

```csharp
public abstract class TransitionCore
{
    public static TSnapshot Create<TSnapshot>() where TSnapshot : StateSnapshotCore, new();

    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Pause<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Resume<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void SetRate<T>(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Seek<T>(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Seek<T>(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;

    public static int Cycle<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static bool IsPaused<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static TimeSpan Position<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static double Rate<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}
```

| 成员 | 说明 |
|---|---|
| `Create<TSnapshot>()` | 返回一个全新的、未链接的构建器，并把它标记为链的*根*，使后续 `Then()` / `AwaitThen()` 分段共用它。 |
| `Exit` | 取消 `target` 上所有正在运行的动画：`IncludeMutual` 时取消互斥调度器（以 `CanMutualTask: true` 启动的动画），`IncludeNoMutual` 时取消每一个非互斥调度器。取消是一个**信号** —— 动画在下一个 await 处停下，因此它返回时动画可能仍在释放其调度器；随后的一次互斥 `Execute` 会在调度器自己的门后排队，最坏晚一帧落地。 |
| `Pause` / `Resume` | 原地冻结 / 解冻该趟的时间轴，不结束任何动画。 |
| `SetRate(target, rate)` | 改变播放速率而不移动位置；`0` 冻结但不暂停。负速率以 `ArgumentOutOfRangeException` 拒绝（不存在反向播放）。 |
| `Seek(target, position)` / `Seek(target, cycle, position)` | 在当前趟内移动，或移入编号为 `cycle` 的那一趟，保持速率。 |
| `Cycle` / `IsPaused` / `Position` / `Rate` | 四个查询；每个对**无运行**给出答案而非抛异常（`0` / `false` / `TimeSpan.Zero` / `0`）。`IsPaused` 仅在至少有一个动画且每一个都被暂停时为 true。 |

**说明：** 控制操作作用于每一趟锚定的 `ITimeSourceControl`，因此共享同一条时间轴的多个动画被一起操纵。它们刻意**不**取目标锁（不同于 `Exit`，其锁串行化「离开」与「进入」）；它们既不增也不删注册，因此没有可串行化的东西，扫描中途启动的一趟与之前启动的一样可控。`Exit` 只对记账（取出被跟踪的 token）持锁，并在**释放锁之后**才取消，因为 `CancellationTokenSource.Cancel()` 在调用线程上同步跑回调 —— 持锁跨过它们会在 UI 线程的 `Exit` 上阻塞 dispatcher，并在一个重入同目标 `Exit` 的回调上死锁。*核验：* WPF 演示（`PauseAll`、`ResumeAll`、`SetRate`、`SeekNextPass`、`ExitAll`）；`AUTO TEST` `TimelineControl_SteersTheRunningAnimation`；`TimelineControlTests`。

### 类：`TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore>`

```csharp
public class TransitionCore<
    T,
    TStateCore,
    TEffectCore,
    TInterpolatorCore,
    THost,
    TTransitionInterpreterCore,
    TPriorityCore> : StateSnapshotCore<T>
    where T : class
    where TStateCore : IFrameState, new()
    where TEffectCore : ITransitionEffect<TPriorityCore>, new()
    where TInterpolatorCore : InterpolatorCore, new()
    where THost : ITransitionHost<TPriorityCore>, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()
{
    public int RepeatTime { get; set; }         // 本段循环的额外迭代次数
    public TStateCore GetState();
    public static void Execute(T target, IEnumerable<TransitionCore<...>> values, bool CanMutualTask = false);
}
```

| 成员 | 说明 |
|---|---|
| `RepeatTime` | 本段循环还要再跑几次：`0` —— 默认 —— 跑一次，`int.MaxValue` 永远跑。经 `Repeat(count)` 扩展设置。 |
| `GetState()` | 底层 `TStateCore`（一个实现 `IFrameState` 的 `StateCore`）—— 本段声明的值 / 采样器 / 选项。 |
| `Execute(target, values, CanMutualTask)` | 在 `target` 上跑批中每个构建器。默认非互斥：它们并发运行且**不**互相取消 —— 刻意与单构建器的 `Execute(target)` 实例方法相反。 |

**说明：**
- **只有一种元数**：宿主的调度器优先级对每个适配器都是类型形参，无优先级的宿主传 `NonPriority`。第 5 个形参是**宿主**（`THost : ITransitionHost<TPriorityCore>`，`new()`），而不是一个裸的线程检查器 —— 引擎通过一个对象向宿主索取线程、派发与存活答案（见 [host](../../00_transitionsystem/03_宿主/index.md)）。
- 链的循环由 `RepeatTime` 描述，一段的循环包裹**从首段到本段**的链；循环按结束位置嵌套。见下面的 `Repeat`。
- 各适配器单出非泛型 `Transition : TransitionCore` 与 `Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>` —— 你通常调用 `Transition<T>.Create()`、`Transition.Exit(...)`，以及继承来的实例 `Execute`（见 [adapter-provided](../../03_适配器提供/index.md)）。`AddNoMutual` / `RemoveNoMutual` / `RejectUnsampleablePaths` / `CoreExecute` 为 `internal`。*核验：* WPF 演示 `MainWindow.xaml.cs`。

### 类：`StateSnapshotCore` / `StateSnapshotCore<T>`

```csharp
public abstract class StateSnapshotCore<T> : StateSnapshotCore where T : class
{
    public void Execute(T target, bool CanMutualTask = true);
    public void Execute(T target, ITimeSourceControl timeline, bool CanMutualTask = true);

    public void Exit(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Pause(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Resume(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void SetRate(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Seek(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Seek(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public bool IsPaused(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public TimeSpan Position(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public int Cycle(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public double Rate(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
}

public abstract class StateSnapshotCore
{
    // internal: AsRoot / CoreExecute / CoreValidate / CoreThen / CoreAwait / CoreAwaitThen /
    //           CoreRepeat / CoreInterpolator / CoreEffect / CoreRecordState
}
```

**说明：**
- 具体构建器（上面的 `TransitionCore<...>`）的抽象根。`Execute(target, CanMutualTask)` 是公开的一次性入口：目标类型由 `T` 固定，因此编译期检查；它校验已声明路径（一条永远无法动画的路径抛 `TransitionPathUnsampleableException`），然后跑这条链。校验在这里而不是在 `CoreExecute` 里做，因为后者是 `async void` —— 从它抛出的异常会逃到同步上下文而不是到达调用方。
- `Execute(target, timeline, CanMutualTask)` 是**共享时间轴**重载。共享一条时间轴的动画共享一套传输：暂停、变速或定位其中一个会一起移动全部，而每一个保留自己的趟与自己在该趟中的位置。这正是编舞式分组所需 —— 多个动画保持同步而彼此互不知晓。`timeline` 为 null 时抛 `ArgumentNullException`。
- 九个控制成员是 `TransitionCore` 静态方法的实例形式 —— `Exit`/`Pause`/`Resume`/`SetRate`/`Seek`/`IsPaused`/`Position`/`Cycle`/`Rate` —— 加上它们，一个构建器就能操纵自己的目标而不必提 `Transition` 或 `TransitionCore`。
- 其余是 `internal`/`protected` 机械：`CoreExecute` 遍历链接分段（`next`），逐段把插值器 / 延时 / 克隆的 effect / state 交给调度器；`CoreThen` / `CoreAwaitThen` / `CoreRepeat` / `CoreEffect` / `CoreInterpolator` 是公开扩展与适配器重载调用的钩子。
- 不存在单独的 `StateSnapshotCore<...>` 构建器类，也没有顶层 `StateSnapshot` 或 `Transition<T>.StateSnapshot` 类型：具体构建器就是 `TransitionCore<...>`。构建器的*公开*词汇来自 `TransitionCoreEx`（见下）与各适配器的 `Property` / `Effect` 重载。
- *核验：* WPF 演示在 `Transition<Rectangle>` 上链式调用 `.Property(...)`、`.Effect(...)`、`.Await(...)`、`.AwaitThen(...)` 并遍历 `GetState().Values`；`ChainRepeatTests`。

### 静态类：`TransitionCoreEx`（扩展，命名空间 `VeloxDev.TransitionSystem`）

| 成员 | 签名 | 说明 |
|---|---|---|
| `Await` | `T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | 在本段播放前设置一段延时。 |
| `Then` | `T Then<T>(this T snapshot) where T : StateSnapshotCore, new()` | 在本段之后立即开始一个链接的新分段。 |
| `AwaitThen` | `T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | 等待 `timeSpan`，随后开始一个链接的新分段。 |
| `Repeat` | `T Repeat<T>(this T snapshot, int count) where T : StateSnapshotCore, new()` | 让本段的循环再跑 `count` 次。`0` 跑一次，`int.MaxValue` 永远跑。 |
| `Interpolator` | `TSnapshot Interpolator<TSnapshot, TTarget, TValue>(this TSnapshot snapshot, Expression<Func<TTarget, TValue>> propertyLambda, ISampler interpolator) where TSnapshot : StateSnapshotCore, new()` | 覆盖 `propertyLambda` 的逐属性采样器。 |

**说明：** 这五个就是 `TransitionCoreEx` 的**全部**公开表面 —— 没有 `Execute` 扩展（运行是继承来的实例方法 `Execute`）。`Await` / `Then` / `AwaitThen` / `Repeat` 通过改写构建器链来记录延时 / 链接 / 循环。*核验：* WPF 演示（`Animation0`/`Animation1`/`Animation2`）、`ChainRepeatTests`。

#### `Repeat` 的语义

一段的循环包裹**从首段到本段**的链，循环按结束位置嵌套：三段各带 `Repeat(1)` 跑 `1, 1, 2, 1, 1, 2, 3, 1, 1, 2, 1, 1, 2, 3`，因此只有**末段**上的计数才重复整条链。计数是**额外**迭代的次数 —— effect 的 `LoopTime` 早已遵循的规则。某段首次之后每次迭代都**重放首次迭代准备的那套帧集**，而不重新读取目标：否则重复的一段会从上次迭代停下处起步，终点不同于起点的链会倒退，而某段写着更早分段都没碰过的属性时会一趟比一趟漂。重放时 **`Awake` 不再触发**（它是把目标放进该段起始状态的钩子，而重放的定义就是不依赖目标的状态）；`Start`、`Update`、`LateUpdate`、`Completed` 与诊断完全照常触发。

### 类：`StateCore : IFrameState`

`IFrameState` 的具体默认实现；适配器的 `State` 由它派生（见 [adapter-provided](../../03_适配器提供/index.md)）。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Values` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Values { get; protected set; }` | 记录的目标值。 |
| `Interpolators` | `virtual ConcurrentDictionary<ITransitionProperty, ISampler> Interpolators { get; protected set; }` | 逐属性采样器覆盖。 |
| `Options` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Options { get; protected set; }` | 逐属性插值选项。 |
| `SetValue` / `TryGetValue` | 三个重载族 | `(Expression<Func<TSource, TValue>>, TValue?)`、`(ITransitionProperty, object?)`、`(PropertyInfo, object?)`；`Try*` 有配套的 `out` 形式。 |
| `SetInterpolator` / `TryGetInterpolator` | 三个重载族 | 同一寻址，值为 `ISampler`。 |
| `SetOptions` / `TryGetOptions` | 三 / 一个重载族 | `SetOptions` 有表达式 / `ITransitionProperty` / `PropertyInfo` 形式；`TryGetOptions` 有 `ITransitionProperty` 形式。 |
| `Clone` | `virtual IFrameState Clone()` | 三份字典的独立浅拷贝。 |

**说明：** `SetValue` 的值形式是运行父/子路径冲突检查（`RejectPathConflict` → `TransitionPathConflictException`）的漏斗。表达式重载只记录可读且可写的路径；字典为 `protected set`，好让派生的适配器 state 能替换它们。*核验：* `StateCoreTests`、`TransitionPathConflictTests`。
