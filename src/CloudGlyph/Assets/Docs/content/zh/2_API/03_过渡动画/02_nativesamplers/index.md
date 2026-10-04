# 过渡动画 — 命名空间：`VeloxDev.TransitionSystem.NativeSamplers`

`VeloxDev.Core` 自带的内置采样器（源：`Src/Core/VeloxDev.Core/TransitionSystem/NativeSamplers/*.cs`）。它们在 `InterpolatorCore` 的静态构造函数中注册，实现 [transitionsystem/sampling-capture](../00_transitionsystem/00_采样与捕获/index.md) 中的 `ISampler` 契约。

所有采样器形状一致：

```csharp
public class DoubleSampler : ISampler
{
    public object? NormalizeStart(object? start, object? end, object? options) => start;
    public object? NormalizeEnd(object? start, object? end, object? options) => end;

    public void InsertFrame(object target, ITransitionProperty property, ref object? working,
        object? start, object? end, object? options, double t)
    {
        // 在 t 处算出 start 与 end 之间的值，然后写入
    }
}
```

## 共同语义

- **无状态 & 共享**：这些类是无状态单例 —— 从不修改 `start` / `end`，也忽略 `working` 暂存形参（它们就地分配插值结果，如 `new Size(...)`、`Color.FromArgb(...)`、`Quaternion.Slerp(...)`）。
- **精确端点**：流水线用恰好 `1`（正向）或 `0`（反向）驱动每趟的最后一帧。对数值采样器，`t = 0` / `t = 1` 处的线性插值精确复现端点，因此无需守卫；`QuaternionSampler` 在恰好 `0` / `1` 时返回调用方**自己的** `start` / `end` 实例，因为像 `((TranslateTransform)x.RenderTransform).X` 这样的嵌套路径依赖该变换被声明时的运行时类型，插值出来的替身会把它丢掉。
- **Null 起止值**：对应端点为 null 时，各采样器以该类型的零值 / 单位值替代（如 `0d`、`default(Color)`、`default(Vector2)`、`Quaternion.Identity`）。
- **Options**：只有角度采样器读 `options`（一个 `RotationDirection`）。
- **过冲**：`t` 是不夹取地传进来的，所以过冲缓动可以把采样器推过端点。这意味着什么按值类型决定 —— 见下面的*受限通道组*。

## 受限通道组（`BoundedProgress`）

五个采样器以**同一个共享进度**插值一*组*通道，而不是逐通道，使过冲无法扭曲该值：`ColorSampler`（R/G/B 共享一个 `[0, 255]` 进度，alpha 保留自己的时间）、`SizeSampler` / `SizeFSampler`（宽/高共享一个 `[0, +∞)` 进度）、`RectangleSampler` / `RectangleFSampler`（宽/高共享一个 `[0, +∞)` 进度；原点不受限）。它们都经 `BoundedProgress` —— 与 `AUTO TEST` 一致性套件中独立推演的 `Conformance/ClosedForm.SharedProgress` / `ColorAt` 是同一个量。`ColorSampler.Channel` 在 `0` / `255` 处**饱和**而不是回绕（裸 `(byte)` 转换会把 300 变成 44），范围内截断，与框架自身的字节转换一致。

## 采样器目录

| 采样器 | 值类型 | 行为说明 | 核验 |
|---|---|---|---|
| `DoubleSampler` | `double` | 线性插值。当 `options` 是非 `Auto` 的 `RotationDirection` 时，走最短路径角差（按 `ClockWise` / `CounterClockWise` 修正的模 360 差值）。null 起点 → `0d`。 | `NativeSamplersTests`、`SamplerConformanceTests` |
| `FloatSampler` | `float` | 线性单精度插值。 | `NativeSamplersTests`（`FloatSampler_BasicLinear`） |
| `IntSampler` | `int` | 整数插值，`Math.Round`；端点相等时短路。 | `SamplerConformanceTests`、`InterpolatorCoreTests` |
| `LongSampler` | `long` | 用 `decimal` 中间运算避免大范围溢出。 | `NativeSamplersTests`（`LongSampler_BasicLinear`、`LongSampler_SameStartEnd_AllSame`） |
| `PointSampler` | `System.Drawing.Point` | X/Y 插值，`(int)Math.Round`。 | `NativeSamplersExtendedTests` |
| `PointFSampler` | `System.Drawing.PointF` | X/Y 单精度插值。 | `NativeSamplersExtendedTests` |
| `SizeSampler` | `System.Drawing.Size` | 宽/高共享一个在零处受限的进度；`(int)Math.Round`。 | `NativeSamplersExtendedTests`、`SamplerConformanceTests`、`EaseOvershootTests` |
| `SizeFSampler` | `System.Drawing.SizeF` | 宽/高共享一个在零处受限的进度。 | `NativeSamplersExtendedTests` |
| `RectangleSampler` | `System.Drawing.Rectangle` | X/Y 插值；宽/高共享一个在零处受限的进度；`(int)Math.Round`。 | `NativeSamplersExtendedTests` |
| `RectangleFSampler` | `System.Drawing.RectangleF` | X/Y 插值；宽/高共享一个在零处受限的进度。 | `NativeSamplersExtendedTests` |
| `ColorSampler` | `System.Drawing.Color` | R/G/B 共享一个 `[0, 255]` 进度并饱和；alpha 保留完整缓动时间；范围内截断。 | `NativeSamplersExtendedTests`、`EaseOvershootTests`、`AUTO TEST` `EverySamplerMatchesItsClosedForm` |
| `Vector2Sampler` | `System.Numerics.Vector2` | `v1 + (v2 - v1) * t`。null 起点 → `default(Vector2)`。 | `NativeSamplersExtendedTests` |
| `Vector3Sampler` | `System.Numerics.Vector3` | `v1 + (v2 - v1) * t`。 | `NativeSamplersExtendedTests` |
| `Vector4Sampler` | `System.Numerics.Vector4` | `v1 + (v2 - v1) * t`。 | `NativeSamplersExtendedTests` |
| `QuaternionSampler` | `System.Numerics.Quaternion` | 在恰好 `t == 0` / `t == 1` 时返回调用方自己的实例；否则定向 `Quaternion.Slerp`。`Auto` = 最短路径；点积符号不对时 `ClockWise` / `CounterClockWise` 对 `q2` 取负（支持逐轴标志）。null 起点 → `Quaternion.Identity`。 | `NativeSamplersExtendedTests`、`QuaternionOvershootTests` |

## 注意事项

- `System.Numerics` 采样器（`Vector2Sampler`、`Vector3Sampler`、`Vector4Sampler`、`QuaternionSampler`）仅在 `#if !NETSTANDARD2_0` 下编译 —— 在 `netstandard2.0` 上不存在。
- 不存在逐类型的帧计数器：端点处理是 `InsertFrame` 的一部分，而 effect 的 `FPS` 只是解释器循环施加的最大采样率上限（见 [abstractions](../01_abstractions/01_引擎/index.md)）。
- 平台适配器还注册它们自己的*额外*平台采样器（画刷、变换、网格、内边距等）—— 见 [adapter-provided](../03_适配器提供/index.md)。
