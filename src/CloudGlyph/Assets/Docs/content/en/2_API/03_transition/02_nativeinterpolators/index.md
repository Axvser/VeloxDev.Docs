# Transition — Namespace: `VeloxDev.TransitionSystem.NativeInterpolators`

All implement `IValueInterpolator.Interpolate(start, end, steps, options)`; each returns a `steps`-element frame list with `result[0] == start` and `result[steps-1] == end` (single-step returns `end`; zero steps returns empty for the numeric trio).

| Interpolator | Notes | Verified by |
|---|---|---|
| `DoubleInterpolator` | Honours `RotationDirection` shortest-path angle (mod-360 delta). `null` start → `0d`. | `NativeInterpolatorsTests`, `NativeInterpolatorsExtendedTests` |
| `FloatInterpolator` | Linear float lerp. | `NativeInterpolatorsTests` |
| `IntInterpolator` | Integer lerp. | — |
| `LongInterpolator` | Uses decimal math to avoid overflow for large ranges. | `NativeInterpolatorsTests` (`LongInterpolator_BasicLinear`, `LongInterpolator_SameStartEnd_AllSame`) |
| `PointInterpolator` | `System.Drawing.Point` lerp (rounded). | `NativeInterpolatorsExtendedTests` |
| `PointFInterpolator` | `System.Drawing.PointF` lerp. | `NativeInterpolatorsExtendedTests` |
| `SizeInterpolator` | `System.Drawing.Size` lerp. | `NativeInterpolatorsExtendedTests` |
| `SizeFInterpolator` | `System.Drawing.SizeF` lerp. | `NativeInterpolatorsExtendedTests` |
| `RectangleInterpolator` | `System.Drawing.Rectangle` lerp (X/Y/W/H). | `NativeInterpolatorsExtendedTests` |
| `RectangleFInterpolator` | `System.Drawing.RectangleF` lerp. | `NativeInterpolatorsExtendedTests` |
| `ColorInterpolator` | ARGB channel lerp. | `NativeInterpolatorsExtendedTests` |
| `Vector2Interpolator` | `System.Numerics.Vector2` lerp. `null` start → `result[0] = null`. | `NativeInterpolatorsExtendedTests` |
| `Vector3Interpolator` | `System.Numerics.Vector3` lerp. | `NativeInterpolatorsExtendedTests` |
| `Vector4Interpolator` | `System.Numerics.Vector4` lerp. | `NativeInterpolatorsExtendedTests` |
| `QuaternionInterpolator` | Directional `Quaternion.Slerp`; `Auto` = shortest path; `ClockWise`/`CounterClockWise` negate `q2` when needed. | `NativeInterpolatorsExtendedTests` |

**Caveats:**
- The `System.Numerics` interpolators (`Vector2/3/4`, `Quaternion`) are compiled only under `#if !NETSTANDARD2_0` — they are **absent on netstandard2.0**.
- Only `DoubleInterpolator`/`FloatInterpolator`/`LongInterpolator` handle `steps == 0` gracefully (return empty); the rest assume `steps >= 1` (documented by `NativeInterpolatorsExtendedTests`).
