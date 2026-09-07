# API — 动态主题 · 支撑引擎（TransitionSystem）

动态主题功能通过 TransitionSystem 引擎对主题属性做动画。`ThemeManager` 并不驱动引擎高层的 `Transition` / `SamplerSet` / `State` 管道：它按属性类型解析一个采样器、归一化起始/结束值，然后在 Stopwatch 循环中自行调用该采样器。本页记录 `ThemeManager` 实际消费的引擎表面；完整引擎由过渡动画功能记录。

> 引擎契约位于 `VeloxDev.TransitionSystem`；引擎基础类型与具体的 `TransitionProperty` 位于 `VeloxDev.TransitionSystem.Abstractions`。完整引擎参考位于过渡动画功能（`2_API/03_transition`）。

## 命名空间：`VeloxDev.TransitionSystem.Abstractions`

### 抽象类：`InterpolatorCore`

`public abstract class InterpolatorCore`

平台插值器的基类，也是静态的按类型采样器注册表的持有者。静态构造函数会预注册原生采样器：`double`、`float`、`int`、`long`、`Point`、`PointF`、`Size`、`SizeF`、`Color`、`Rectangle`、`RectangleF`，以及（在 `NETSTANDARD2_0` 之外）`Vector2`、`Vector3`、`Vector4`、`Quaternion`。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/Interpolator.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `NativeInterpolators` | `public static ConcurrentDictionary<Type, ISampler> NativeInterpolators { get; protected set; }` | 按类型注册的采样器表。 |
| `TryGetInterpolator` | `public static bool TryGetInterpolator(Type type, out ISampler? sampler)` | 查找某类型已注册的采样器。 |
| `RegisterInterpolator` | `public static bool RegisterInterpolator(Type type, ISampler sampler)` | 注册采样器（原子的「后写者胜」）。 |
| `UnregisterInterpolator` | `public static bool UnregisterInterpolator(Type type, out ISampler? sampler)` | 移除已注册的采样器。 |
| `Prepare`（实例、`virtual`） | `public virtual SamplerSet Prepare(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector)` | 把状态快照中的每个属性归一化进一个 `SamplerSet`。供过渡动画功能使用，`ThemeManager` 不使用。 |

**说明：**
- `ThemeManager.PrepareSamplers` 通过 `InterpolatorCore.TryGetInterpolator` 按 `PropertyInfo.PropertyType` 解析属性的采样器。当该类型没有注册采样器时，该属性退化为简单的「保持到结束再切换」。
- 平台适配器 `Interpolator` 继承 `InterpolatorCore`，并在其静态构造函数中注册平台采样器（见 [04 PlatformAdapters](../04_PlatformAdapters/index.md)）。

### 类：`TransitionProperty`

`public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

`ITransitionProperty` 的编译版 getter/setter 实现。属性路径由一个或多个 `PropertyInfo` 段组成；读写经由惰性编译的委托。当中间对象非空但其运行时类型与路径不匹配时，读返回哨兵 `UnreadablePath`，写返回 `false`，调用方据此跳过该属性而不是把它当作 null/identity 处理。

源码：`Src/Core/VeloxDev.Core/TransitionSystem/TransitionProperty.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `UnreadablePath` | `public static readonly object UnreadablePath` | 路径对当前目标无效时 `GetValue` 返回的哨兵。 |
| `FromProperty` | `public static TransitionProperty FromProperty(PropertyInfo propertyInfo)` | 为单个属性创建单段路径。 |
| `Members<TSource>` | `public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | 从表达式构建可读可写的成员路径（供 `ISampleable` 使用）。 |
| `ReadableMembers<TSource>` | `public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | 构建可读成员路径（供结构体 `ISampleable` 组装）。 |
| `Combine` | `public static TransitionProperty Combine(ITransitionProperty prefix, ITransitionProperty suffix)` | 把两个路径拼接为一个。 |
| `TryCreate` | `public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property)` | 把表达式树解析为路径。 |
| `Path` | `string Path` | 以点号连接的段名。 |
| `PropertyType` / `PropertyInfo` / `Segments` | `Type` / `PropertyInfo` / `IReadOnlyList<PropertyInfo>` | 类型、末段属性信息、完整段列表。 |
| `CanRead` / `CanWrite` | `bool` | 各段可读性 / 末段可写性。 |
| `GetValue` / `SetValue` | `object? GetValue(object target)` / `bool SetValue(object target, object? value)` | 编译版路径读写。 |

**说明：**
- `ThemeManager.PrepareSamplers` 用 `TransitionProperty.FromProperty(propertyInfo)` 包装每个动画属性，随后通过 `SetValue` 写入端点/工作值。

## 命名空间：`VeloxDev.TransitionSystem`

### 接口：`ITransitionProperty`

