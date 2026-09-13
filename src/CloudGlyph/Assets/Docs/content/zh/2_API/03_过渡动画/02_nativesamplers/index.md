# Transition — 命名空间：`VeloxDev.TransitionSystem.NativeSamplers`

由 `VeloxDev.Core` 提供的内置采样器（源码：`Src/Core/VeloxDev.Core/TransitionSystem/NativeSamplers/*.cs`）。它们在 `InterpolatorCore` 的静态构造函数中注册，并实现 [00_transitionsystem/00_sampling-capture](../00_transitionsystem/00_采样与捕获/index.md) 的 `ISampler` 契约。

所有采样器共享同一形态：

```csharp
public class DoubleSampler : ISampler
{
    public object? NormalizeStart(object? start, object? end, object? options) => start;
    public object? NormalizeEnd(object? start, object? end, object? options) => end;

    public void InsertFrame(object target, ITransitionProperty property, ref object? working,
        object? start, object? end, object? options, double t)
    {
        if (t <= 0) { property.SetValue(target, start); return; }   // 精确 start
        if (t >= 1) { property.SetValue(target, end); return; }     // 精确 end
        // 中间帧：在 start 与 end 之间计算并写入
    }
}
```

## 共享语义

- **无状态且共享**：这些类是无状态单例——绝不修改 `start` / `end`，并忽略 `working` 临时参数（它们就地构造插值结果，如 `new Point(...)` / `Color.FromArgb(...)` / `Quaternion.Slerp(...)`）。
- **端点在 `InsertFrame` 内处理**：`t <= 0` 写精确（归一化后的）start，`t >= 1` 写精确 end；只有 `0 < t < 1` 才计算中间帧。
- **null 起点 / 终点**：各采样器在该端点 null 时代入类型的零 / identity（如 `0d`、`default(Color)`、`default(Vector2)`、`Quaternion.Identity`）。
- **Options**：只有角度采样器读取 `options`（一个 `RotationDirection`）。

## 采样器目录

| 采样器 | 值类型 | 行为说明 | 验证依据 |
|---|---|---|---|
| `DoubleSampler` | `double` | 线性插值。当 `options` 为非 `Auto` 的 `RotationDirection` 时，使用最短路径角度差（mod-360 delta，按 `ClockWise` / `CounterClockWise` 校正）。`null` start → `0d`。 | `NativeSamplersTests`（`DoubleSampler_BasicLinear`、`DoubleSampler_Endpoints_AreExact`、`DoubleSampler_NullStart_TreatsAsZero`、`DoubleSampler_Quarters_AreCorrect`、`NormalizeEndpoints_ReturnStartAndEnd_ForStatelessSampler`） |
| `FloatSampler` | `float` | 线性 float 插值。 | `NativeSamplersTests`（`FloatSampler_BasicLinear`） |
| `IntSampler` | `int` | 整数插值，`Math.Round`。 | `InterpolatorCoreTests`（`NativeInterpolators_ContainsDefaults`，仅注册表） |
| `LongSampler` | `long` | 用 decimal 中间运算避免大范围溢出。 | `NativeSamplersTests`（`LongSampler_BasicLinear`、`LongSampler_SameStartEnd_AllSame`） |
| `PointSampler` | `System.Drawing.Point` | X/Y 插值，`(int)Math.Round`。 | `NativeSamplersExtendedTests`（`PointSampler_BasicLinear`） |
| `PointFSampler` | `System.Drawing.PointF` | X/Y float 插值。 | `NativeSamplersExtendedTests`（`PointFSampler_BasicLinear`） |
| `SizeSampler` | `System.Drawing.Size` | 宽/高插值，`(int)Math.Round`。 | `NativeSamplersExtendedTests`（`SizeSampler_BasicLinear`） |
| `SizeFSampler` | `System.Drawing.SizeF` | 宽/高 float 插值。 | `NativeSamplersExtendedTests`（`SizeFSampler_BasicLinear`） |
| `RectangleSampler` | `System.Drawing.Rectangle` | X/Y/宽/高插值，`(int)Math.Round`。 | `NativeSamplersExtendedTests`（`RectangleSampler_BasicLinear`） |
| `RectangleFSampler` | `System.Drawing.RectangleF` | X/Y/宽/高 float 插值。 | `NativeSamplersExtendedTests`（`RectangleFSampler_BasicLinear`） |
| `ColorSampler` | `System.Drawing.Color` | 经 `Color.FromArgb` 逐通道 ARGB 插值。通道值以 `(byte)` 强转（截断而非四舍五入——见测试）。 | `NativeSamplersExtendedTests`（`ColorSampler_BasicLinear`、`ColorSampler_NullStart_UsesDefault`） |
| `Vector2Sampler` | `System.Numerics.Vector2` | `v1 + (v2 - v1) * t`。`null` start → `default(Vector2)`。 | `NativeSamplersExtendedTests`（`Vector2Sampler_BasicLinear`） |
| `Vector3Sampler` | `System.Numerics.Vector3` | `v1 + (v2 - v1) * t`。 | `NativeSamplersExtendedTests`（`Vector3Sampler_BasicLinear`） |
| `Vector4Sampler` | `System.Numerics.Vector4` | `v1 + (v2 - v1) * t`。 | `NativeSamplersExtendedTests`（`Vector4Sampler_BasicLinear`） |
| `QuaternionSampler` | `System.Numerics.Quaternion` | 定向 `Quaternion.Slerp`。`Auto` = 最短路径；`ClockWise` / `CounterClockWise` 在点积符号不符时取反 `q2`（支持逐轴标记）。`null` start → `Quaternion.Identity`。 | `NativeSamplersExtendedTests`（`QuaternionSampler_BasicSlerp`、`QuaternionSampler_NullStart_UsesIdentity`） |

## 注意

- `System.Numerics` 采样器（`Vector2Sampler`、`Vector3Sampler`、`Vector4Sampler`、`QuaternionSampler`）仅在 `#if !NETSTANDARD2_0` 下编译——**`netstandard2.0` 上没有**它们。
- 没有逐类型帧计数：端点处理是 `InsertFrame` 的一部分，效果里的 `FPS` 只是解释器循环施加的最大采样率上限（见 [01_abstractions](../01_abstractions/index.md)）。
- 平台适配器会额外注册各自的平台采样器（画刷、变换、网格、padding……）——见 [03_adapter-provided](../03_适配器提供/index.md)。
