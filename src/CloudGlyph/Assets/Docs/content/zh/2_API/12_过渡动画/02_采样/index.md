# 采样

采样器把进度 `t` 变成写入目标的值。`InterpolatorCore` 持有进程级采样器注册表，也是各适配器 `Interpolator` 的基类。命名空间 `VeloxDev.TransitionSystem`；注册表基类与 `SamplerSet` 在 `VeloxDev.TransitionSystem.Abstractions`。

## VeloxDev.TransitionSystem

### 接口：ISampler

**签名：** `public interface ISampler`

| 成员 | 签名 | 说明 |
|---|---|---|
| `NormalizeStart` | `object? NormalizeStart(object? start, object? end, object? options)` | `t <= 0` 时写入的值。 |
| `NormalizeEnd` | `object? NormalizeEnd(object? start, object? end, object? options)` | `t >= 1` 时写入的值。 |
| `InsertFrame` | `void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t)` | 在 `t`（`[0,1]`）写入插值。`working` 是每次动画的暂存槽，采样器可在首次中间帧惰性创建并在后续帧复用。 |

实现不得修改 `start` 或 `end`；它们与快照共享。`NormalizeStart` / `NormalizeEnd` 可返回副本（例如可变引用类型的克隆），避免目标别名共享实例。

### 接口：ISampleable

声明复合值类型如何逐成员插值并重组。

**签名：** `public interface ISampleable`

| 成员 | 签名 | 说明 |
|---|---|---|
| `GetAnimatableMembers` | `IReadOnlyList<ITransitionProperty> GetAnimatableMembers()` | 一层深的成员，按 `CreateFrameValue` 期望的顺序。用 `TransitionProperty.Members<T>(...)` 声明。 |
| `CreateFrameValue` | `object? CreateFrameValue(IReadOnlyList<object?> memberValues)` | 从插值成员重建值。 |

该路径只适用于**值类型**。引用类型通过显式成员路径或专用 `ISampler` 动画。

### 结构：BoundedProgress

一组必须保持在范围内的通道共享的进度，以缓动时间为上限。用于同时插值多个通道（颜色、向量）的采样器，使一个通道不会在另一个仍在攀升时越界。

**签名：** `public struct BoundedProgress`

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `BoundedProgress(double t, double minimum = 0d, double maximum = 1d)` | 在 `t` 处开始一组，带边界。 |
| `Add` | `void Add(double start, double end)` | 加入一个通道；只会收紧进度，因此加入顺序无关。 |
| `Progress` | `double Progress { get; }` | 整组移动的进度。 |
| `At` | `double At(double start, double end)` | 在 `Progress` 处插值该通道。 |

缓动时间在 `[0,1]` 内时结果始终是同一时间；只有超过 1 的过冲被截断。

### 枚举：RotationDirection

旋转插值的方向策略。

**签名：** `[Flags] public enum RotationDirection`

| 成员 | 值 | 含义 |
|---|---|---|
| `Auto` | 0 | 最短路径，不强制方向（默认）。 |
| `ClockWise` | 1 | 顺时针，二维或轴无关三维。 |
| `CounterClockWise` | 2 | 逆时针，二维或轴无关三维。 |
| `ClockWiseX` / `CounterClockWiseX` | 4 / 8 | 绕 X 轴。 |
| `ClockWiseY` / `CounterClockWiseY` | 16 / 32 | 绕 Y 轴。 |
| `ClockWiseZ` / `CounterClockWiseZ` | 64 / 128 | 绕 Z 轴。 |

作为 `Property(..., interpolationOptions)` 的 `interpolationOptions` 参数传入。各值可按位组合。

### 接口：ITransitionProperty

