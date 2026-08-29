# Transition — 命名空间：`VeloxDev.TransitionSystem.NativeSamplers`

全部实现 `ISampleable, ISampler`：`Normalize(start, end, options) => this`，`Update(target, property, start, end, options, t)` 在归一化时间 `t ∈ [0, 1]` 直接更新目标属性。语义：`t <= 0` 写精确 `start`、`t >= 1` 写精确 `end`；`0 < t < 1` 时值类型算好即赋、引用类型**原地修改** `start` 现有实例（不 new）。采样器是无状态、共享单例实例。

| 采样器 | 说明 | 验证依据 |
|---|---|---|
| `DoubleSampler` | 遵循 `RotationDirection` 最短路径角度（mod-360 delta）。`null` 起点 → `0d`。 | `NativeSamplersTests`、`NativeSamplersExtendedTests` |
| `FloatSampler` | 线性 float 插值。 | `NativeSamplersTests` |
| `IntSampler` | 整数插值。 | — |
| `LongSampler` | 用 decimal 数学避免大范围溢出。 | `NativeSamplersTests`（`LongSampler_BasicLinear`、`LongSampler_SameStartEnd_AllSame`） |
| `PointSampler` | `System.Drawing.Point` 插值（取整）。 | `NativeSamplersExtendedTests` |
| `PointFSampler` | `System.Drawing.PointF` 插值。 | `NativeSamplersExtendedTests` |
| `SizeSampler` | `System.Drawing.Size` 插值。 | `NativeSamplersExtendedTests` |
| `SizeFSampler` | `System.Drawing.SizeF` 插值。 | `NativeSamplersExtendedTests` |
| `RectangleSampler` | `System.Drawing.Rectangle` 插值（X/Y/W/H）。 | `NativeSamplersExtendedTests` |
| `RectangleFSampler` | `System.Drawing.RectangleF` 插值。 | `NativeSamplersExtendedTests` |
| `ColorSampler` | ARGB 通道插值。 | `NativeSamplersExtendedTests` |
| `Vector2Sampler` | `System.Numerics.Vector2` 插值。`null` 起点 → `default(Vector2)`。 | `NativeSamplersExtendedTests` |
| `Vector3Sampler` | `System.Numerics.Vector3` 插值。 | `NativeSamplersExtendedTests` |
| `Vector4Sampler` | `System.Numerics.Vector4` 插值。 | `NativeSamplersExtendedTests` |
| `QuaternionSampler` | 定向 `Quaternion.Slerp`；`Auto` = 最短路径；`ClockWise`/`CounterClockWise` 在需要时取反 `q2`。`null` 起点 → `Quaternion.Identity`。 | `NativeSamplersExtendedTests` |

**注意：**
- `System.Numerics` 采样器（`Vector2/3/4`、`Quaternion`）仅在 `#if !NETSTANDARD2_0` 下编译 —— **netstandard2.0 上没有**它们。
- 采样器不返回值、没有帧计数。端点由采样器自身在 `Update` 内处理（`t <= 0` 精确 start、`t >= 1` 精确 end），其余时刻直接更新属性。