`public interface ITransitionProperty`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ITransitionProperty.cs`。

| 成员 | 签名 |
|---|---|
| `Path` | `string Path { get; }` |
| `PropertyType` | `Type PropertyType { get; }` |
| `PropertyInfo` | `PropertyInfo PropertyInfo { get; }` |
| `Segments` | `IReadOnlyList<PropertyInfo> Segments { get; }` |
| `CanRead` / `CanWrite` | `bool CanRead { get; }` / `bool CanWrite { get; }` |
| `GetValue` | `object? GetValue(object target)` |
| `SetValue` | `bool SetValue(object target, object? value)` |

### 接口：`ISampler`

`public interface ISampler`

无状态、线程安全的采样器。采样器通常是注册在 `InterpolatorCore.NativeInterpolators` 中的共享单例。`ThemeManager` 在切换时对每个属性调用一次 `NormalizeStart` / `NormalizeEnd`，然后在每个采样帧调用一次 `InsertFrame`。

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampler.cs`。

| 成员 | 签名 | 描述 |
|---|---|---|
| `NormalizeStart` | `object? NormalizeStart(object? start, object? end, object? options)` | 在 `t <= 0` 时写入的值。可返回副本，使目标永不同名共享的起始实例。 |
| `NormalizeEnd` | `object? NormalizeEnd(object? start, object? end, object? options)` | 在 `t >= 1` 时写入的值。同样可返回副本。 |
| `InsertFrame` | `void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t)` | 计算 `t ∈ [0, 1]` 处的插值帧并写入 `target` 上的 `property`。`working` 是每次动画可复用的临时对象（在首个中间帧经 `ref` 惰性创建）。 |

**说明：**
- 端点在 `InsertFrame` 内部处理；实现不得修改传入的 `start` / `end` 实参。
- 主题切换中，采样器按属性类型经 `InterpolatorCore.TryGetInterpolator` 从注册表解析。

### 接口：`ISampleable`

`public interface ISampleable { IReadOnlyList<ITransitionProperty> GetAnimatableMembers(); object? CreateFrameValue(IReadOnlyList<object?> memberValues); }`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ISampleable.cs`。

**说明：**
- 声明某个类型的哪些成员可动画（一层）以及如何从插值后的成员重建一个值。供过渡动画功能的捕获/`Prepare` 阶段用于没有注册采样器的属性类型。
- `ThemeManager` 只从注册表解析采样器，因此 `ISampleable` 的成员展开不参与主题切换。

### 接口：`ITransitionEffectCore`

`public interface ITransitionEffectCore`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/ITransitionEffect.cs`。

| 成员 | 类型 / 签名 |
|---|---|
| `FPS` | `int FPS { get; set; }` |
| `Duration` | `TimeSpan Duration { get; set; }` |
| `IsAutoReverse` | `bool IsAutoReverse { get; set; }` |
| `LoopTime` | `int LoopTime { get; set; }` |
| `Ease` | `IEaseCalculator Ease { get; set; }` |
| 事件 | `event EventHandler<TransitionEventArgs> Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally` |
| 触发方法 | `void InvokeAwake(object, TransitionEventArgs)`、`InvokeStart`、`InvokeUpdate`、`InvokeLateUpdate`、`InvokeCompleted`、`InvokeCancled`、`InvokeFinally` |
| `Clone` | `ITransitionEffectCore Clone()` |

**说明：**
- `ThemeManager` 只读取两个成员：`Ease`（计算缓动后时间）与 `Duration`（推导总耗时毫秒数）。`FPS`、`IsAutoReverse`、`LoopTime`、生命周期事件与 `Clone` 属于更高层的引擎管道。
- 基实现 `TransitionEffectCore` 的默认值：`FPS = 60`、`Duration = 0 ms`、`Ease = Eases.Default`。主题示例所用到的适配器预设见 [04 PlatformAdapters](../04_PlatformAdapters/index.md)。

### 接口：`IEaseCalculator` 与静态类：`Eases`

`public interface IEaseCalculator { double Ease(double t); }`

源码：`Src/Core/VeloxDev.Core/Interfaces/TransitionSystem/IEaseCalculator.cs` 与 `Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`。

| 成员 | 描述 |
|---|---|
| `Eases.Default` | `IEaseCalculator` — 线性（`Ease(t) = t`，由 `EaseDefault` 支撑）。`ThemeManager.Jump` 的零时长程使用它。 |
| `Sine` / `Quad` / `Cubic` / `Quart` / `Quint` / `Expo` / `Circ` / `Back` / `Elastic` / `Bounce` | 嵌套静态类，每个都暴露 `In`、`Out`、`InOut` 成员，返回 `IEaseCalculator`。 |

**说明：**
- 完整缓动目录记录在过渡动画功能的 Eases 章节（`2_API/03_transition`）。