**签名：** `public interface ITransitionProperty`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Path` | `string { get; }` | 路径文本，仅用于诊断；不是身份。 |
| `PropertyType` | `Type { get; }` | 路径末端值类型。 |
| `CanRead` | `bool { get; }` | 全部段可读。 |
| `CanWrite` | `bool { get; }` | 末段可写。 |
| `GetValue` | `object? GetValue(object? target)` | 读取；中间对象为 null 时返回 `null`。 |
| `SetValue` | `bool SetValue(object target, object? value)` | 写入；路径不适用时返回 false。 |

具体实现是 `TransitionProperty`；见[过渡核心](../00_过渡核心/index.md)。

### 接口：IFrameState

**签名：** `public interface IFrameState`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Values` | `ConcurrentDictionary<ITransitionProperty, object?>` | 逐属性终值。 |
| `Interpolators` | `ConcurrentDictionary<ITransitionProperty, ISampler>` | 逐属性采样器覆盖。 |
| `Options` | `ConcurrentDictionary<ITransitionProperty, object?>` | 逐属性选项。 |

方法：`SetInterpolator`、`SetValue`、`TryGetInterpolator`、`TryGetValue` 的表达式、`ITransitionProperty` 与 `PropertyInfo` 重载；`SetOptions`；以及 `IFrameState Clone()`。

## VeloxDev.TransitionSystem.Abstractions

### 类：InterpolatorCore

进程级采样器注册表与适配器插值器基类。

**签名：** `public abstract class InterpolatorCore`

静态构造函数为 `double`、`float`、`int`、`long`、`Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF` 注册采样器；在非 `netstandard2.0` 平台还注册 `Vector2`、`Vector3`、`Vector4` 与 `Quaternion`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `TryGetInterpolator` | `static bool TryGetInterpolator(Type type, out ISampler? sampler)` | 先精确类型，再按最近优先走基类，最后按名称序接口。 |
| `RegisterInterpolator` | `static bool RegisterInterpolator(Type type, ISampler sampler)` | 安装或替换类型采样器；始终返回 `true`。 |
| `UnregisterInterpolator` | `static bool UnregisterInterpolator(Type type, out ISampler? sampler)` | 移除注册。 |
| `CreateScheduler` | `virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect)` | 适配器为目标的调度器；无法承载该效果时为 `null`。基类返回 `null`。 |
| `Prepare<TPriorityCore>` | `virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(object target, IFrameState state, ITransitionEffectCore effect, ITransitionHost<TPriorityCore> host)` | 读取当前值与目标值，解析采样器（覆盖后注册表），存入归一化端点。不可达路径与缺失采样器经 `Warn` 报告并跳过。 |

### 类：SamplerSet<TPriorityCore>

`Prepare` 产出的单次运行容器。

**签名：** `public sealed class SamplerSet<TPriorityCore>`

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `SamplerSet(ITransitionHost<TPriorityCore> host)` | 为宿主创建空集合。 |
| `CanSetValue` | `bool CanSetValue()` | 宿主是否仍存活。 |
| `Apply` | `void Apply(object target, double t, TPriorityCore priority = default!)` | 以进度 `t` 写入每个条目。 |

**嵌套类 `Entry`**——`public sealed class Entry`，构造为 `Entry(ITransitionProperty property, ISampler sampler, object? start, object? end, object? options)`。公开成员：`Property`、`Sampler`、`Start`、`End`、`Options`（只读）与公开 `Working` 暂存字段。

## 内置采样器

命名空间 `VeloxDev.TransitionSystem.NativeSamplers`。每个都是实现 `ISampler` 的公开类，由 `InterpolatorCore` 静态构造函数注册。

| 采样器 | 类型 |
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

`System.Numerics` 采样器在 `netstandard2.0` 上不包含。

## 示例

```csharp
using System;
using System.Windows.Media;
using VeloxDev.TransitionSystem;

// 注册表未覆盖的引用类型可写自定义采样器。
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

用 `InterpolatorCore.RegisterInterpolator(typeof(Color), new HsbSampler())` 注册，或通过 `Transition<T>.Property(..., options)` 与 `Interpolator` 链方法把它挂到单个属性上。
