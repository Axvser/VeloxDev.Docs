# Transition — Namespace: `VeloxDev.TransitionSystem.NativeSamplers`

Built-in samplers shipped by `VeloxDev.Core` (source: `Src/Core/VeloxDev.Core/TransitionSystem/NativeSamplers/*.cs`). They are registered in `InterpolatorCore`'s static constructor and implement the `ISampler` contract from [transitionsystem/sampling-capture](../00_transitionsystem/00_sampling-capture/index.md).

All samplers share one shape:

```csharp
public class DoubleSampler : ISampler
{
    public object? NormalizeStart(object? start, object? end, object? options) => start;
    public object? NormalizeEnd(object? start, object? end, object? options) => end;

    public void InsertFrame(object target, ITransitionProperty property, ref object? working,
        object? start, object? end, object? options, double t)
    {
        // compute between start and end at t, then write the result
    }
}
```

## Shared semantics

- **Stateless & shared**: the classes are stateless singletons — they never mutate `start` / `end` and ignore the `working` scratch parameter (they allocate the interpolated value inline, e.g. `new Size(...)`, `Color.FromArgb(...)`, `Quaternion.Slerp(...)`).
- **Exact endpoints**: the pipeline drives the last frame of every pass with exactly `1` (forward) or `0` (reverse). For the numeric samplers a lerp at `t = 0` / `t = 1` reproduces the endpoint exactly, so no guard is needed; `QuaternionSampler` returns the caller's **own** `start` / `end` instance at exactly `0` / `1`, because a nested path such as `((TranslateTransform)x.RenderTransform).X` depends on the runtime type the transform was declared with, and an interpolated replacement would lose it.
- **Null starts / ends**: each sampler substitutes its type's zero/identity (e.g. `0d`, `default(Color)`, `default(Vector2)`, `Quaternion.Identity`) when the corresponding endpoint is null.
- **Options**: only the angular samplers read `options` (a `RotationDirection`).
- **Overshoot**: `t` arrives unclamped, so an overshooting ease can push a sampler past its endpoint. What that means is decided per value type — see the *bounded groups* below.

## Bounded channel groups (`BoundedProgress`)

Five samplers interpolate a **group** of channels with one shared progress rather than channel by channel, so an overshoot cannot distort the value: `ColorSampler` (R/G/B share one `[0, 255]` progress, alpha keeps its own time), `SizeSampler` / `SizeFSampler` (width/height share one `[0, +∞)` progress) and `RectangleSampler` / `RectangleFSampler` (width/height share one `[0, +∞)` progress; the origin stays unbounded). They go through `BoundedProgress` — the same quantity the `AUTO TEST` conformance suite re-derives independently in `Conformance/ClosedForm.SharedProgress` / `ColorAt`. `ColorSampler.Channel` **saturates** at `0` / `255` rather than wrapping (a bare `(byte)` cast turns 300 into 44) and truncates in range, matching the framework's own byte conversion.

## Sampler catalog

