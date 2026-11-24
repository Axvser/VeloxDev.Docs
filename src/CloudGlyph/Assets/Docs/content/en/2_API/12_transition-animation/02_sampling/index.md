# Sampling

A sampler turns progress `t` into a value written to the target. `InterpolatorCore` holds the process-wide sampler registry and is the base each adapter's `Interpolator` derives from. Namespace `VeloxDev.TransitionSystem`; registry base and `SamplerSet` in `VeloxDev.TransitionSystem.Abstractions`.

## VeloxDev.TransitionSystem

### Interface: ISampler

**Signature:** `public interface ISampler`

| Member | Signature | Description |
|---|---|---|
| `NormalizeStart` | `object? NormalizeStart(object? start, object? end, object? options)` | The value written at `t <= 0`. |
| `NormalizeEnd` | `object? NormalizeEnd(object? start, object? end, object? options)` | The value written at `t >= 1`. |
| `InsertFrame` | `void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t)` | Writes the interpolated value at `t` in `[0,1]`. `working` is a per-animation scratch slot the sampler may create on its first middle frame and reuse. |

Implementations must not mutate `start` or `end`; they are shared with the snapshot. `NormalizeStart` / `NormalizeEnd` may return a copy (for example a cloned mutable reference type) so the target does not alias the shared instance.

### Interface: ISampleable

Declares how a composite value type is interpolated member by member and reassembled.

**Signature:** `public interface ISampleable`

| Member | Signature | Description |
|---|---|---|
| `GetAnimatableMembers` | `IReadOnlyList<ITransitionProperty> GetAnimatableMembers()` | The members, one level deep, in the order `CreateFrameValue` expects. Use `TransitionProperty.Members<T>(...)`. |
| `CreateFrameValue` | `object? CreateFrameValue(IReadOnlyList<object?> memberValues)` | Reconstructs the value from interpolated members. |

This path applies to **value types** only. A reference type is animated through explicit member paths or a dedicated `ISampler`.

### Struct: BoundedProgress

The shared progress of a group of channels that must stay inside a range, capped at the eased time. Used by samplers that interpolate several channels together (a colour, a vector) so one channel cannot leave the range while another keeps climbing.

**Signature:** `public struct BoundedProgress`

| Member | Signature | Description |
|---|---|---|
| Constructor | `BoundedProgress(double t, double minimum = 0d, double maximum = 1d)` | Starts the group at `t`, bounded. |
| `Add` | `void Add(double start, double end)` | Adds a channel; only ever tightens the progress, so order does not matter. |
| `Progress` | `double Progress { get; }` | The progress the whole group moves by. |
| `At` | `double At(double start, double end)` | Interpolates this channel at `Progress`. |

For an eased time in `[0,1]` the result is always that same time; only an overshoot past 1 is capped.

### Enum: RotationDirection

The direction strategy for rotation interpolation.

**Signature:** `[Flags] public enum RotationDirection`

| Member | Value | Meaning |
|---|---|---|
| `Auto` | 0 | Shortest path, no forced direction (default). |
| `ClockWise` | 1 | Clockwise, 2-D or axis-agnostic 3-D. |
| `CounterClockWise` | 2 | Counter-clockwise, 2-D or axis-agnostic 3-D. |
| `ClockWiseX` / `CounterClockWiseX` | 4 / 8 | Around the X axis. |
| `ClockWiseY` / `CounterClockWiseY` | 16 / 32 | Around the Y axis. |
| `ClockWiseZ` / `CounterClockWiseZ` | 64 / 128 | Around the Z axis. |

Pass it as the `interpolationOptions` argument of `Property(..., interpolationOptions)`. Values combine bitwise.

### Interface: ITransitionProperty

**Signature:** `public interface ITransitionProperty`

| Member | Type | Description |
|---|---|---|
| `Path` | `string { get; }` | The path text, for diagnostics only; not the identity. |
| `PropertyType` | `Type { get; }` | The value type at the end of the path. |
| `CanRead` | `bool { get; }` | Every segment readable. |
| `CanWrite` | `bool { get; }` | The last segment writable. |
| `GetValue` | `object? GetValue(object? target)` | Reads; `null` when an intermediate object is null. |
| `SetValue` | `bool SetValue(object target, object? value)` | Writes; false when the path does not apply. |

`TransitionProperty` is the concrete implementation; see [Transition core](../00_transition-core/index.md).

### Interface: IFrameState

**Signature:** `public interface IFrameState`

| Member | Type | Description |
|---|---|---|
| `Values` | `ConcurrentDictionary<ITransitionProperty, object?>` | End value per property. |
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, ISampler>` | Per-property sampler override. |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` | Per-property options. |

