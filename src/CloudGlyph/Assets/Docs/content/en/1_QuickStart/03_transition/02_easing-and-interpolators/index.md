# Transition — Easing & Interpolators

## 1. Pick a built-in easing

`Eases` (namespace `VeloxDev.TransitionSystem`) is a static factory over `IEaseCalculator`. Assign one to an effect's `Ease` property — `TransitionEffectCore.Ease` defaults to `Eases.Default` (linear):

| Group | `In` | `Out` | `InOut` |
|---|---|---|---|
| linear | `Eases.Default` | — | — |
| Sine / Quad / Cubic / Quart / Quint / Expo / Circ / Back / Elastic / Bounce | `Eases.{Group}.In` | `Eases.{Group}.Out` | `Eases.{Group}.InOut` |

For example `Eases.Circ.InOut`, `Eases.Expo.Out`, `Eases.Back.Out` and `Eases.Bounce.Out` are used by the demos. Every built-in `Ease*` class is `public` too, so `new EaseInOutCubic()` is equivalent to `Eases.Cubic.InOut`.

```csharp
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

public static class QuickStart
{
    public static readonly Transition<Rectangle> SlideAndFade =
        Transition<Rectangle>.Create()
            .Property(r => r.Opacity, 0)
            .Property(r => ((TranslateTransform)r.RenderTransform).X, 800)
            .Effect(e => e.Ease = Eases.Back.Out);   // fluent effect setter
}
```

**Expected result:** an effect whose `Ease` is `Eases.Back.Out`; the `Back` curve overshoots the target then settles, and the frame sampler clamps `t` to `[0,1]` before writing a value.

## 2. Define a custom easing

An easing is one method — `double Ease(double t)` mapping normalized time `t ∈ [0,1]` to an eased value. Implement `IEaseCalculator` and assign an instance to `Effect.Ease`:

```csharp
using VeloxDev.TransitionSystem;

public sealed class FlashEase : IEaseCalculator
{
    public double Ease(double t)
    {
        // A single light flash at the start of the transition.
        return t < 0.5 ? 4 * t * t * t : 1 - Math.Pow(-2 * t + 2, 3) / 2;
    }
}
```

```csharp
Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 1)
    .Effect(new TransitionEffect
    {
        Duration = TimeSpan.FromSeconds(1),
        Ease = new FlashEase(),
    });
```

**Expected result:** during the one-second effect the opacity is sampled through `FlashEase.Ease`, so the value accelerates in, holds near the end, then completes.

## 3. Define or override a sampler (`ISampler`)

While `Ease` reshapes *time*, a sampler (`ISampler`) reshapes the *value* between the normalized endpoints. A sampler is a stateless singleton with three methods:

- `NormalizeStart(start, end, options)` — value written at `t <= 0` (default: `start` as-is).
- `NormalizeEnd(start, end, options)` — value written at `t >= 1` (default: `end` as-is).
- `InsertFrame(target, property, ref working, start, end, options, t)` — interpolate `start → end` at eased time `t` and write it. Implementations must never mutate `start` / `end` (they are shared with the transition declaration that recorded them).

The engine-core registrations live in `InterpolatorCore` (the `NativeInterpolators` dictionary) and cover `double`, `float`, `int`, `long`, `Point`, `PointF`, `Size`, `SizeF`, `Color`, `Rectangle`, `RectangleF` and — off `netstandard2.0` — `Vector2/3/4`, `Quaternion`. Each GUI adapter registers its own framework samplers (e.g. WPF adds `Brush`, `Thickness`, `CornerRadius`, `Transform`, `DropShadowEffect`, `Point3D`, `Vector3D`). A custom sampler is registered or removed with the static registry API:

```csharp
using VeloxDev.TransitionSystem;

public sealed class SmoothStepDoubleSampler : ISampler
{
    public object? NormalizeStart(object? start, object? end, object? options) => start;
    public object? NormalizeEnd(object? start, object? end, object? options) => end;

    public void InsertFrame(object target, ITransitionProperty property, ref object? working,
        object? start, object? end, object? options, double t)
    {
        if (t <= 0) { property.SetValue(target, start); return; }
        if (t >= 1) { property.SetValue(target, end); return; }

        var d1 = (double)(start ?? 0d);
        var d2 = (double)(end ?? d1);
        var s = t * t * (3 - 2 * t); // smoothstep: 3t^2 - 2t^3
        property.SetValue(target, d1 + (d2 - d1) * s);
    }
}
```

```csharp
// Process-wide opt-in: every double-typed property now interpolates with smoothstep.
InterpolatorCore.RegisterInterpolator(typeof(double), new SmoothStepDoubleSampler());
// InterpolatorCore.UnregisterInterpolator(typeof(double), out _);  // restore the default
```

Registration is last-writer-wins on the key you write, but **lookup is not an exact-type match**. `InterpolatorCore.TryGetInterpolator` (source: `Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`) resolves a property's type in three steps: the **exact type** first, then its **base classes nearest-first**, then its **interfaces ordered by full name (ordinal)**. The fallback is there because a framework property is very often declared as a subclass of what the adapter registered — WPF registers `Brush`, while a property may be declared `LinearGradientBrush` — so an exact match alone would leave that property unanimated (and, for a reference-typed leaf, make it fail `TransitionPathUnsampleableException` instead). Two consequences for a registration of your own:

- **Register the general type.** A registered general type must handle its whole family, because every subclass now resolves to it; a concrete-type registration is redundant once a base class or an interface is registered.
- **Interface order is a tie-break, not a preference.** Interfaces come last and are ordered by name only because reflection's own order is not specified: which of two matching interfaces wins is arbitrary, but that the same one wins every time is not.

The walk runs **once per property, when the animation starts** (`InterpolatorCore.Prepare`) — never per frame.

Rotation direction is the one per-property *option* you can pass through `Property` without writing a sampler: numeric paths that represent an angle honor `RotationDirection` (e.g. `RotationDirection.CounterClockWise`), because `DoubleSampler.InsertFrame` reads the `options` argument and steers the wrap-around (see [Declare State Explicitly](../03_declare-state/index.md)).

**Expected result:** registering the sampler makes an exact lookup of `typeof(double)` return it (last-writer-wins), so the next animation of a `double`-typed property uses smoothstep until you unregister it — and, in the other direction, a sampler registered for a base class or an interface now serves every property type declared below it. Per-property overrides take precedence over the registry — attach one with the `TransitionCoreEx.Interpolator(propertyLambda, sampler)` extension (`namespace VeloxDev.TransitionSystem`) if you need a single property to animate differently.
