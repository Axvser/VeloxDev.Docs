# Transition — 命名空间：`VeloxDev.TransitionSystem.Abstractions`

### 类：`TransitionCore` / `TransitionCore<TTarget, TStateSnapshotCore>`

```csharp
public abstract class TransitionCore
{
    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}
public class TransitionCore<TTarget, TStateSnapshotCore> : TransitionCore where TStateSnapshotCore : new()
{
    public static TStateSnapshotCore Create();
    public static void Execute<T>(T target, StateSnapshotCore value, bool CanMutualTask = true) where T : class, TTarget;
    public static void Execute(StateSnapshotCore values, bool CanMutualTask = true);
    public static void Execute<T>(T target, IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false) where T : class, TTarget;
    public static void Execute(IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false);
}
```

**说明：** `Exit` 停止目标的互斥调度器，并可选停止其非互斥调度器。适配器的 `Transition`（非泛型）与 `Transition<T>` 派生于这些类。
**验证依据：** WPF 示例 `MainWindow.xaml.cs`（`Transition.Exit(Rec0, IncludeMutual: true, IncludeNoMutual: true)`）。

### 类：`StateSnapshotCore`（流式构建器）+ `TransitionCoreEx` 扩展

`Transition<T>.StateSnapshot`（适配器）继承自 `StateSnapshotCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter[, TPriorityCore]>`。公开的链式方法定义在 `TransitionCoreEx` 中，是 `StateSnapshotCore` 上的扩展方法：

| 成员 | 签名 | 描述 |
|---|---|---|
| `Property` | `StateSnapshot Property<T>(Expression<Func<TTarget, T>> lambda, T newValue, object? interpolationOptions = null)` | 记录目标值。每种可动画类型一个重载。 |
| `Effect` | `StateSnapshot Effect(TransitionEffect effect)` / `Effect(Action<TransitionEffect> effectSetter)` | 设置动画时序描述符。 |
| `Await` | `StateSnapshot Await(TimeSpan)` | 本段开始前等待。 |
| `Then` | `StateSnapshot Then()` | 开始下一段。 |
| `AwaitThen` | `StateSnapshot AwaitThen(TimeSpan)` | 等待后开始下一段。 |
| `Interpolator` | `StateSnapshot Interpolator<T>(Expression, IValueInterpolator)` | 按属性插值器覆盖。 |
| `Execute` | `void Execute(object target, bool CanMutualTask = true)` / `void Execute(bool CanMutualTask = true)` | 运行快照。 |

**说明：** `GetState()` 返回底层 `IFrameState`。分段通过 `next` 链接；`CoreExecute` 逐段把插值器、延迟、效果与状态交给调度器执行。

### 类：`StateCore : IFrameState`

`IFrameState` 的具体实现；`Values`/`Interpolators`/`Options` 为 `public virtual` + `protected set`。适配器的 `State` 由其派生。
**验证依据：** `StateCoreTests`。

### 抽象类：`InterpolatorCore`

