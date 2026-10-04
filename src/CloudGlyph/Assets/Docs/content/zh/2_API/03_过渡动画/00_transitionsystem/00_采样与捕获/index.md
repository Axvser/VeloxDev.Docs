# 过渡动画 — 契约：采样与属性寻址

命名空间 `VeloxDev.TransitionSystem`。这四个契约描述一个值如何被采样、一个目标属性如何被寻址与声明；`BoundedProgress` 是多通道采样器用的分组助手；末尾两个异常拒绝一条对本次过渡无效、或永远无法动画的声明路径。

### 接口：`ISampler`

```csharp
public interface ISampler
{
    object? NormalizeStart(object? start, object? end, object? options);
    object? NormalizeEnd(object? start, object? end, object? options);
    void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t);
}
```

| 成员 | 说明 |
|---|---|
| `NormalizeStart` | 返回 `t <= 0` 时写入的值。默认原样返回 `start`；采样器可以返回副本（例如可变引用类型的克隆），使目标不会与共享的起点实例互为别名。 |
| `NormalizeEnd` | 返回 `t >= 1` 时写入的值。默认原样返回 `end`；出于同样的别名理由可以返回副本。 |
| `InsertFrame` | 计算 `t ∈ [0, 1]` 处的帧并写入 `target` 上的 `property`。`working` 是每次动画复用的暂存对象（首个中间帧调用时经 `ref` 惰性创建、之后复用 —— 每帧零分配）；值类型采样器忽略它。 |

**说明：**
- 实现是无状态、线程安全的共享单例，经 `Abstractions.InterpolatorCore.RegisterInterpolator` 注册（或者作为 `IFrameState.Interpolators` 中的逐属性覆盖提供）。注册表字典本身是**私有**的 —— 三个成员（`RegisterInterpolator` / `UnregisterInterpolator` / `TryGetInterpolator`）就是全部表面，因为能拿到字典的调用方可以整体替换它、丢掉所有默认项。
- 端点**在 `InsertFrame` 内**处理：`t <= 0` 写入精确的（归一化后）起点，`t >= 1` 写入精确终点。不存在 `Update` / `Sample` 方法 —— 这个三方法形状取代了更早的 `IValueInterpolator` / `IInPlaceSampler` 设计。
- 实现**不得修改** `start` / `end` 实参：它们与记录它们的过渡声明共享，修改就污染了声明。
- `options` 仍然承载角度采样器的 `RotationDirection`（见 [eases](../02_eases/index.md)）。
- *核验：* `NativeSamplersTests`（`DoubleSampler_Endpoints_AreExact`、`DoubleSampler_NullStart_TreatsAsZero`）、`NativeSamplersExtendedTests`（各采样器的 `_BasicLinear`）、`SamplerSetTests`。

### 接口：`ISampleable`

```csharp
public interface ISampleable
{
    IReadOnlyList<ITransitionProperty> GetAnimatableMembers();
    object? CreateFrameValue(IReadOnlyList<object?> memberValues);
}
```

**说明：**
- 声明一个复合**值类型**作为整体如何动画 —— **只一层，不递归**。只有值类型走这条路：结构体的成员无法就地写回，所以整个值必须每帧重建。引用类型**不**使用本接口。
- `GetAnimatableMembers` 返回可动画成员（相对本类型的路径，顺序与 `CreateFrameValue` 一致）。建议用 `TransitionProperty.Members<Foo>(f => f.Bar, ...)` 声明它们（见 [abstractions](../../01_abstractions/index.md)）。
- `CreateFrameValue` 按 `GetAnimatableMembers` 顺序从插值后的成员重建该值 —— 实现经自己的构造函数构建（编译期，零反射）。
- `InterpolatorCore.Prepare` **最后**才伸手取本接口：一个实现 `ISampleable` 且没有注册采样器的**结构体**值类型，会交给内部 `StructAssembler`，它用各成员各自注册的采样器插值、并经 `CreateFrameValue` 重装该结构体。任一成员采样器无法解析，该属性就被跳过。
- 引用类型要么经显式成员路径动画（`Property(x => x.Foo.Bar, end)`），要么由专门的 `ISampler` 内部做分解/归一/插值 —— 否则 `Transition<T>.Execute` 会拒绝该路径（见下）。
- *核验：* `StructAssemblerTests`、`NativeSamplersExtendedTests`（测试结构体）。

