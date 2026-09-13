# Transition — 旋转方向与缓动

命名空间 `VeloxDev.TransitionSystem`。本命名空间其余成员：引导角度插值的 `RotationDirection` 标记枚举，以及 `Eases` 工厂和它的 31 个具体缓动类（全部实现 `IEaseCalculator`）。

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
- `[Flags]`——成员可按位组合表达逐轴方向；带轴值的成员用于 3D 旋转。
- 作为 `Property(lambda, value, options)` 的 `interpolationOptions` 参数传入（记录在 `IFrameState.Options`），由角度采样器读取：`DoubleSampler` 与 `QuaternionSampler` 遵循它（`QuaternionSampler` 通过取反 `q2` 来按需强制方向，支持逐轴）；其它采样器忽略它。
- *验证依据：* WPF 示例 `Animation1` 传入 `RotationDirection.CounterClockWise`（`Examples/Transition/WPF/Demo/MainWindow.xaml.cs`）。

### 接口：`IEaseCalculator`

```csharp
public interface IEaseCalculator
{
    double Ease(double t);
}
```

**说明：** `t` 为归一化时间 `[0, 1]`。标准曲线返回值落在 `[0, 1]`；`Back` 与 `Elastic` 可能过冲，采样循环会把缓动结果再钳制回 `[0, 1]`。

### 静态类：`Eases`

`Eases` 暴露 `Default`（线性）以及每种命名曲线一个嵌套工厂类；每个嵌套类暴露 `In`、`Out`、`InOut` 三个静态只读属性：

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
    // Quad, Cubic, Quart, Quint, Expo, Circ, Back, Elastic, Bounce — 结构相同
}
```

**说明：** 工厂属性每次访问都构造新的缓动实例（计算型 getter），因此廉价但并非单例。所有工厂与具体类均为 public。

### 具体缓动类

每个具体类实现 `IEaseCalculator`，仅含一个 `double Ease(double t)` 成员：

`EaseDefault`、`EaseInSine`、`EaseOutSine`、`EaseInOutSine`、`EaseInQuad`、`EaseOutQuad`、`EaseInOutQuad`、`EaseInCubic`、`EaseOutCubic`、`EaseInOutCubic`、`EaseInQuart`、`EaseOutQuart`、`EaseInOutQuart`、`EaseInQuint`、`EaseOutQuint`、`EaseInOutQuint`、`EaseInExpo`、`EaseOutExpo`、`EaseInOutExpo`、`EaseInCirc`、`EaseOutCirc`、`EaseInOutCirc`、`EaseInBack`、`EaseOutBack`、`EaseInOutBack`、`EaseInElastic`、`EaseOutElastic`、`EaseInOutElastic`、`EaseInBounce`、`EaseOutBounce`、`EaseInOutBounce`。

**说明：**
- `EaseDefault.Ease(t) => t`（线性）。标准缓动公式集（Robert Penner 风格）实现在 `Eases.cs`（`Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs`）。
- *验证依据：* `EasesTests`（`Default_AtZero_ReturnsZero`、`Default_AtOne_ReturnsOne`、`AllStandardEases_AtBoundaries_ReturnExpected`、`QuadIn_IsMonotonicallyIncreasing`、`InOutQuad_Symmetry_AtHalf`、`*_FactoryProperties_ReturnNonNull`）。

### `VeloxDev.TransitionSystem` 的其它成员

另有两个 public 类型与本命名空间共享，但按其所属的构建器 / 适配器表面另行记录：

- `TransitionCoreEx` —— 构建与运行 `StateSnapshotCore` 链的静态流程扩展（`Await`、`Then`、`AwaitThen`、`Interpolator`）→ [01_abstractions](../../01_abstractions/index.md)。
- 各适配器的 `Transition`、`Transition<T>` → [03_adapter-provided](../../03_适配器提供/index.md)。
