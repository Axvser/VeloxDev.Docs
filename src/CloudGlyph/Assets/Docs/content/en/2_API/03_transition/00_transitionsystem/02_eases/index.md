# Transition — Rotation Direction & Eases

Namespace `VeloxDev.TransitionSystem`. The remaining members of the core namespace: the `RotationDirection` flag enum steering angular interpolation, and the `Eases` factory plus its 31 concrete ease classes (all implementing `IEaseCalculator`).

### Enum: `RotationDirection`

```csharp
[Flags]
public enum RotationDirection
{
    Auto = 0,
    ClockWise = 1 << 0,
    CounterClockWise = 1 << 1,
    ClockWiseX = 1 << 2,
    CounterClockWiseX = 1 << 3,
    ClockWiseY = 1 << 4,
    CounterClockWiseY = 1 << 5,
    ClockWiseZ = 1 << 6,
    CounterClockWiseZ = 1 << 7,
}
```

**Notes:**
- `[Flags]` — members combine bitwise so per-axis direction can be expressed; the axis-specific values apply to 3-D rotation.
- Passed as the `interpolationOptions` argument of `Property(lambda, value, options)` (recorded in `IFrameState.Options`) and read by the angular samplers: `DoubleSampler` and `QuaternionSampler` honor it (`QuaternionSampler` negates `q2` to force the requested direction, per axis); other samplers ignore it.
- *Verified by:* WPF demo `Animation1` passes `RotationDirection.CounterClockWise` (`Examples/Transition/WPF/Demo/MainWindow.xaml.cs`).

### Interface: `IEaseCalculator`

```csharp
public interface IEaseCalculator
{
    double Ease(double t);
}
```

**Notes:** `t` is the normalized time in `[0, 1]`. Standard curves return a value in `[0, 1]`; `Back` and `Elastic` may overshoot, and the sampling loop clamps the eased result back to `[0, 1]`.

### Static Class: `Eases`

`Eases` exposes `Default` (linear) plus one nested factory class per named curve; each nested class exposes `In`, `Out`, and `InOut` static read-only properties:

| Factory | In | Out | InOut |
|---|---|---|---|
| `Eases.Sine` | `EaseInSine` | `EaseOutSine` | `EaseInOutSine` |
| `Eases.Quad` | `EaseInQuad` | `EaseOutQuad` | `EaseInOutQuad` |
| `Eases.Cubic` | `EaseInCubic` | `EaseOutCubic` | `EaseInOutCubic` |
| `Eases.Quart` | `EaseInQuart` | `EaseOutQuart` | `EaseInOutQuart` |
| `Eases.Quint` | `EaseInQuint` | `EaseOutQuint` | `EaseInOutQuint` |
| `Eases.Expo` | `EaseInExpo` | `EaseOutExpo` | `EaseInOutExpo` |
| `Eases.Circ` | `EaseInCirc` | `EaseOutCirc` | `EaseInOutCirc` |
| `Eases.Back` | `EaseInBack` | `EaseOutBack` | `EaseInOutBack` |
| `Eases.Elastic` | `EaseInElastic` | `EaseOutElastic` | `EaseInOutElastic` |
| `Eases.Bounce` | `EaseInBounce` | `EaseOutBounce` | `EaseInOutBounce` |

```csharp
public static class Eases
{
    public static IEaseCalculator Default { get; }        // linear, new EaseDefault()
    public static class Sine
    {
        public static IEaseCalculator In { get; }
        public static IEaseCalculator Out { get; }
        public static IEaseCalculator InOut { get; }
    }
    // Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic, Bounce — same shape
}
```

**Notes:** The factory properties construct a fresh ease instance on every access (computed getters), so they are cheap but not singletons. All factories and the concrete classes are public.

### Concrete Ease Classes

Each concrete class implements `IEaseCalculator` with a single `double Ease(double t)` member:

`EaseDefault`, `EaseInSine`, `EaseOutSine`, `EaseInOutSine`, `EaseInQuad`, `EaseOutQuad`, `EaseInOutQuad`, `EaseInCubic`, `EaseOutCubic`, `EaseInOutCubic`, `EaseInQuart`, `EaseOutQuart`, `EaseInOutQuart`, `EaseInQuint`, `EaseOutQuint`, `EaseInOutQuint`, `EaseInExpo`, `EaseOutExpo`, `EaseInOutExpo`, `EaseInCirc`, `EaseOutCirc`, `EaseInOutCirc`, `EaseInBack`, `EaseOutBack`, `EaseInOutBack`, `EaseInElastic`, `EaseOutElastic`, `EaseInOutElastic`, `EaseInBounce`, `EaseOutBounce`, `EaseInOutBounce`.

**Notes:**
- `EaseDefault.Ease(t) => t` (linear). The standard easing formula set (Robert Penner style) is implemented in `Eases.cs` (`Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`).
- *Verified by:* `EasesTests` (`Default_AtZero_ReturnsZero`, `Default_AtOne_ReturnsOne`, `AllStandardEases_AtBoundaries_ReturnExpected`, `QuadIn_IsMonotonicallyIncreasing`, `InOutQuad_Symmetry_AtHalf`, `*_FactoryProperties_ReturnNonNull`).

### Other Members of `VeloxDev.TransitionSystem`

Two more public types share this namespace but are documented with the builder / adapter surfaces they belong to:

- `TransitionCoreEx` — static extension methods (`Await`, `Then`, `AwaitThen`, `Interpolator`, `Execute`) that build and run `StateSnapshotCore` chains → [01_abstractions](../../01_abstractions/index.md).
- Per-adapter `TransitionEx`, `Transition`, `Transition<T>`, `Transition<T>.StateSnapshot` → [03_adapter-provided](../../03_adapter-provided/index.md).
