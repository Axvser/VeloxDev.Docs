# Transition — Namespace: `VeloxDev.TransitionSystem`

### Interface: `ISampler`

```csharp
public interface ISampler
{
    void Update(object target, ITransitionProperty property, object? start, object? end, object? options, double t);
}
```

**Notes:** Stateless, thread-safe, shared-singleton sampling processor (无状态采样处理器) that **directly updates the property** at normalized time `t ∈ [0, 1]` — it no longer returns a value. Semantics: `t <= 0` writes the exact `start`; `t >= 1` writes the exact `end`; `0 < t < 1` computes-and-assigns for value types and **MUTATES the existing `start` instance in place** for reference types (no new instance). Replaces `IValueInterpolator`/`IInterpolable`. The interpreter applies easing and clamps `t` before invoking. `options` still carries `RotationDirection` for angular samplers.
**Verified by:** `NativeSamplersTests`, `NativeSamplersExtendedTests`.

### Interface: `ISampleable`

```csharp
public interface ISampleable
{
    ISampler Normalize(object? start, object? end, object? options);
}
```

**Notes:** 可采样定义 (sampleable definition) at the **type level**. User-defined types implement it to be directly animatable without registering a sampler. `Normalize` normalizes start/end **once** (called by the interpreter when it is created with the FrameState, per animated property) and returns the stateless `ISampler`. The former `IInPlaceSampler.CreateUpdater` / in-place `FrameUpdater` classes are now the per-type `ISampler.Update`: reference-type samplers mutate `start` in place inside `Update`; value types compute-and-assign.
**Verified by:** `NativeSamplersTests`, `NativeSamplersExtendedTests`.

### Interface: `IEaseCalculator`

```csharp
public interface IEaseCalculator
{
    double Ease(double t);
}
```

**Notes:** `t` is in `[0, 1]`. Return `double` in `[0, 1]` for standard curves (Back/Elastic may overshoot).
**Verified by:** `EasesTests` (`AllStandardEases_AtBoundaries_ReturnExpected`, `QuadIn_IsMonotonicallyIncreasing`).

### Interface: `ITransitionProperty`

| Member | Type | Description |
|---|---|---|
| `Path` | `string` | Dot-separated nested property path (e.g. `"RenderTransform.X"`). |
| `PropertyType` | `Type` | Type of the leaf property. |
| `PropertyInfo` | `PropertyInfo` | Leaf property metadata. |
| `CanRead` / `CanWrite` | `bool` | Whether the whole chain supports reading/writing. |
| `Segments` | `IReadOnlyList<PropertyInfo>` | The property chain (core `TransitionProperty`). |
| `GetValue` | `object? GetValue(object target)` | Read through the chain. |
| `SetValue` | `bool SetValue(object target, object? value)` | Write through the chain. |

**Verified by:** `TransitionPropertyTests` (`GetValue_ReadsFromTarget`, `SetValue_WritesToTarget`, `GetValue_IntermediateTypeMismatch_ReturnsUnreadablePath_NotTargetException`).

### Interface: `IFrameState`

A bag of three `ConcurrentDictionary`s keyed by `ITransitionProperty`:

| Member | Type |
|---|---|
| `Values` | `ConcurrentDictionary<ITransitionProperty, object?>` |
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, ISampleable>` |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` |

Plus typed/strongly-named accessors: `SetValue`, `TryGetValue`, `SetInterpolator`, `TryGetInterpolator`, `SetOptions`, `TryGetOptions` — each with three overload families (expression lambda / `ITransitionProperty` / `PropertyInfo`), and `IFrameState Clone()`. The `SetInterpolator`/`TryGetInterpolator` overloads take/return `ISampleable`.
**Verified by:** `StateCoreTests` (`SetValue_Expression_CanRetrieve`, `Clone_ReturnsIndependentCopy`).

### Interface: `ITransitionEffectCore`

