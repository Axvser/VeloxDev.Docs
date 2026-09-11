# Transition — 契约：采样与属性路径

命名空间 `VeloxDev.TransitionSystem`。这四个契约描述「值如何被采样」以及「目标属性如何被声明与寻址」。

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
| `NormalizeStart` | 返回在 `t <= 0` 时要写入的值。默认原样返回 `start`；采样器可返回副本（如可变引用类型的克隆），避免目标与共享的 start 实例互为别名。 |
| `NormalizeEnd` | 返回在 `t >= 1` 时要写入的值。默认原样返回 `end`；出于同样的别名原因可返回副本。 |
| `InsertFrame` | 计算 `t ∈ [0, 1]` 处的帧并写入 `target` 上的 `property`。`working` 是「每动画可复用」的临时对象（首帧中间帧经 `ref` 惰性创建，此后复用——零逐帧分配）；值类型采样器忽略它。 |

**说明：**
- 实现应为无状态、线程安全、共享单例，注册于 `Abstractions.InterpolatorCore.NativeInterpolators`（或作为 `IFrameState.Interpolators` 中的逐属性覆盖）。
- 端点在 `InsertFrame` 内部处理：`t <= 0` 写精确（归一化后的）start，`t >= 1` 写精确 end。不存在 `Update`/`Sample` 方法——该三方法形态取代了旧的 `IValueInterpolator`/`IInPlaceSampler` 设计。
- 实现**不得修改** `start` / `end` 参数：它们与记录它们的快照共享，修改会污染快照。
- `options` 仍携带 `RotationDirection` 供角度采样器使用（见 [02_eases](../02_eases/index.md)）。
- *验证依据：* `NativeSamplersTests`（`DoubleSampler_Endpoints_AreExact`、`DoubleSampler_NullStart_TreatsAsZero`）、`NativeSamplersExtendedTests`（各 `_BasicLinear`）、`SamplerSetTests`。

### 接口：`ISampleable`

```csharp
public interface ISampleable
{
    IReadOnlyList<ITransitionProperty> GetAnimatableMembers();
    object? CreateFrameValue(IReadOnlyList<object?> memberValues);
}
```

**说明：**
- **只服务值类型。** 复合*值类型*（结构体）用 `GetAnimatableMembers()` 声明它哪些成员可动画、用 `CreateFrameValue` 声明如何由插值后的成员重建该值。**引用类型不走这条路**：引用类型持有的复合值必须用**逐成员显式路径**（`Property(x => x.Foo.Bar, end)`）表达，或交给一个专用 `ISampler` 在内部完成分解。
- `GetAnimatableMembers` 返回相对本类型的路径（**单层、不递归**）。推荐用 `TransitionProperty.Members<Foo>(f => f.Bar, ...)` 声明（见 [01_abstractions](../../01_abstractions/index.md)）。
- `CreateFrameValue` 按 `GetAnimatableMembers` 的顺序、用已插值的成员重建一个值。**结构体**实现它以便在编译期经构造函数重建（零反射）。
- 仅当该类型没有注册采样器时才需要它：`Prepare` 的采样器解析顺序是「逐属性自定义覆盖 → 按 `PropertyType` 查注册表 → 值类型 `ISampleable`」，前两者都落空后才会走本接口。复杂的组合类型（变换矩阵、画刷……）应自带专用 `ISampler` 在内部完成分解/归一化/插值——它们无需实现本接口。
- 在 `Prepare`（见 [01_abstractions](../../01_abstractions/index.md)）期间，实现了 `ISampleable` 的**结构体**值类型会被重组：每个声明成员由各自注册的采样器插值，再经 `CreateFrameValue` 重建整个结构体。WorkflowSystem 的 `Viewport`（结构体）是工作流域内的实例；`Offset` / `Anchor` / `Size` / `Scale` 是引用类型，**不再**实现本接口。
- 若某结构体的成员采样器解析不全，`StructAssembler.Create` 返回 `null`，该属性在动画中被跳过。
- *验证依据：* `NativeSamplersExtendedTests`（测试用结构体）、`StructAssemblerTests`、`ISampleableAnimationTests`。

### 接口：`ITransitionProperty`

```csharp
public interface ITransitionProperty
{
    string Path { get; }
    Type PropertyType { get; }
    PropertyInfo PropertyInfo { get; }
    IReadOnlyList<PropertyInfo> Segments { get; }
    bool CanRead { get; }
    bool CanWrite { get; }
    object? GetValue(object target);
    bool SetValue(object target, object? value);
}
```

| 成员 | 类型 | 说明 |
|---|---|---|
| `Path` | `string` | 点分隔的嵌套属性路径（如 `"RenderTransform.X"`）。 |
| `PropertyType` | `Type` | 叶子属性的类型。 |
| `PropertyInfo` | `PropertyInfo` | 叶子属性的元数据。 |
| `Segments` | `IReadOnlyList<PropertyInfo>` | 完整属性链（只读）。 |
| `CanRead` / `CanWrite` | `bool` | 整条链是否可读 / 叶子是否可写。 |
| `GetValue` | `object? GetValue(object target)` | 沿链读取。中间对象*运行时类型*不匹配路径（路径无效）时返回 `Abstractions.TransitionProperty.UnreadablePath`；中间对象确实为 null 时返回 `null`。 |
| `SetValue` | `bool SetValue(object target, object? value)` | 沿链写入。中间类型不匹配或为 null 时返回 `false`（不抛 `TargetException`）；引用类型叶子写入 `null` 被允许并返回 `true`。 |

**说明：**
- 具体类型 `TransitionProperty`（命名空间 `VeloxDev.TransitionSystem.Abstractions`）在首次使用时把 getter/setter **编译为单个委托**——无逐帧反射（见 [01_abstractions](../../01_abstractions/index.md)）。
- *验证依据：* `TransitionPropertyTests`（`GetValue_ReadsFromTarget`、`SetValue_WritesToTarget`、`GetValue_IntermediateTypeMismatch_ReturnsUnreadablePath_NotTargetException`、`SetValue_IntermediateTypeMismatch_ReturnsFalse_NotTargetException`、`GetValue_NullIntermediate_ReturnsNull_NotUnreadable`）。

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
- 以 `ITransitionProperty` 为键的三个 `ConcurrentDictionary`：记录的目标 `Values`、逐属性 `ISampler` 覆盖、逐属性 `Options`（例如 `RotationDirection`）。
- 每个 `Set*/TryGet*` 操作都有三种重载族——表达式 lambda、`ITransitionProperty`、`PropertyInfo`。表达式 / `PropertyInfo` 重载与基于键的形式寻址同一路径。
- 表达式重载只记录可读**且**可写路径（具体实现 `StateCore` 会拒绝记录只读或不可写路径）。
- `Clone()` 返回三个字典的独立副本（快照分段入队时被 `CoreRecordState` 使用）。
- `InterpolatorCore.Prepare` 消费状态：读取 `state.Values`、从 `state.Interpolators` 查询逐属性采样器覆盖、从 `state.Options` 取 options 参数。
- *验证依据：* `StateCoreTests`（`SetValue_Expression_CanRetrieve`、`SetInterpolator_Expression_CanRetrieve`、`Clone_ReturnsIndependentCopy`）、`TransitionPathConflictTests`。
