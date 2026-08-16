# Transition — Namespace: `VeloxDev.TransitionSystem`

### Interface: `IInterpolable`

```csharp
public interface IInterpolable
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**Returns:** `List<object?>` — the intermediate values for `steps` frames.
**Notes:** Implement this on a value type to make it animatable without registering an interpolator. The engine checks it as a fallback on the current value, then on the new value.
**Verified by:** `NativeInterpolatorsExtendedTests` (a test `TestStringInterpolator` implements `IValueInterpolator`); adapter `Property(Expression<Func<T, IInterpolable?>>, ...)` overloads accept it.

### Interface: `IValueInterpolator`

```csharp
public interface IValueInterpolator
{
    List<object?> Interpolate(object? start, object? end, int steps, object? options = null);
}
```

**Notes:** Implement this to register support for a custom type via `InterpolatorCore.RegisterInterpolator`. `options` carries `RotationDirection` for angular interpolators.
**Verified by:** `InterpolatorCoreTests` (`RegisterInterpolator_And_TryGet_Succeeds`, `RegisterInterpolator_ForCustomType_Succeeds`), `NativeInterpolatorsTests`.

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
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, IValueInterpolator>` |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` |

Plus typed/strongly-named accessors: `SetValue`, `TryGetValue`, `SetInterpolator`, `TryGetInterpolator`, `SetOptions`, `TryGetOptions` — each with three overload families (expression lambda / `ITransitionProperty` / `PropertyInfo`), and `IFrameState Clone()`.
**Verified by:** `StateCoreTests` (`SetValue_Expression_CanRetrieve`, `Clone_ReturnsIndependentCopy`).

### Interface: `ITransitionEffectCore`

| Member | Type / Signature |
|---|---|
| `FPS` | `int FPS { get; set; }` (default 60) |
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
    Task Execute(IFrameInterpolatorCore interpolator, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    void Exit();
}
```

**Notes:** The concrete `TransitionSchedulerCore` exposes `FindOrCreate<T>(T source, bool CanMutualTask = true)`: returns a per-target shared **mutual** scheduler (stored in a `ConditionalWeakTable`) when `CanMutualTask: true`, otherwise a one-off **non-mutual** scheduler that allows parallel animations. Typed variants `ITransitionScheduler` and `ITransitionScheduler<TPriorityCore>` narrow the parameter types.

### Interface: `ITransitionInterpreterCore : IDisposable`

```csharp
public interface ITransitionInterpreterCore : IDisposable
{
    TransitionEventArgs Args { get; set; }
    Task Execute(object target, IFrameSequenceCore frameSequence, ITransitionEffectCore effect, CancellationTokenSource cts);
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
| `ProtectedInterpolate` | `abstract List<object?> ProtectedInterpolate(object target, Func<List<object?>> interpolate)` |

**Notes:** Typed variants `IUIThreadInspector` and `IUIThreadInspector<TPriorityCore>` add `ProtectedInvoke(object, Action)` / `ProtectedInvoke(object, Action, TPriorityCore)`.

### Interface family (frame pump)

| Interface | Key member |
|---|---|
| `IFrameInterpolatorCore` | `IFrameSequenceCore Interpolate(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector)` |
| `IFrameInterpolator : IFrameInterpolatorCore` | `IFrameSequence Interpolate(..., ITransitionEffectCore, IUIThreadInspector)` |
| `IFrameInterpolator<TPriorityCore> : IFrameInterpolatorCore` | `IFrameSequence<TPriorityCore> Interpolate(..., ITransitionEffect<TPriorityCore>, IUIThreadInspector<TPriorityCore>)` |
| `IFrameSequenceCore` | `int Count`; `SetValues(target, frameIndex)`; `Update(target, frameIndex, object? priority = default)`; `AddPropertyInterpolations(property, objects)`; `SetCount(count)` |
| `IFrameSequence : IFrameSequenceCore` | `Update(target, frameIndex)` |
| `IFrameSequence<TPriorityCore> : IFrameSequenceCore` | `Update(target, frameIndex, TPriorityCore priority)` |

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

**Notes:** Passed as the `interpolationOptions` of `.Property(lambda, value, options)` to steer angular interpolation. `DoubleInterpolator` and `QuaternionInterpolator` honor it (`QuaternionInterpolator` negates `q2` to force direction).
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
