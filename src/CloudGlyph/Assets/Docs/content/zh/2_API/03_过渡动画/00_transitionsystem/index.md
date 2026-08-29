# Transition — 命名空间：`VeloxDev.TransitionSystem`

### 接口：`ISampler`

```csharp
public interface ISampler
{
    void Update(object target, ITransitionProperty property, object? start, object? end, object? options, double t);
}
```

**说明：** 无状态、线程安全的共享单例采样处理器：不返回值，直接更新属性。语义：`t <= 0` 写精确 `start`；`t >= 1` 写精确 `end`；`0 < t < 1` 时值类型算好即赋、引用类型**原地修改** `start` 现有实例（不 new）。取代 `IValueInterpolator`/`IInterpolable`/`IInPlaceSampler`/`IFrameUpdater`。`options` 仍携带 `RotationDirection` 供角度采样器使用。
**验证依据：** `InterpolatorCoreTests`（`RegisterInterpolator_And_TryGet_Succeeds`、`RegisterInterpolator_ForCustomType_Succeeds`）、`NativeSamplersTests`、`NativeSamplersExtendedTests`。

### 接口：`ISampleable`

```csharp
public interface ISampleable
{
    ISampler Normalize(object? start, object? end, object? options);
}
```

**说明：** 可采样定义（类型级）：用户自定义类型实现它即可直接用于动画，无需注册采样器。`Normalize` 归一化 start/end/options——解释器创建并知晓 `FrameState` 时对每个动画属性调用一次，返回该类型的无状态 `ISampler`；`start` 为 target 上的现值（引用类型即现有实例，供原地修改），`end` 为目标值。取代 `IInPlaceSampler`/`IFrameUpdater`/`IFrameUpdaterProducer`（引用类型的原地修改逻辑现在在各自 `ISampler.Update` 内）。
**验证依据：** `InterpolatorCoreTests`、`SamplingLoopTests`。

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
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, ISampleable>` |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` |

另有强类型访问器：`SetValue`、`TryGetValue`、`SetInterpolator`、`TryGetInterpolator`、`SetOptions`、`TryGetOptions` —— 每种都有三种重载族（表达式 lambda / `ITransitionProperty` / `PropertyInfo`），以及 `IFrameState Clone()`。`SetInterpolator`/`TryGetInterpolator` 重载接受/返回 `ISampleable`。
**验证依据：** `StateCoreTests`（`SetValue_Expression_CanRetrieve`、`Clone_ReturnsIndependentCopy`）。

### 接口：`ITransitionEffectCore`

| 成员 | 类型 / 签名 |
|---|---|
| `FPS` | `int FPS { get; set; }`（默认 60）——最大采样率上限（yield 间隔 = `1000 / FPS` ms）；计时为 Stopwatch 连续采样——FPS 只限制采样频率，不是帧网格 |
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
    Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**说明：** 具体 `TransitionSchedulerCore` 暴露 `FindOrCreate<T>(T source, bool CanMutualTask = true)`：在 `CanMutualTask: true` 时返回按目标共享的**互斥**调度器（存于 `ConditionalWeakTable`），否则返回允许并行动画的一次性**非互斥**调度器。类型化变体 `ITransitionScheduler` 与 `ITransitionScheduler<TPriorityCore>` 收窄参数类型。

### 接口：`ITransitionInterpreterCore : IDisposable`

```csharp
public interface ITransitionInterpreterCore : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, SamplerSet samplerSet, ITransitionEffectCore effect, CancellationTokenSource cts);
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

**说明：** 类型化变体 `IUIThreadInspector` 与 `IUIThreadInspector<TPriorityCore>` 增加 `ProtectedInvoke(object, Action)` / `ProtectedInvoke(object, Action, TPriorityCore)`。

### 接口家族（采样器）

| 接口 | 关键成员 |
|---|---|
| `ISampler` | `void Update(object target, ITransitionProperty property, object? start, object? end, object? options, double t)` |
| `ISampleable` | `ISampler Normalize(object? start, object? end, object? options)` |

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

**说明：** 作为 `.Property(lambda, value, options)` 的 `interpolationOptions` 传入，用于引导角度采样方向。`DoubleSampler` 与 `QuaternionSampler` 都会遵循它（`QuaternionSampler` 通过取反 `q2` 强制方向）。
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
