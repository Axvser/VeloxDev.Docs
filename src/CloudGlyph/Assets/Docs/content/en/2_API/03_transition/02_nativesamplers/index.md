# Transition — Namespace: `VeloxDev.TransitionSystem.NativeSamplers`

All native samplers implement `ISampleable, ISampler` (e.g. `DoubleSampler`) with `Normalize => this` and `Update`. Each `Update` directly writes the property at normalized time `t ∈ [0, 1]` (`t <= 0` → exact `start`, `t >= 1` → exact `end`). Samplers are stateless, shared-singleton instances; the endpoints are handled inside `Update`.

| Sampler | Notes | Verified by |
|---|---|---|
| `DoubleSampler` | Honours `RotationDirection` shortest-path angle (mod-360 delta). `null` start → `0d`. | `NativeSamplersTests`, `NativeSamplersExtendedTests` |
| `FloatSampler` | Linear float lerp. | `NativeSamplersTests` |
| `IntSampler` | Integer lerp. | — |
| `LongSampler` | Uses decimal math to avoid overflow for large ranges. | `NativeSamplersTests` (`LongSampler_BasicLinear`, `LongSampler_SameStartEnd_AllSame`) |
| `PointSampler` | `System.Drawing.Point` lerp (rounded). | `NativeSamplersExtendedTests` |
| `PointFSampler` | `System.Drawing.PointF` lerp. | `NativeSamplersExtendedTests` |
| `SizeSampler` | `System.Drawing.Size` lerp. | `NativeSamplersExtendedTests` |
| `SizeFSampler` | `System.Drawing.SizeF` lerp. | `NativeSamplersExtendedTests` |
| `RectangleSampler` | `System.Drawing.Rectangle` lerp (X/Y/W/H). | `NativeSamplersExtendedTests` |
| `RectangleFSampler` | `System.Drawing.RectangleF` lerp. | `NativeSamplersExtendedTests` |
| `ColorSampler` | ARGB channel lerp. | `NativeSamplersExtendedTests` |
| `Vector2Sampler` | `System.Numerics.Vector2` lerp. `null` start → `default(Vector2)`. | `NativeSamplersExtendedTests` |
| `Vector3Sampler` | `System.Numerics.Vector3` lerp. | `NativeSamplersExtendedTests` |
| `Vector4Sampler` | `System.Numerics.Vector4` lerp. | `NativeSamplersExtendedTests` |
| `QuaternionSampler` | Directional `Quaternion.Slerp`; `Auto` = shortest path; `ClockWise`/`CounterClockWise` negate `q2` when needed. `null` start → `Quaternion.Identity`. | `NativeSamplersExtendedTests` |

**Caveats:**
- The `System.Numerics` samplers (`Vector2/3/4`, `Quaternion`) are compiled only under `#if !NETSTANDARD2_0` — they are **absent on netstandard2.0**.
- Samplers directly update the property per sample; there is no frame count. The `steps == 0`/`steps == 1` edge cases moved to `ISampler.Update`, which handles the endpoints (`t <= 0` exact start, `t >= 1` exact end).
