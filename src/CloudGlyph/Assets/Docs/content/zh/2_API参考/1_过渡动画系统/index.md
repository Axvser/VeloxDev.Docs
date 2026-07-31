# 过渡动画系统 — API 参考

引擎位于 `VeloxDev.Core`；每个平台适配器（WPF/Avalonia/WinUI/MAUI/WinForms/Razor）在 `VeloxDev.TransitionSystem` 命名空间中暴露相同的公共形态，并自带 `Interpolator`、`TransitionEffect`、`UIThreadInspector` 与原生插值器。

## 命名空间：`VeloxDev.TransitionSystem`

### 接口：`IInterpolable`

```csharp
public interface IInterpolable
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**返回：** `List<object?>` — `steps` 帧的中间值。

### 接口：`IValueInterpolator`

```csharp
public interface IValueInterpolator
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**说明：** 实现此接口可通过 `InterpolatorCore.RegisterInterpolator` 注册自定义类型支持。

### 接口：`IEaseCalculator`

```csharp
public interface IEaseCalculator
{
    double Ease(double t);
}
```

### 接口：`ITransitionProperty`

| 成员 | 类型 | 描述 |
|---|---|---|
| `Path` | `string` | 点分隔的嵌套属性路径（如 `"RenderTransform.X"`）。 |
| `PropertyType` | `Type` | 叶子属性类型。 |
| `PropertyInfo` | `PropertyInfo` | 叶子属性元数据。 |
| `CanRead` / `CanWrite` | `bool` | 整个链是否支持读取/写入。 |
| `GetValue` | `object? GetValue(object target)` | 沿链读取。 |
| `SetValue` | `bool SetValue(object target, object? value)` | 沿链写入。 |

### 接口：`IFrameState`

以 `ITransitionProperty` 为键的三个 `ConcurrentDictionary`：

| 成员 | 类型 |
|---|---|
| `Values` | `ConcurrentDictionary<ITransitionProperty, object?>` |
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, IValueInterpolator>` |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` |

另有强类型访问器：`SetValue`、`TryGetValue`、`SetInterpolator`、`TryGetInterpolator`、`SetOptions`、`TryGetOptions` —— 每种都有三种重载族（表达式 lambda / `ITransitionProperty` / `PropertyInfo`），以及 `IFrameState Clone()`。

### 接口：`ITransitionEffectCore`

| 成员 | 类型 / 签名 |
|---|---|
| `FPS` | `int FPS { get; set; }`（默认 60） |
| `Duration` | `TimeSpan Duration { get; set; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` |
| `LoopTime` | `int LoopTime { get; set; }`（`int.MaxValue` = 无限） |
| `Ease` | `IEaseCalculator Ease { get; set; }` |
| 事件 | `Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally` — `EventHandler<TransitionEventArgs>` |
| `Clone` | `ITransitionEffectCore Clone()` |

### 接口：`ITransitionEffect<TPriorityCore> : ITransitionEffectCore`

增加 `TPriorityCore Priority { get; set; }` 与 `new ITransitionEffect<TPriorityCore> Clone()`。

### 接口：`ITransitionSchedulerCore`

