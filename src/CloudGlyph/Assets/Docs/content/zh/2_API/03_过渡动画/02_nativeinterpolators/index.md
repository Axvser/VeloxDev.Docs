# Transition — 命名空间：`VeloxDev.TransitionSystem.NativeInterpolators`

全部实现 `IValueInterpolator.Interpolate(start, end, steps, options)`；各自返回 `steps` 元素帧列表，且 `result[0] == start`、`result[steps-1] == end`（单步返回 `end`；数值三剑客在 0 步时返回空）。

| 插值器 | 说明 | 验证依据 |
|---|---|---|
| `DoubleInterpolator` | 遵循 `RotationDirection` 最短路径角度（mod-360 delta）。`null` 起点 → `0d`。 | `NativeInterpolatorsTests`、`NativeInterpolatorsExtendedTests` |
| `FloatInterpolator` | 线性 float 插值。 | `NativeInterpolatorsTests` |
| `IntInterpolator` | 整数插值。 | — |
| `LongInterpolator` | 用 decimal 数学避免大范围溢出。 | `NativeInterpolatorsTests`（`LongInterpolator_BasicLinear`、`LongInterpolator_SameStartEnd_AllSame`） |
| `PointInterpolator` | `System.Drawing.Point` 插值（取整）。 | `NativeInterpolatorsExtendedTests` |
| `PointFInterpolator` | `System.Drawing.PointF` 插值。 | `NativeInterpolatorsExtendedTests` |
| `SizeInterpolator` | `System.Drawing.Size` 插值。 | `NativeInterpolatorsExtendedTests` |
| `SizeFInterpolator` | `System.Drawing.SizeF` 插值。 | `NativeInterpolatorsExtendedTests` |
| `RectangleInterpolator` | `System.Drawing.Rectangle` 插值（X/Y/W/H）。 | `NativeInterpolatorsExtendedTests` |
| `RectangleFInterpolator` | `System.Drawing.RectangleF` 插值。 | `NativeInterpolatorsExtendedTests` |
| `ColorInterpolator` | ARGB 通道插值。 | `NativeInterpolatorsExtendedTests` |
| `Vector2Interpolator` | `System.Numerics.Vector2` 插值。`null` 起点 → `result[0] = null`。 | `NativeInterpolatorsExtendedTests` |
| `Vector3Interpolator` | `System.Numerics.Vector3` 插值。 | `NativeInterpolatorsExtendedTests` |
| `Vector4Interpolator` | `System.Numerics.Vector4` 插值。 | `NativeInterpolatorsExtendedTests` |
| `QuaternionInterpolator` | 定向 `Quaternion.Slerp`；`Auto` = 最短路径；`ClockWise`/`CounterClockWise` 在需要时取反 `q2`。 | `NativeInterpolatorsExtendedTests` |

**注意：**
- `System.Numerics` 插值器（`Vector2/3/4`、`Quaternion`）仅在 `#if !NETSTANDARD2_0` 下编译 —— **netstandard2.0 上没有**它们。
- 只有 `DoubleInterpolator`/`FloatInterpolator`/`LongInterpolator` 优雅处理 `steps == 0`（返回空）；其余假定 `steps >= 1`（`NativeInterpolatorsExtendedTests` 已注明）。
