# Transition — 命名空间：`VeloxDev.TransitionSystem`

### 接口：`IInterpolable`

```csharp
public interface IInterpolable
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**返回：** `List<object?>` — `steps` 帧的中间值。
**说明：** 在值类型上实现此接口即可使其可动画，而无需注册插值器。引擎会作为回退先检查当前值上的实现，再检查新值上的实现。
**验证依据：** `NativeInterpolatorsExtendedTests`（测试用 `TestStringInterpolator` 实现 `IValueInterpolator`）；适配器的 `Property(Expression<Func<T, IInterpolable?>>, ...)` 重载接受它。

### 接口：`IValueInterpolator`

```csharp
public interface IValueInterpolator
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**说明：** 实现此接口可通过 `InterpolatorCore.RegisterInterpolator` 注册自定义类型支持。`options` 携带 `RotationDirection` 供角度插值器使用。
**验证依据：** `InterpolatorCoreTests`（`RegisterInterpolator_And_TryGet_Succeeds`、`RegisterInterpolator_ForCustomType_Succeeds`）、`NativeInterpolatorsTests`。

### 接口：`IEaseCalculator`

```csharp
public interface IEaseCalculator
{
    double Ease(double t);
}
```

**说明：** `t` 取值 `[0, 1]`。标准曲线返回 `[0, 1]`（Back/Elastic 可能过冲）。
**验证依据：** `EasesTests`（`AllStandardEases_AtBoundaries_ReturnExpected`、`QuadIn_IsMonotonicallyIncreasing`）。

### 接口：`ITransitionProperty`

| 成员 | 类型 | 描述 |
|---|---|---|
| `Path` | `string` | 点分隔的嵌套属性路径（如 `"RenderTransform.X"`）。 |
| `PropertyType` | `Type` | 叶子属性类型。 |
| `PropertyInfo` | `PropertyInfo` | 叶子属性元数据。 |
| `CanRead` / `CanWrite` | `bool` | 整个链是否支持读取/写入。 |
| `Segments` | `IReadOnlyList<PropertyInfo>` | 属性链（核心 `TransitionProperty`）。 |
| `GetValue` | `object? GetValue(object target)` | 沿链读取。 |
| `SetValue` | `bool SetValue(object target, object? value)` | 沿链写入。 |

**验证依据：** `TransitionPropertyTests`（`GetValue_ReadsFromTarget`、`SetValue_WritesToTarget`、`GetValue_IntermediateTypeMismatch_ReturnsUnreadablePath_NotTargetException`）。

### 接口：`IFrameState`

以 `ITransitionProperty` 为键的三个 `ConcurrentDictionary`：

| 成员 | 类型 |
|---|---|
| `Values` | `ConcurrentDictionary<ITransitionProperty, object?>` |
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, IValueInterpolator>` |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` |

另有强类型访问器：`SetValue`、`TryGetValue`、`SetInterpolator`、`TryGetInterpolator`、`SetOptions`、`TryGetOptions` —— 每种都有三种重载族（表达式 lambda / `ITransitionProperty` / `PropertyInfo`），以及 `IFrameState Clone()`。
**验证依据：** `StateCoreTests`（`SetValue_Expression_CanRetrieve`、`Clone_ReturnsIndependentCopy`）。

### 接口：`ITransitionEffectCore`

| 成员 | 类型 / 签名 |
|---|---|
| `FPS` | `int FPS { get; set; }`（默认 60） |
| `Duration` | `TimeSpan Duration { get; set; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` |
| `LoopTime` | `int LoopTime { get; set; }`（`int.MaxValue` = 无限） |
| `Ease` | `IEaseCalculator Ease { get; set; }` |
| 事件 | `Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally` — `EventHandler<TransitionEventArgs>` |
| 调用器 | `InvokeAwake`、`InvokeStart`、`InvokeUpdate`、`InvokeLateUpdate`、`InvokeCancled`、`InvokeCompleted`、`InvokeFinally` |
| `Clone` | `ITransitionEffectCore Clone()` |

**验证依据：** `TransitionEffectCoreTests`（`Defaults_AreCorrect`、`Events_AreInvoked`、`Clone_CopiesProperties`）。

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

**说明：** 具体 `TransitionSchedulerCore` 暴露 `FindOrCreate<T>(T source, bool CanMutualTask = true)`：在 `CanMutualTask: true` 时返回按目标共享的**互斥**调度器（存于 `ConditionalWeakTable`），否则返回允许并行动画的一次性**非互斥**调度器。类型化变体 `ITransitionScheduler` 与 `ITransitionScheduler<TPriorityCore>` 收窄参数类型。

