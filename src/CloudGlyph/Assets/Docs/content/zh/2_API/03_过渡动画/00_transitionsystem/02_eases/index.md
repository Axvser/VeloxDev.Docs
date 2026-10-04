# 过渡动画 — 旋转方向与缓动

命名空间 `VeloxDev.TransitionSystem`。除契约之外，本核心命名空间的其余成员：引导角度插值的 `RotationDirection` 标志枚举，以及 `Eases` 工厂与其 31 个具体缓动类（都实现 `IEaseCalculator`）。

### 枚举：`RotationDirection`

```csharp
[Flags]
public enum RotationDirection
{
    Auto = 0,
    ClockWise = 1 << 0,
    CounterClockWise = 1 << 1,
    ClockWiseX = 1 << 2,
    CounterClockWiseX = 1 << 3,
    ClockWiseY = 1 << 4,
    CounterClockWiseY = 1 << 5,
    ClockWiseZ = 1 << 6,
    CounterClockWiseZ = 1 << 7,
}
```

**说明：**
- `[Flags]` —— 各成员可按位组合，因此能表达逐轴方向；轴专属值适用于 3D 旋转。
- 作为 `Property(lambda, value, options)` 的 `interpolationOptions` 实参传入（记录在 `IFrameState.Options`），由角度采样器读取：`DoubleSampler` 与 `QuaternionSampler` 会遵守它（`QuaternionSampler` 按轴对 `q2` 取负以强制指定方向）；其他采样器忽略它。
- *核验：* WPF 演示 `Animation1` 传入 `RotationDirection.CounterClockWise`（`Examples/Transition/WPF/Demo/MainWindow.xaml.cs`）。

### 接口：`IEaseCalculator`

```csharp
public interface IEaseCalculator
{
    double Ease(double t);
}
```

**说明：** `t` 是 `[0, 1]` 内的归一化时间。标准曲线返回值在 `[0, 1]`；`Back` 与 `Elastic` 刻意越界 —— 解释器把缓动后的值**不夹取**地交给采样器，由采样器决定是能外推（数值型可以）还是必须钉在端点。在这里夹取会把两条曲线都压平。本特性的 SE 分析逐类推演了过冲对各采样器意味着什么。

### 静态类：`Eases`

`Eases` 暴露 `Default`（线性）以及每个具名曲线一个嵌套工厂类；每个嵌套类暴露 `In`、`Out`、`InOut` 三个静态只读属性：

| 工厂 | In | Out | InOut |
|---|---|---|---|
| `Eases.Sine` | `EaseInSine` | `EaseOutSine` | `EaseInOutSine` |
| `Eases.Quad` | `EaseInQuad` | `EaseOutQuad` | `EaseInOutQuad` |
| `Eases.Cubic` | `EaseInCubic` | `EaseOutCubic` | `EaseInOutCubic` |
| `Eases.Quart` | `EaseInQuart` | `EaseOutQuart` | `EaseInOutQuart` |
| `Eases.Quint` | `EaseInQuint` | `EaseOutQuint` | `EaseInOutQuint` |
| `Eases.Expo` | `EaseInExpo` | `EaseOutExpo` | `EaseInOutExpo` |
| `Eases.Circ` | `EaseInCirc` | `EaseOutCirc` | `EaseInOutCirc` |
| `Eases.Back` | `EaseInBack` | `EaseOutBack` | `EaseInOutBack` |
| `Eases.Elastic` | `EaseInElastic` | `EaseOutElastic` | `EaseInOutElastic` |
| `Eases.Bounce` | `EaseInBounce` | `EaseOutBounce` | `EaseInOutBounce` |

```csharp
public static class Eases
{
    public static IEaseCalculator Default { get; }        // 线性，new EaseDefault()
    public static class Sine
    {
        public static IEaseCalculator In { get; }
        public static IEaseCalculator Out { get; }
        public static IEaseCalculator InOut { get; }
    }
    // Quad、Cubic、Quart、Quint、Expo、Circ、Back、Elastic、Bounce —— 形状相同
}
```

**说明：** 工厂属性每次访问都构造一个新的缓动实例（计算属性），因此便宜但非单例。所有工厂与具体类都是公开的。唯一**不能**走属性的地方是采样循环的热路径 —— `EaseInBounce` / `EaseInOutBounce` 持有 `private static readonly EaseOutBounce` 而不调用 `Eases.Bounce.Out`，因为该属性会分配。

### 具体缓动类

每个具体类以单个 `double Ease(double t)` 成员实现 `IEaseCalculator`：

`EaseDefault`、`EaseInSine`、`EaseOutSine`、`EaseInOutSine`、`EaseInQuad`、`EaseOutQuad`、`EaseInOutQuad`、`EaseInCubic`、`EaseOutCubic`、`EaseInOutCubic`、`EaseInQuart`、`EaseOutQuart`、`EaseInOutQuart`、`EaseInQuint`、`EaseOutQuint`、`EaseInOutQuint`、`EaseInExpo`、`EaseOutExpo`、`EaseInOutExpo`、`EaseInCirc`、`EaseOutCirc`、`EaseInOutCirc`、`EaseInBack`、`EaseOutBack`、`EaseInOutBack`、`EaseInElastic`、`EaseOutElastic`、`EaseInOutElastic`、`EaseInBounce`、`EaseOutBounce`、`EaseInOutBounce`。

**说明：**
- `EaseDefault.Ease(t) => t`（线性）。标准缓动公式集（Robert Penner 风格）实现在 `Eases.cs`（`Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`）。
- *核验：* `EasesTests`（`Default_AtZero_ReturnsZero`、`Default_AtOne_ReturnsOne`、`AllStandardEases_AtBoundaries_ReturnExpected`、`QuadIn_IsTickabletonicallyIncreasing`、`InOutQuad_Symmetry_AtHalf`、`Sine_FactoryProperties_ReturnNonNull` 等每个工厂组一条）、`EaseOvershootTests`。

### `VeloxDev.TransitionSystem` 的其他成员

本命名空间另有三个公开成员，随它们所属的表面记录：

- `TransitionCoreEx` —— 链接 `StateSnapshotCore` 分段的静态扩展方法（`Await`、`Then`、`AwaitThen`、`Repeat`、`Interpolator`）→ [abstractions](../../01_abstractions/index.md)。
- `NonPriority` —— 无优先级适配器用作优先级类型实参的空结构体 → [host](../03_宿主/index.md)（它声明在 `VeloxDev.Threading`，不在这里）。
- `ITransitionHost<TPriorityCore>` —— 引擎索取的宿主组合 → [host](../03_宿主/index.md)。
- `TransitionHostBase<TPriorityCore>` —— 适配器宿主派生的基类 → [host](../03_宿主/index.md)。
- 各适配器的 `Transition`、`Transition<T>` → [adapter-provided](../../03_适配器提供/index.md)。