Methods: expression, `ITransitionProperty` and `PropertyInfo` overloads of `SetInterpolator`, `SetValue`, `TryGetInterpolator`, `TryGetValue`; `SetOptions`; and `IFrameState Clone()`.

## VeloxDev.TransitionSystem.Abstractions

### Class: InterpolatorCore

The process-wide sampler registry and the adapter interpolator base.

**Signature:** `public abstract class InterpolatorCore`

The static constructor registers samplers for `double`, `float`, `int`, `long`, `Point`, `PointF`, `Size`, `SizeF`, `Color`, `Rectangle`, `RectangleF`, and on platforms other than `netstandard2.0` also `Vector2`, `Vector3`, `Vector4` and `Quaternion`.

| Member | Signature | Description |
|---|---|---|
| `TryGetInterpolator` | `static bool TryGetInterpolator(Type type, out ISampler? sampler)` | Exact type first, then base classes nearest-first, then interfaces ordered by name. |
| `RegisterInterpolator` | `static bool RegisterInterpolator(Type type, ISampler sampler)` | Installs or replaces the sampler for a type; always returns `true`. |
| `UnregisterInterpolator` | `static bool UnregisterInterpolator(Type type, out ISampler? sampler)` | Removes the registration. |
| `CreateScheduler` | `virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` | The adapter's scheduler for a target, or `null` when it cannot carry the effect. The base returns `null`. |
| `Prepare<TPriorityCore>` | `virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(object target, IFrameState state, ITransitionEffectCore effect, ITransitionHost<TPriorityCore> host)` | Reads current and target values, resolves each sampler (override then registry), and stores normalized endpoints. Unreachable paths and missing samplers are reported through `Warn` and skipped. |

### Class: SamplerSet<TPriorityCore>

The per-run container produced by `Prepare`.

**Signature:** `public sealed class SamplerSet<TPriorityCore>`

| Member | Signature | Description |
|---|---|---|
| Constructor | `SamplerSet(ITransitionHost<TPriorityCore> host)` | Creates an empty set for a host. |
| `CanSetValue` | `bool CanSetValue()` | Whether the host is still alive. |
| `Apply` | `void Apply(object target, double t, TPriorityCore priority = default!)` | Writes every entry at progress `t`. |

**Nested class `Entry`** — `public sealed class Entry`, constructed as `Entry(ITransitionProperty property, ISampler sampler, object? start, object? end, object? options)`. Public members: `Property`, `Sampler`, `Start`, `End`, `Options` (all get-only) and a public `Working` scratch field.

## Built-in samplers

Namespace `VeloxDev.TransitionSystem.NativeSamplers`. Each is a public `sealed`/`class` implementing `ISampler` and registered by `InterpolatorCore`'s static constructor.

| Sampler | Type |
|---|---|
| `DoubleSampler` | `double` |
| `FloatSampler` | `float` |
| `IntSampler` | `int` |
| `LongSampler` | `long` |
| `PointSampler` | `System.Drawing.Point` |
| `PointFSampler` | `System.Drawing.PointF` |
| `SizeSampler` | `System.Drawing.Size` |
| `SizeFSampler` | `System.Drawing.SizeF` |
| `ColorSampler` | `System.Drawing.Color` |
| `RectangleSampler` | `System.Drawing.Rectangle` |
| `RectangleFSampler` | `System.Drawing.RectangleF` |
| `Vector2Sampler` | `System.Numerics.Vector2` |
| `Vector3Sampler` | `System.Numerics.Vector3` |
| `Vector4Sampler` | `System.Numerics.Vector4` |
| `QuaternionSampler` | `System.Numerics.Quaternion` |

The `System.Numerics` samplers are excluded on `netstandard2.0`.

## Example

```csharp
using System;
using System.Windows.Media;
using VeloxDev.TransitionSystem;

// A custom sampler for a reference type the registry does not cover.
public sealed class HsbSampler : ISampler
{
    public object? NormalizeStart(object? start, object? end, object? options) => start;
    public object? NormalizeEnd(object? start, object? end, object? options) => end;

    public void InsertFrame(object target, ITransitionProperty property, ref object? working,
        object? start, object? end, object? options, double t)
    {
        var from = (Color)start!;
        var to = (Color)end!;
        property.SetValue(target, Color.FromRgb(
            (byte)(from.R + (to.R - from.R) * t),
            (byte)(from.G + (to.G - from.G) * t),
            (byte)(from.B + (to.B - from.B) * t)));
    }
}
```

Register it with `InterpolatorCore.RegisterInterpolator(typeof(Color), new HsbSampler())`, or attach it to one property through `Transition<T>.Property(..., options)` combined with the `Interpolator` chain method.