### 接口：`ITransitionInterpreterCore : IDisposable`

```csharp
public interface ITransitionInterpreterCore : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, IFrameSequenceCore frameSequence, ITransitionEffectCore effect, CancellationTokenSource cts);
    void Exit();
}
```

### 接口：`IUIThreadInspectorCore`

| 成员 | 签名 |
|---|---|
| `IsAppAlive` | `bool IsAppAlive()` |
| `IsUIThread` | `bool IsUIThread()` |
| `ProtectedInvoke` | `abstract void ProtectedInvoke(object target, Action action, object? priority = default)` |
| `ProtectedGetValue` | `object? ProtectedGetValue(object target, ITransitionProperty property)` |
| `ProtectedInterpolate` | `abstract List<object?> ProtectedInterpolate(object target, Func<List<object?>> interpolate)` |

**说明：** 类型化变体 `IUIThreadInspector` 与 `IUIThreadInspector<TPriorityCore>` 增加 `ProtectedInvoke(object, Action)` / `ProtectedInvoke(object, Action, TPriorityCore)`。

### 接口家族（帧泵）

| 接口 | 关键成员 |
|---|---|
| `IFrameInterpolatorCore` | `IFrameSequenceCore Interpolate(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector)` |
| `IFrameInterpolator : IFrameInterpolatorCore` | `IFrameSequence Interpolate(..., ITransitionEffectCore, IUIThreadInspector)` |
| `IFrameInterpolator<TPriorityCore> : IFrameInterpolatorCore` | `IFrameSequence<TPriorityCore> Interpolate(..., ITransitionEffect<TPriorityCore>, IUIThreadInspector<TPriorityCore>)` |
| `IFrameSequenceCore` | `int Count`；`SetValues(target, frameIndex)`；`Update(target, frameIndex, object? priority = default)`；`AddPropertyInterpolations(property, objects)`；`SetCount(count)` |
| `IFrameSequence : IFrameSequenceCore` | `Update(target, frameIndex)` |
| `IFrameSequence<TPriorityCore> : IFrameSequenceCore` | `Update(target, frameIndex, TPriorityCore priority)` |

### 枚举：`RotationDirection`

```csharp
[Flags]
public enum RotationDirection
{
    Auto = 0, ClockWise = 1 << 0, CounterClockWise = 1 << 1,
    ClockWiseX = 1 << 2, CounterClockWiseX = 1 << 3,
    ClockWiseY = 1 << 4, CounterClockWiseY = 1 << 5,
    ClockWiseZ = 1 << 6, CounterClockWiseZ = 1 << 7,
}
```

**说明：** 作为 `.Property(lambda, value, options)` 的 `interpolationOptions` 传入，用于引导角度插值方向。`DoubleInterpolator` 与 `QuaternionInterpolator` 都会遵循它（`QuaternionInterpolator` 通过取反 `q2` 强制方向）。
**验证依据：** WPF 示例 `Animation1` 传入 `RotationDirection.CounterClockWise`。

### 静态类：`Eases`

```csharp
public static class Eases
{
    public static IEaseCalculator Default { get; }   // 线性（EaseDefault）
    public static class Sine    { public static IEaseCalculator In { get; } /* Out, InOut */ }
    // Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic, Bounce — 结构相同
}
```

具体缓动类（每个 `: IEaseCalculator`）：`EaseDefault`、`EaseInSine`、`EaseOutSine`、`EaseInOutSine`、`EaseInQuad`、`EaseOutQuad`、`EaseInOutQuad`、`EaseInCubic`、`EaseOutCubic`、`EaseInOutCubic`、`EaseInQuart`、`EaseOutQuart`、`EaseInOutQuart`、`EaseInQuint`、`EaseOutQuint`、`EaseInOutQuint`、`EaseInExpo`、`EaseOutExpo`、`EaseInOutExpo`、`EaseInCirc`、`EaseOutCirc`、`EaseInOutCirc`、`EaseInBack`、`EaseOutBack`、`EaseInOutBack`、`EaseInElastic`、`EaseOutElastic`、`EaseInOutElastic`、`EaseInBounce`、`EaseOutBounce`、`EaseInOutBounce`。
**验证依据：** `EasesTests`。