```csharp
public interface ITransitionSchedulerCore
{
    Task Execute(IFrameInterpolatorCore interpolator, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**说明：** 具体调度器上的 `FindOrCreate<T>(T source, bool CanMutualTask = true)` 在 `CanMutualTask: true` 时返回按目标共享的**互斥**调度器（存于 `ConditionalWeakTable`），否则返回允许并行动画的一次性**非互斥**调度器。

### 接口：`ITransitionInterpreterCore : IDisposable`

```csharp
public interface ITransitionInterpreterCore : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, IFrameSequenceCore frameSequence, ITransitionEffectCore effect, bool isUIAccess, CancellationTokenSource cts);
    void Exit();
}
```

### 接口：`IUIThreadInspectorCore`

| 成员 | 签名 |
|---|---|
| `IsAppAlive` | `bool IsAppAlive()` |
| `IsUIThread` | `bool IsUIThread()` |
| `ProtectedInvoke` | `abstract void ProtectedInvoke(bool isUIThread, Action action, object? priority = default)` |
| `ProtectedGetValue` | `object? ProtectedGetValue(bool isUIThread, object target, ITransitionProperty property)` |
| `ProtectedInterpolate` | `abstract List<object?> ProtectedInterpolate(bool isUIThread, Func<List<object?>> interpolate)` |

### 接口家族（帧泵）

| 接口 | 关键成员 |
|---|---|
| `IFrameInterpolatorCore` | `IFrameSequenceCore Interpolate(object target, IFrameState state, ITransitionEffectCore effect, bool isUIAccess, IUIThreadInspectorCore inspector)` |
| `IFrameInterpolator : IFrameInterpolatorCore` | 平台特定重载 |
| `IFrameInterpolator<TPriorityCore> : IFrameInterpolatorCore` | 平台特定重载 |
| `IFrameSequenceCore` | `int Count`；`SetValues(target, frameIndex)`；`Update(target, frameIndex, isUIAccess, priority)`；`AddPropertyInterpolations(property, objects)`；`SetCount(count)` |
| `IFrameSequence : IFrameSequenceCore` | `Update(target, frameIndex, isUIAccess)` |
| `IFrameSequence<TPriorityCore> : IFrameSequenceCore` | `Update(target, frameIndex, isUIAccess, TPriorityCore)` |

### 枚举：`RotationDirection`

```csharp
[Flags]
public enum RotationDirection : int
{
    Auto = 0, ClockWise = 1 << 0, CounterClockWise = 1 << 1,
    ClockWiseX = 1 << 2, CounterClockWiseX = 1 << 3,
    ClockWiseY = 1 << 4, CounterClockWiseY = 1 << 5,
    ClockWiseZ = 1 << 6, CounterClockWiseZ = 1 << 7,
}
```

**说明：** 作为 `.Property(lambda, value, options)` 的 `interpolationOptions` 传入，用于引导角度插值方向。

### 静态类：`Eases`

```csharp
public static class Eases
{
    public static IEaseCalculator Default { get; }
    public static class Sine    { public static IEaseCalculator In { get; } /* Out, InOut */ }
    // Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic, Bounce — 结构相同
}
```

具体缓动类（每个 `: IEaseCalculator`）：`EaseDefault`、`EaseInSine`、`EaseOutSine`、`EaseInOutSine`、...、`EaseInOutBounce`。

## 命名空间：`VeloxDev.TransitionSystem.Abstractions`

### 类：`Transition` / `Transition<T>`

```csharp
public abstract class TransitionCore
{
    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}
