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
        if (t <= 0) { property.SetValue(target, start); return; }   // exact start
        if (t >= 1) { property.SetValue(target, end); return; }     // exact end
        // middle frames: compute between start and end, write the result
    }
}
```

## Shared semantics

- **Stateless & shared**: the classes are stateless singletons — they never mutate `start` / `end` and ignore the `working` scratch parameter (they allocate the interpolated value inline, e.g. `new Point(...)` / `Color.FromArgb(...)` / `Quaternion.Slerp(...)`).
- **Endpoints handled in `InsertFrame`**: `t <= 0` writes the exact (normalized) start, `t >= 1` writes the exact end; only `0 < t < 1` computes a middle frame.
- **Null starts / ends**: each sampler substitutes its type's zero/identity (e.g. `0d`, `default(Color)`, `default(Vector2)`, `Quaternion.Identity`) when the corresponding endpoint is null.
- **Options**: only the angular samplers read `options` (a `RotationDirection`).

## Sampler catalog

| Sampler | Value type | Behavior notes | Verified by |
|---|---|---|---|
| `DoubleSampler` | `double` | Linear lerp. When `options` is a non-`Auto` `RotationDirection`, uses the shortest-path angle delta (mod-360 delta corrected for `ClockWise` / `CounterClockWise`). `null` start → `0d`. | `NativeSamplersTests` (`DoubleSampler_BasicLinear`, `DoubleSampler_Endpoints_AreExact`, `DoubleSampler_NullStart_TreatsAsZero`, `DoubleSampler_Quarters_AreCorrect`, `NormalizeEndpoints_ReturnStartAndEnd_ForStatelessSampler`) |
| `FloatSampler` | `float` | Linear float lerp. | `NativeSamplersTests` (`FloatSampler_BasicLinear`) |
| `IntSampler` | `int` | Integer lerp with `Math.Round`. | `InterpolatorCoreTests` (`NativeInterpolators_ContainsDefaults`, registry only) |
| `LongSampler` | `long` | Uses decimal intermediate math to avoid overflow for large ranges. | `NativeSamplersTests` (`LongSampler_BasicLinear`, `LongSampler_SameStartEnd_AllSame`) |
| `PointSampler` | `System.Drawing.Point` | X/Y lerp, `(int)Math.Round`. | `NativeSamplersExtendedTests` (`PointSampler_BasicLinear`) |
| `PointFSampler` | `System.Drawing.PointF` | X/Y float lerp. | `NativeSamplersExtendedTests` (`PointFSampler_BasicLinear`) |
| `SizeSampler` | `System.Drawing.Size` | Width/Height lerp, `(int)Math.Round`. | `NativeSamplersExtendedTests` (`SizeSampler_BasicLinear`) |
| `SizeFSampler` | `System.Drawing.SizeF` | Width/Height float lerp. | `NativeSamplersExtendedTests` (`SizeFSampler_BasicLinear`) |
| `RectangleSampler` | `System.Drawing.Rectangle` | X/Y/Width/Height lerp, `(int)Math.Round`. | `NativeSamplersExtendedTests` (`RectangleSampler_BasicLinear`) |
| `RectangleFSampler` | `System.Drawing.RectangleF` | X/Y/Width/Height float lerp. | `NativeSamplersExtendedTests` (`RectangleFSampler_BasicLinear`) |
| `ColorSampler` | `System.Drawing.Color` | Per-channel ARGB lerp via `Color.FromArgb`. Channel values are `(byte)`-cast (truncation, not rounding — see test). | `NativeSamplersExtendedTests` (`ColorSampler_BasicLinear`, `ColorSampler_NullStart_UsesDefault`) |
| `Vector2Sampler` | `System.Numerics.Vector2` | `v1 + (v2 - v1) * t`. `null` start → `default(Vector2)`. | `NativeSamplersExtendedTests` (`Vector2Sampler_BasicLinear`) |
| `Vector3Sampler` | `System.Numerics.Vector3` | `v1 + (v2 - v1) * t`. | `NativeSamplersExtendedTests` (`Vector3Sampler_BasicLinear`) |
| `Vector4Sampler` | `System.Numerics.Vector4` | `v1 + (v2 - v1) * t`. | `NativeSamplersExtendedTests` (`Vector4Sampler_BasicLinear`) |
| `QuaternionSampler` | `System.Numerics.Quaternion` | Directional `Quaternion.Slerp`. `Auto` = shortest path; `ClockWise` / `CounterClockWise` negate `q2` when the dot product has the wrong sign (per-axis flags supported). `null` start → `Quaternion.Identity`. | `NativeSamplersExtendedTests` (`QuaternionSampler_BasicSlerp`, `QuaternionSampler_NullStart_UsesIdentity`) |

## Caveats

- The `System.Numerics` samplers (`Vector2Sampler`, `Vector3Sampler`, `Vector4Sampler`, `QuaternionSampler`) are compiled only under `#if !NETSTANDARD2_0` — they are absent on `netstandard2.0`.
- There is no per-type frame counter: endpoint handling is part of `InsertFrame`, and `FPS` in the effect is only a maximum sample-rate cap applied by the interpreter loop (see [abstractions](../01_abstractions/index.md)).
- Platform adapters register *additional* platform samplers of their own (brushes, transforms, grids, padding, ...) — see [adapter-provided](../03_adapter-provided/index.md).