| Member | Type / Signature |
|---|---|
| `FPS` | `int FPS { get; set; }` (default 60) — **maximum sample-rate cap** (yield interval = `1000 / FPS` ms); timing is Stopwatch-driven continuous sampling — FPS bounds how often the loop samples, not a frame grid |
| `Duration` | `TimeSpan Duration { get; set; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` |
| `LoopTime` | `int LoopTime { get; set; }` (`int.MaxValue` = infinite) |
| `Ease` | `IEaseCalculator Ease { get; set; }` |
| Events | `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally` — `EventHandler<TransitionEventArgs>` |
| Invokers | `InvokeAwake`, `InvokeStart`, `InvokeUpdate`, `InvokeLateUpdate`, `InvokeCancled`, `InvokeCompleted`, `InvokeFinally` |
| `Clone` | `ITransitionEffectCore Clone()` |

**Verified by:** `TransitionEffectCoreTests` (`Defaults_AreCorrect`, `Events_AreInvoked`, `Clone_CopiesProperties`).

### Interface: `ITransitionEffect<TPriorityCore> : ITransitionEffectCore`

Adds `TPriorityCore Priority { get; set; }` and `new ITransitionEffect<TPriorityCore> Clone()`.

### Interface: `ITransitionSchedulerCore`

```csharp
public interface ITransitionSchedulerCore
{
    Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**Notes:** The concrete `TransitionSchedulerCore` exposes `FindOrCreate<T>(T source, bool CanMutualTask = true)`: returns a per-target shared **mutual** scheduler (stored in a `ConditionalWeakTable`) when `CanMutualTask: true`, otherwise a one-off **non-mutual** scheduler that allows parallel animations. Typed variants `ITransitionScheduler` and `ITransitionScheduler<TPriorityCore>` narrow the parameter types.

### Interface: `ITransitionInterpreterCore : IDisposable`

```csharp
public interface ITransitionInterpreterCore : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, SamplerSet samplerSet, ITransitionEffectCore effect, CancellationTokenSource cts);
    void Exit();
}
```

### Interface: `IUIThreadInspectorCore`

| Member | Signature |
|---|---|
| `IsAppAlive` | `bool IsAppAlive()` |
| `IsUIThread` | `bool IsUIThread()` |
| `ProtectedInvoke` | `abstract void ProtectedInvoke(object target, Action action, object? priority = default)` |
| `ProtectedGetValue` | `object? ProtectedGetValue(object target, ITransitionProperty property)` |

**Notes:** Typed variants `IUIThreadInspector` and `IUIThreadInspector<TPriorityCore>` add `ProtectedInvoke(object, Action)` / `ProtectedInvoke(object, Action, TPriorityCore)`.

### Interface family (sampler)

| Interface | Key member |
|---|---|
| `ISampler` | `void Update(object target, ITransitionProperty property, object? start, object? end, object? options, double t)` |
| `ISampleable` | `ISampler Normalize(object? start, object? end, object? options)` |

### Enum: `RotationDirection`

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

**Notes:** Passed as the `interpolationOptions` of `.Property(lambda, value, options)` to steer angular interpolation. `DoubleSampler` and `QuaternionSampler` honor it (`QuaternionSampler` negates `q2` to force direction).
**Verified by:** WPF demo `Animation1` passes `RotationDirection.CounterClockWise`.

### Static Class: `Eases`

```csharp
public static class Eases
{
    public static IEaseCalculator Default { get; }   // linear (EaseDefault)
    public static class Sine    { public static IEaseCalculator In { get; } /* Out, InOut */ }
    // Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic, Bounce — same shape
}
```

Concrete ease classes (each `: IEaseCalculator`): `EaseDefault`, `EaseInSine`, `EaseOutSine`, `EaseInOutSine`, `EaseInQuad`, `EaseOutQuad`, `EaseInOutQuad`, `EaseInCubic`, `EaseOutCubic`, `EaseInOutCubic`, `EaseInQuart`, `EaseOutQuart`, `EaseInOutQuart`, `EaseInQuint`, `EaseOutQuint`, `EaseInOutQuint`, `EaseInExpo`, `EaseOutExpo`, `EaseInOutExpo`, `EaseInCirc`, `EaseOutCirc`, `EaseInOutCirc`, `EaseInBack`, `EaseOutBack`, `EaseInOutBack`, `EaseInElastic`, `EaseOutElastic`, `EaseInOutElastic`, `EaseInBounce`, `EaseOutBounce`, `EaseInOutBounce`.
**Verified by:** `EasesTests`.