public class Transition : TransitionCore { }   // 非泛型；适配器子类
public class Transition<T> : TransitionCore<T, Transition<T>.StateSnapshot> { }
public class TransitionCore<TTarget, TStateSnapshotCore> : TransitionCore where TStateSnapshotCore : new()
{
    public static TStateSnapshotCore Create();
    public static void Execute<T>(T target, StateSnapshotCore value, bool CanMutualTask = true) where T : class, TTarget;
    public static void Execute(StateSnapshotCore values, bool CanMutualTask = true);
    public static void Execute<T>(T target, IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false) where T : class, TTarget;
    public static void Execute(IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false);
}
```

### 类：`StateSnapshotCore`（流式构建器）

`Transition<T>.StateSnapshot` 继承自 `StateSnapshotCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter[, TPriorityCore]>`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `Property` | `StateSnapshot Property<T>(Expression<Func<TTarget, T>> lambda, T newValue, object? interpolationOptions = null)` | 记录目标值。每种可动画类型一个重载。 |
| `Effect` | `StateSnapshot Effect(TransitionEffect effect)` / `Effect(Action<TransitionEffect> effectSetter)` | 设置动画时序描述符。 |
| `Await` | `StateSnapshot Await(TimeSpan)` | 本段开始前等待。 |
| `Then` | `StateSnapshot Then()` | 开始下一段。 |
| `AwaitThen` | `StateSnapshot AwaitThen(TimeSpan)` | 等待后开始下一段。 |
| `Interpolator` | `StateSnapshot Interpolator<T>(Expression, IValueInterpolator)` | 按属性插值器覆盖。 |

### 类：`StateCore : IFrameState`

`IFrameState` 的具体实现；`Values`/`Interpolators`/`Options` 为 `public virtual` + `protected set`。适配器的 `State` 由其派生。

### 抽象类：`InterpolatorCore : IFrameInterpolatorCore`

| 成员 | 签名 |
|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, IValueInterpolator> NativeInterpolators { get; protected set; }` |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out IValueInterpolator? interpolator)` |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, IValueInterpolator interpolator)` |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out IValueInterpolator? interpolator)` |

**说明：** 静态构造函数内置数值 + `System.Drawing` + `System.Numerics` 插值器。适配器派生 `Interpolator : InterpolatorCore<InterpolatorOutput[, TPriorityCore]>` 并在静态构造函数中注册平台类型。

### 类：`TransitionEffectCore : ITransitionEffectCore`

默认：`FPS = 60`、`Duration = 0ms`、`Ease = Eases.Default`。事件由 `WeakDelegate` 支撑。适配器 `TransitionEffect : TransitionEffectCore<TPriorityCore>` 设置平台优先级（WPF/Avalonia `DispatcherPriority.Render`、WinUI `DispatcherQueuePriority.Normal`）。

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

### 抽象类：`TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable`

帧泵：遍历帧序列、调用 `effect.InvokeStart/Update/LateUpdate`、应用每帧、尊重 `IsAutoReverse`/`LoopTime`，然后 `InvokeCompleted`/`InvokeCancled`/`InvokeFinally`。`TransitionEventArgs.Handled` 会取消时间线。

### 抽象类：`InterpolatorOutputBase : IFrameSequenceCore`

`Frames`（`Dictionary<ITransitionProperty, List<object?>>`）+ `Count`。`Update(target, frameIndex, isUIAccess, priority)` 把每个属性的帧值写到目标上，需要时调度回 UI 线程。

### 类：`TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public TransitionProperty(IEnumerable<PropertyInfo> segments);   // 空或带索引的属性会抛出异常
public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);
public IReadOnlyList<PropertyInfo> Segments { get; }
```

### 静态类：`TransitionSnapshotHelper`

| 成员 | 签名 |
|---|---|
| `CaptureSpecific` | `void CaptureSpecific<T>(T target, IFrameState state, IEnumerable<Expression<Func<T, object?>>>? expressions) where T : class` |
| `CaptureAll` | `void CaptureAll<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? extraExpressions = null, int maxDepth = 4)` |
| `CaptureAllExcept` | `void CaptureAllExcept<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? excludedExpressions = null, int maxDepth = 4)` |
| `DiscoverAnimatableProperties` | `IReadOnlyCollection<ITransitionProperty> DiscoverAnimatableProperties(object target, Func<Type, bool> canAnimateType, int maxDepth = 4)` |
| `TryGetPropertyFromExpression` | `bool TryGetPropertyFromExpression<T>(Expression<Func<T, object?>> expression, out ITransitionProperty? property) where T : class` |
| `CaptureProperties` | `void CaptureProperties(object target, IFrameState state, IEnumerable<ITransitionProperty> properties)` |

## 命名空间：`VeloxDev.TransitionSystem.NativeInterpolators`

全部实现 `IValueInterpolator.Interpolate(start, end, steps, options)`：

`DoubleInterpolator`（遵循 `RotationDirection` 最短路径角度）、`FloatInterpolator`、`IntInterpolator`、`LongInterpolator`（使用 decimal 防溢出）、`PointInterpolator`、`PointFInterpolator`、`SizeInterpolator`、`SizeFInterpolator`、`RectangleInterpolator`、`RectangleFInterpolator`、`ColorInterpolator`（ARGB 通道插值），以及（非 netstandard2.0）`Vector2Interpolator`、`Vector3Interpolator`、`Vector4Interpolator`、`QuaternionInterpolator`（定向 `Slerp`）。

## 命名空间：`VeloxDev.TransitionSystem`（适配器提供）

### 静态类：`TransitionEx`

```csharp
public static class TransitionEx
{
    public static Transition<T>.StateSnapshot Snapshot<T>(this T target, params Expression<Func<T, object?>>[] expressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotAll<T>(this T target, params Expression<Func<T, object?>>[] extraExpressions) where T : class;
    public static Transition<T>.StateSnapshot SnapshotExcept<T>(this T target, params Expression<Func<T, object?>>[] excludedExpressions) where T : class;
}
```

### 类：`StateSnapshot` — `.Property(...)` 重载集（按适配器）

每个重载：`StateSnapshot Property(Expression<Func<T, X>>, X newValue, object? interpolationOptions = null)`。

| 适配器 | 优先级类型 | 额外重载 | 缺失 |
|---|---|---|---|
| WPF | `DispatcherPriority` | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`CornerRadius`、`Thickness`、`Size`、`Rect`、`Vector`、`Color`、`DropShadowEffect?`、`Point3D`、`Vector3D` | — |
| Avalonia | `DispatcherPriority` | `IInterpolable?`、`ITransform?`、`IBrush?`、`Thickness`、`Point`、`CornerRadius`、`Size`、`PixelPoint`、`PixelSize`、`PixelRect`、`RelativePoint`、`RelativeRect`、`Color`、`BoxShadows` | — |
| WinUI | `DispatcherQueuePriority` | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`CornerRadius`、`Thickness`、`Projection?`、`Size`、`Rect`、`GridLength`、`Color` | — |
| MAUI | 无 | `IInterpolable?`、`Brush?`、`Transform?`、`Point`、`PointF`、`CornerRadius`、`Thickness`、`Color?`、`Size`、`SizeF`、`Rect`、`RectF`、`Shadow?` | `Transform?` 无 `interpolationOptions` |
| WinForms | 无 | `IInterpolable?`、`Padding` | — |
| Razor | 无 | `string?` | 无 `IInterpolable?`；有 `string?` |

所有适配器共有重载：`int`、`double`、`float`、`decimal`、`System.Drawing.*`、以及（非 netstandard2.0）`System.Numerics.*`。

### 平台特定类型

- `UIThreadInspector` — WPF：`Application.Current.Dispatcher`；Avalonia：`Dispatcher.UIThread`；WinUI：**需 `SetWindow(Window)`**；MAUI：`Application.Current.Dispatcher`；WinForms/Razor：`SynchronizationContext` + `CaptureUIThread()`。
- `Interpolator` 静态构造函数注册平台类型（WPF：`Brush`、`Thickness`、`Transform`、`DropShadowEffect`...；Avalonia：`IBrush`、`ITransform`、`BoxShadows`、`GridLength`...；WinUI：`Projection`、`GridLength`...；MAUI：`Shadow`、`RectF`...；WinForms：`Padding`；Razor：`string` → `StringInterpolator`）。
- `TransitionEffects` — 静态预设：`Empty`（0 秒）、`Theme`（0.46 秒）、`Hover`（0.32 秒）。**注意：** WinUI 的 `TransitionEffects` 是非静态类。

## 命名空间：`VeloxDev.TimeLine`

### 类：`TransitionEventArgs : TimeLineEventArgs`

空类型；继承自 `TimeLineEventArgs` 的 `bool Handled { get; set; }`（设为 `true` 会短路动画时间线）。