### 接口：`ITransitionProperty`

```csharp
public interface ITransitionProperty
{
    string Path { get; }
    Type PropertyType { get; }
    bool CanRead { get; }
    bool CanWrite { get; }
    object? GetValue(object? target);
    bool SetValue(object target, object? value);
}
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `Path` | `string` | 路径文本（如 `"RenderTransform.X"`、`"Items[0].Width"`），仅供诊断 —— 它不是身份，身份是对象的相等性。 |
| `PropertyType` | `Type` | 末端属性的类型。 |
| `CanRead` / `CanWrite` | `bool` | 整条链是否可读 / 末端是否可写。 |
| `GetValue` | `object? GetValue(object? target)` | 沿链读取。当中间对象的**类型**与路径不符（路径无效）时返回 `Abstractions.TransitionProperty.UnreadablePath`；当中间对象确实为 `null` 时返回 `null`。 |
| `SetValue` | `bool SetValue(object target, object? value)` | 沿链写入。当中间类型不符或为 `null` 时返回 `false`（不抛 `TargetException`）；引用类型末端写 `null` 是允许的，返回 `true`。 |

**说明：**
- 刻意收窄：接口不暴露 `PropertyInfo`，也不暴露 `Segments`，因为路径可能以数组元素或索引器结尾，而两者都无法用它们描述 —— 数组元素根本没有 `PropertyInfo`，且类型上每个索引器都报告同一个 `Item` 成员，因此无法把 `Items[0]` 与 `Items[1]` 区分开。
- 具体类型 `TransitionProperty`（命名空间 `VeloxDev.TransitionSystem.Abstractions`）在首次使用时把 getter / setter 编译成单个委托 —— 每帧无反射（见 [abstractions](../../01_abstractions/index.md)）。
- *核验：* `TransitionPropertyTests`（`GetValue_ReadsFromTarget`、`SetValue_WritesToTarget`、`GetValue_IntermediateTypeMismatch_ReturnsUnreadablePath_NotTargetException`、`SetValue_IntermediateTypeMismatch_ReturnsFalse_NotTargetException`、`GetValue_NullIntermediate_ReturnsNull_NotUnreadable`）。

### 接口：`IFrameState`

```csharp
public interface IFrameState
{
    ConcurrentDictionary<ITransitionProperty, object?> Values { get; }
    ConcurrentDictionary<ITransitionProperty, ISampler> Interpolators { get; }
    ConcurrentDictionary<ITransitionProperty, object?> Options { get; }