| Sampler | Value type | Behavior notes | Verified by |
|---|---|---|---|
| `DoubleSampler` | `double` | Linear lerp. When `options` is a non-`Auto` `RotationDirection`, uses the shortest-path angle delta (mod-360 delta corrected for `ClockWise` / `CounterClockWise`). `null` start → `0d`. | `NativeSamplersTests` (`DoubleSampler_BasicLinear`, `DoubleSampler_Endpoints_AreExact`, `DoubleSampler_NullStart_TreatsAsZero`, `DoubleSampler_Quarters_AreCorrect`, `NormalizeEndpoints_ReturnStartAndEnd_ForStatelessSampler`) |
| `FloatSampler` | `float` | Linear float lerp. | `NativeSamplersTests` (`FloatSampler_BasicLinear`) |
| `IntSampler` | `int` | Integer lerp with `Math.Round`; equal endpoints short-circuit. | `SamplerConformanceTests` (closed form), `InterpolatorCoreTests` (`TheDefaultsAreRegistered`) |
| `LongSampler` | `long` | Uses `decimal` intermediate math to avoid overflow for large ranges. | `NativeSamplersTests` (`LongSampler_BasicLinear`, `LongSampler_SameStartEnd_AllSame`) |
| `PointSampler` | `System.Drawing.Point` | X/Y lerp, `(int)Math.Round`. | `NativeSamplersExtendedTests` (`PointSampler_BasicLinear`) |
| `PointFSampler` | `System.Drawing.PointF` | X/Y float lerp. | `NativeSamplersExtendedTests` (`PointFSampler_BasicLinear`) |
| `SizeSampler` | `System.Drawing.Size` | Width/height share one progress bounded at zero; `(int)Math.Round`. | `NativeSamplersExtendedTests` (`SizeSampler_BasicLinear`), `SamplerConformanceTests`, `EaseOvershootTests` |
| `SizeFSampler` | `System.Drawing.SizeF` | Width/height share one progress bounded at zero. | `NativeSamplersExtendedTests` (`SizeFSampler_BasicLinear`) |
| `RectangleSampler` | `System.Drawing.Rectangle` | X/Y lerp; width/height share one progress bounded at zero; `(int)Math.Round`. | `NativeSamplersExtendedTests` (`RectangleSampler_BasicLinear`) |
| `RectangleFSampler` | `System.Drawing.RectangleF` | X/Y lerp; width/height share one progress bounded at zero. | `NativeSamplersExtendedTests` (`RectangleFSampler_BasicLinear`) |
| `ColorSampler` | `System.Drawing.Color` | R/G/B share one `[0, 255]` progress and saturate; alpha keeps the full eased time. Channel values are truncated in range (matching the framework's byte conversion). | `NativeSamplersExtendedTests` (`ColorSampler_BasicLinear`, `ColorSampler_NullStart_UsesDefault`), `EaseOvershootTests`, `AUTO TEST` `EverySamplerMatchesItsClosedForm` |
| `Vector2Sampler` | `System.Numerics.Vector2` | `v1 + (v2 - v1) * t`. `null` start → `default(Vector2)`. | `NativeSamplersExtendedTests` (`Vector2Sampler_BasicLinear`) |
| `Vector3Sampler` | `System.Numerics.Vector3` | `v1 + (v2 - v1) * t`. | `NativeSamplersExtendedTests` (`Vector3Sampler_BasicLinear`) |
| `Vector4Sampler` | `System.Numerics.Vector4` | `v1 + (v2 - v1) * t`. | `NativeSamplersExtendedTests` (`Vector4Sampler_BasicLinear`) |
| `QuaternionSampler` | `System.Numerics.Quaternion` | Returns the caller's own instance at exactly `t == 0` / `t == 1`; otherwise directional `Quaternion.Slerp`. `Auto` = shortest path; `ClockWise` / `CounterClockWise` negate `q2` when the dot product has the wrong sign (per-axis flags supported). `null` start → `Quaternion.Identity`. | `NativeSamplersExtendedTests` (`QuaternionSampler_BasicSlerp`, `QuaternionSampler_NullStart_UsesIdentity`), `QuaternionOvershootTests` |

## Caveats

- The `System.Numerics` samplers (`Vector2Sampler`, `Vector3Sampler`, `Vector4Sampler`, `QuaternionSampler`) are compiled only under `#if !NETSTANDARD2_0` — they are absent on `netstandard2.0`.
- There is no per-type frame counter: endpoint handling is part of `InsertFrame`, and `FPS` in the effect is only a maximum sample-rate cap applied by the interpreter loop (see [abstractions](../01_abstractions/01_engine/index.md)).
- Platform adapters register *additional* platform samplers of their own (brushes, transforms, grids, padding, ...) — see [adapter-provided](../03_adapter-provided/index.md).