| 成员 | 签名 |
|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` |

**说明：** 静态构造函数内置数值 + `System.Drawing` +（非 netstandard2.0）`System.Numerics` 插值器。`Interpolate` 按「按属性自定义插值器 → 注册表 → `IInterpolable` 回退」解析；返回 `TransitionProperty.UnreadablePath` 的属性会被跳过。适配器派生 `Interpolator : InterpolatorCore<InterpolatorOutput[, TPriorityCore]>` 并在静态构造函数中注册平台类型。
**验证依据：** `InterpolatorCoreTests`、`NativeInterpolatorsTests`。

### 类：`TransitionEffectCore` / `TransitionEffectCore<TPriorityCore> : ITransitionEffectCore`

默认：`FPS = 60`、`Duration = 0ms`、`IsAutoReverse = false`、`LoopTime = 0`、`Ease = Eases.Default`。事件由 `WeakDelegate`（无泄漏）支撑。`TPriorityCore` 变体增加 `Priority`。适配器 `TransitionEffect : TransitionEffectCore<DispatcherPriority>` 设置 `DispatcherPriority.Render`（WPF/Avalonia），`TransitionEffect : TransitionEffectCore<DispatcherQueuePriority>` 设置 `DispatcherQueuePriority.Normal`（WinUI）。
**验证依据：** `TransitionEffectCoreTests`。

### 抽象类：`TransitionSchedulerCore`

```csharp
public abstract class TransitionSchedulerCore : ITransitionSchedulerCore
{
    public static ConditionalWeakTable<object, ITransitionSchedulerCore> MutualSchedulers { get; protected set; }
    public static ConditionalWeakTable<object, List<ITransitionSchedulerCore>> NoMutualSchedulers { get; internal set; }
    public static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler);
    public static bool RemoveMutualScheduler(object source);
    public static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers);
    public static bool RemoveNoMutualScheduler(object source);
    public virtual WeakReference<object>? TargetRef { get; protected set; }
    public abstract Task Execute(IFrameInterpolatorCore interpolator, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**说明：** `SemaphoreSlim` 门控串行化互斥调度器上的执行；`Exit()` 取消当前的 `CancellationTokenSource`。泛型子类上的 `FindOrCreate` 把每个目标的一个互斥调度器缓存进 `MutualSchedulers`（随目标一起回收），或在并行时返回全新的非互斥调度器。
**验证依据：** WPF 示例 `RepeatMutual`（新的互斥动画取消上一次）。

### 抽象类：`TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable`

帧泵：通过 `GetEaseIndex` 计算缓动索引列表（重新索引预计算帧数组）、调用 `effect.InvokeStart/Update/LateUpdate`、通过 `frameSequence.Update(target, index)` 应用每帧、尊重 `IsAutoReverse`（反向遍历）与 `LoopTime`，然后 `InvokeCompleted` / `InvokeCancled` / `InvokeFinally`。`TransitionEventArgs.Handled` 或已取消的 `cts` 抛出 `OperationCanceledException` → `InvokeCancled`。帧间隔用 `Stopwatch` 校准（`WaitForFrameAsync`），补偿 `Task.Delay` 的抖动。
**验证依据：** WPF 示例动画（往返 + 循环）、`TransitionEffectCoreTests` 的事件顺序。

### 抽象类：`InterpolatorOutputBase : IFrameSequenceCore`

`Frames`（`Dictionary<ITransitionProperty, List<object?>>`）+ `Count`。`SetValues(target, frameIndex)` 把每个属性的帧值写到目标上；若取消令牌已被请求则跳过写入（防止已入队的旧帧覆盖重置结果）。`InterpolatorOutputCore<TUIThreadInspectorCore[, TPriorityCore]>` 缓存可复用的帧写入委托，并经 inspector 编组。

### 类：`TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public TransitionProperty(IEnumerable<PropertyInfo> segments);   // 空或带索引的属性会抛出异常
public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);
public IReadOnlyList<PropertyInfo> Segments { get; }
public static readonly object UnreadablePath;   // 中间类型无效时的哨兵
```

**说明：** getter/setter 在首次使用时**编译为单个委托**（无每帧反射）。中间类型不匹配时 `GetValue` 返回 `UnreadablePath`（插值器会跳过该属性）而不是抛 `TargetException`。
**验证依据：** `TransitionPropertyTests`。

### 静态类：`TransitionSnapshotHelper`

| 成员 | 签名 |
|---|---|
| `CaptureSpecific` | `void CaptureSpecific<T>(T target, IFrameState state, IEnumerable<Expression<Func<T, object?>>>? expressions) where T : class` |
| `CaptureAll` | `void CaptureAll<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? extraExpressions = null, int maxDepth = 4)` |
| `CaptureAllExcept` | `void CaptureAllExcept<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? excludedExpressions = null, int maxDepth = 4)` |
| `DiscoverAnimatableProperties` | `IReadOnlyCollection<ITransitionProperty> DiscoverAnimatableProperties(object target, Func<Type, bool> canAnimateType, int maxDepth = 4)` |
| `TryGetPropertyFromExpression` | `bool TryGetPropertyFromExpression<T>(Expression<Func<T, object?>> expression, out ITransitionProperty? property) where T : class` |
| `CaptureProperties` | `void CaptureProperties(object target, IFrameState state, IEnumerable<ITransitionProperty> properties)` |

**说明：** 发现过程是深度受限的 DFS（`maxDepth = 4`），拒绝下钻到基元类型、枚举、值类型、`string`、`object`、`IEnumerable` 与 `Delegate`。`CaptureAllExcept` 也会排除被排除属性的子路径。