    void SetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, ISampler interpolator);
    void SetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, TValue? value);
    bool TryGetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out ISampler? interpolator);
    bool TryGetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out TValue? value);

    void SetInterpolator(ITransitionProperty property, ISampler interpolator);
    void SetValue(ITransitionProperty property, object? value);
    bool TryGetInterpolator(ITransitionProperty property, out ISampler? interpolator);
    bool TryGetValue(ITransitionProperty property, out object? value);

    void SetInterpolator(PropertyInfo propertyInfo, ISampler interpolator);
    void SetValue(PropertyInfo propertyInfo, object? value);
    bool TryGetInterpolator(PropertyInfo propertyInfo, out ISampler? interpolator);
    bool TryGetValue(PropertyInfo propertyInfo, out object? value);

    void SetOptions<TSource, TValue>(Expression<Func<TSource, TValue>> expression, object? options);
    void SetOptions(ITransitionProperty property, object? options);
    void SetOptions(PropertyInfo propertyInfo, object? options);
    bool TryGetOptions(ITransitionProperty property, out object? options);

    IFrameState Clone();
}
```

**说明：**
- 三个以 `ITransitionProperty` 为键的 `ConcurrentDictionary` 组成的容器：记录的目标 `Values`、逐属性 `ISampler` 覆盖、逐属性 `Options`（例如一个 `RotationDirection`）。
- 每个 `Set*` / `TryGet*` 都有三个重载族 —— 表达式 lambda、`ITransitionProperty`、`PropertyInfo`。表达式 / `PropertyInfo` 重载与键形式寻址同一条路径。
- 表达式重载只记录既可读**又**可写的路径（具体 `StateCore` 拒绝存入只读或不可写路径）。
- `Clone()` 返回三份字典的独立副本。
- `InterpolatorCore.Prepare` 消费一个 state：读 `state.Values`，从 `state.Interpolators` 取逐属性覆盖，从 `state.Options` 取 options 实参。
- *核验：* `StateCoreTests`（`SetValue_Expression_CanRetrieve`、`SetInterpolator_Expression_CanRetrieve`、`Clone_ReturnsIndependentCopy`）。

### 结构体：`BoundedProgress`

一组通道的共享进度，被限制在某个范围内、并以缓动时间为上界。

```csharp
public struct BoundedProgress
{
    public BoundedProgress(double t, double minimum = 0d, double maximum = 1d);
    public void Add(double start, double end);
    public readonly double Progress { get; }
    public readonly double At(double start, double end);
}
```

| 成员 | 说明 |
|---|---|
| 构造函数 | 从 `t` 起建一组通道，限定在 `[minimum, maximum]`。 |
| `Add(start, end)` | 往组里加一个通道。只会**收紧**进度，因此加通道的顺序无关。范围两端都会约束它，不只是远的那一端 —— 通道在过冲时由最大值离开、在预期（anticipation）时由最小值离开。delta 为 0 的通道被忽略。 |
| `Progress` | 整组移动所依据的进度。 |
| `At(start, end)` | 以 `Progress` 插值组内某个通道。 |

**说明：**
- 存在的理由：缓动曲线可能越过 1，而一组通道必须**按同一个进度**移动，否则值会被扭曲而不只是被推过目标 —— 逐通道插值颜色会让红先饱和而绿继续爬，色相就偏了。本类型找出让每个已加入通道都留在范围内的最大进度，且后来者绝不放松它。
- 该组剩余的过冲被丢弃，这是不可避免而非妥协：一个保持比例的值无法在越过上限的同时留在其类型可表示的范围内。没有上下限的通道干脆不加进来，于是它保留完整缓动时间 —— alpha 是典型例子（它自成一个单通道范围，放进来会让本已不透明的 opacity 截断颜色的过冲）。
- 对 `[0, 1]` 内的缓动时间，结果永远是同一个时间：在两个都在范围内的端点间插值不会出范围，所以只有过冲会受影响。
- *核验：* `AUTO TEST` 一致性套件中独立写就的 `Conformance/ClosedForm.SharedProgress` / `ColorAt`；`Src/Core/VeloxDev.Core.Test/TransitionSystem/EaseOvershootTests.cs`。

### 异常：`TransitionPathConflictException`

在过渡**构建**期间由具体 `StateCore.SetValue` 抛出，当新来的路径位于本次过渡上已有路径之上或之下时。一个对象必须由且只由一条路径表达：整对象路径与其某个子叶路径同时存在时，整对象采样器与子叶采样器会每帧写同一个对象，结果取决于它们恰好运行的顺序。重复声明同一条路径只是普通覆盖，允许。

```csharp
public sealed class TransitionPathConflictException : Exception
{
    public TransitionPathConflictException(ITransitionProperty existing, ITransitionProperty conflicting);
    public ITransitionProperty Existing { get; }
    public ITransitionProperty Conflicting { get; }
}
```

**说明：** 该检查只覆盖**一次**过渡的值路径（所有值路径必经的漏斗）。两条过渡各自持有自己的 state，因此它们之间的冲突检测不到 —— 经 `SetInterpolator` / `SetOptions` 注册的路径也不检测。*核验：* `TransitionPathConflictTests`。

### 异常：`TransitionPathUnsampleableException`

由 **`Transition<T>.Execute(...)` 同步抛出**，当一条声明路径永远无法动画：其叶为引用类型，既无自定义插值器也无注册采样器，没有任何可用来插值的东西。值类型豁免 —— 它仍可逐成员装配。

```csharp
public sealed class TransitionPathUnsampleableException : Exception
{
    public TransitionPathUnsampleableException(ITransitionProperty property);
    public ITransitionProperty Property { get; }
}
```

**说明：** 它在过渡**运行**时而不是构建时抛出 —— 那是每条路径、每个插值器、适配器注册的每个采样器都已确定的第一个时刻，因此一条只是暂时看起来不可采样、直到其插值器被声明的路径不会被误拒。它与 `TransitionProperty.UnreadablePath` 无关，后者是路径有效但不匹配当前目标运行时类型：那仍是逐帧跳过。请改为逐成员表达该值，或为该类型注册专门的 `ISampler`。*核验：* `TransitionPathValidationTests`。
