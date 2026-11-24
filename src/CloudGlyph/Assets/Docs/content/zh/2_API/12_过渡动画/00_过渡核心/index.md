# 过渡核心

链模型、按目标的控制面与帧状态。命名空间：`VeloxDev.TransitionSystem.Abstractions`（链、状态、属性）与 `VeloxDev.TransitionSystem`（流式扩展、异常）。

## VeloxDev.TransitionSystem.Abstractions

### 类：TransitionCore

非泛型控制面。所有成员都是静态的，按目标而非按快照寻址。

**签名：** `public abstract class TransitionCore`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Create<TSnapshot>` | `static TSnapshot Create<TSnapshot>() where TSnapshot : StateSnapshotCore, new()` | 创建快照并标记为链根。 |
| `Exit<T>` | `static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 取消 `target` 上每个选中的运行。停止是信号；调用返回时该运行可能仍在释放调度器。 |
| `Pause<T>` | `static void Pause<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 冻结选中的时间轴；暂停时间不计入动画。 |
| `Resume<T>` | `static void Resume<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 以最后设置的速率恢复。 |
| `SetRate<T>` | `static void SetRate<T>(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 乘以流逝时间。零值冻结但不置 `IsPaused`；负值抛 `ArgumentOutOfRangeException`。 |
| `Seek<T>` | `static void Seek<T>(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 在当前趟内移动。越过末尾即完成；负值固定在开头。 |
| `Seek<T>` | `static void Seek<T>(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 在指定趟内移动。 |
| `Cycle<T>` | `static int Cycle<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 正在播放的趟号；无运行时为 0。 |
| `IsPaused<T>` | `static bool IsPaused<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 每个选中的运行都暂停且至少有一个时为真。 |
| `Position<T>` | `static TimeSpan Position<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 当前趟内的位置；否则为 `TimeSpan.Zero`。 |
| `Rate<T>` | `static double Rate<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | 已配置速率，跨暂停保留；无运行时为 0。 |

`IncludeMutual` 寻址后续 `Execute` 会取代的运行；`IncludeNoMutual` 寻址以 `CanMutualTask: false` 启动的并发运行。

### 类：TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore>

强类型链段。

**签名：**
`public class TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore> : StateSnapshotCore<T> where T : class where TStateCore : IFrameState, new() where TEffectCore : ITransitionEffect<TPriorityCore>, new() where TInterpolatorCore : InterpolatorCore, new() where THost : ITransitionHost<TPriorityCore>, new() where TTransitionInterpreterCore : ITransitionInterpreter<TPriorityCore>, new()`

| 成员 | 签名 | 说明 |
|---|---|---|
| `RepeatTime` | `int RepeatTime { get; set; }` | 从首段到本段的链额外迭代次数。`0` 运行一次；`int.MaxValue` 永久运行。 |
| `GetState` | `TStateCore GetState()` | 本段的帧状态。 |
| `Execute` | `static void Execute(T target, IEnumerable<TransitionCore<…>> values, bool CanMutualTask = false)` | 启动一批快照，默认非互斥。 |

受保护字段：`state`、`root`、`next`、`effect`、`interpolator`。

### 类：StateSnapshotCore<T>

强类型快照基类，也是链段上的公开执行面。

**签名：** `public abstract class StateSnapshotCore<T> : StateSnapshotCore where T : class`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Execute` | `void Execute(T target, bool CanMutualTask = true)` | 校验链并启动。`CanMutualTask: true` 取消目标上的上一次运行。 |
| `Execute` | `void Execute(T target, ITimeSourceControl timeline, bool CanMutualTask = true)` | 针对共享时间轴启动；此时暂停与速率会移动所有锚定其上的动画。 |
| `Exit` | `void Exit(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价于 `TransitionCore.Exit`。 |
| `Pause` | `void Pause(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价于 `TransitionCore.Pause`。 |
| `Resume` | `void Resume(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价于 `TransitionCore.Resume`。 |
| `SetRate` | `void SetRate(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价于 `TransitionCore.SetRate`。 |
| `Seek` | `void Seek(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价于 `TransitionCore.Seek`。 |
| `Seek` | `void Seek(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价于按趟重载。 |
| `IsPaused` | `bool IsPaused(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价查询。 |
| `Position` | `TimeSpan Position(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价查询。 |
| `Cycle` | `int Cycle(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价查询。 |
| `Rate` | `double Rate(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | 等价查询。 |

**异常：** 声明路径永远无法动画时 `Execute` 抛 `TransitionPathUnsampleableException`；`timeline` 为 null 时抛 `ArgumentNullException`。

### 类：StateSnapshotCore

非泛型快照契约。成员是 `TransitionCore<…>` 实现的 internal 抽象；不直接使用。

**签名：** `public abstract class StateSnapshotCore`

### 类：StateCore

默认帧状态：按 `ITransitionProperty` 键控的值、采样器与逐属性选项。

**签名：** `public class StateCore : IFrameState`

| 成员 | 类型 | 说明 |
|---|---|---|
| `Values` | `virtual ConcurrentDictionary<ITransitionProperty, object?>` | 每个动画属性的终值。 |
| `Interpolators` | `virtual ConcurrentDictionary<ITransitionProperty, ISampler>` | 逐属性采样器覆盖。 |
| `Options` | `virtual ConcurrentDictionary<ITransitionProperty, object?>` | 传给采样器的逐属性选项。 |

| 方法 | 签名 |
|---|---|
| `SetInterpolator` | `virtual void SetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, ISampler interpolator)` |
| `SetValue` | `virtual void SetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, TValue? value)` |
| `TryGetInterpolator` | `virtual bool TryGetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out ISampler? interpolator)` |
| `TryGetValue` | `virtual bool TryGetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out TValue? value)` |
| `SetInterpolator` | `virtual void SetInterpolator(ITransitionProperty propertyInfo, ISampler interpolator)` |
| `SetValue` | `virtual void SetValue(ITransitionProperty propertyInfo, object? value)` |
| `TryGetInterpolator` | `virtual bool TryGetInterpolator(ITransitionProperty propertyInfo, out ISampler? interpolator)` |
| `TryGetValue` | `virtual bool TryGetValue(ITransitionProperty propertyInfo, out object? value)` |
| `SetInterpolator` | `virtual void SetInterpolator(PropertyInfo propertyInfo, ISampler interpolator)` |
| `SetValue` | `virtual void SetValue(PropertyInfo propertyInfo, object? value)` |
| `TryGetInterpolator` | `virtual bool TryGetInterpolator(PropertyInfo propertyInfo, out ISampler? interpolator)` |
| `TryGetValue` | `virtual bool TryGetValue(PropertyInfo propertyInfo, out object? value)` |
| `SetOptions` | `virtual void SetOptions<TSource, TValue>(Expression<Func<TSource, TValue>> expression, object? options)` |
| `SetOptions` | `virtual void SetOptions(ITransitionProperty property, object? options)` |
| `SetOptions` | `virtual void SetOptions(PropertyInfo propertyInfo, object? options)` |
| `TryGetOptions` | `virtual bool TryGetOptions(ITransitionProperty property, out object? options)` |
| `Clone` | `virtual IFrameState Clone()` |

`SetValue` 拒绝已声明路径的祖先或后代路径，抛 `TransitionPathConflictException`；重复添加同一路径是普通覆盖。

### 类：TransitionProperty

一个动画值的已编译路径。它既是访问器也是字典键，因此相等性至关重要。

**签名：** `public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `TransitionProperty(IEnumerable<PropertyInfo> segments)` | 纯属性路径；拒绝索引段。 |
| `Path` | `string Path { get; }` | 路径文本，仅用于诊断。 |
| `PropertyType` | `Type PropertyType { get; }` | 路径末端值类型。 |
| `CanRead` / `CanWrite` | `bool { get; }` | 全部段可读 / 末段可写。 |
| `UnreadablePath` | `static readonly object` | 路径与目标不匹配时 `GetValue` 返回的哨兵。 |
| `GetValue` | `object? GetValue(object? target)` | 读取；运行期类型不符时返回 `UnreadablePath`。 |
| `SetValue` | `bool SetValue(object target, object? value)` | 写入；路径不适用时返回 false。 |
| `TryCreate` | `static bool TryCreate(LambdaExpression expression, out TransitionProperty? property)` | 解析 lambda，包括嵌套属性与索引段。 |
| `FromProperty` | `static TransitionProperty FromProperty(PropertyInfo propertyInfo)` | 包装单个成员。 |
| `Members<TSource>` | `static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | 为 `ISampleable.GetAnimatableMembers` 声明成员。 |
| `ReadableMembers<TSource>` | `static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | 可读子集。 |
| `Combine` | `static TransitionProperty Combine(TransitionProperty prefix, TransitionProperty suffix)` | 拼接两条路径。 |
| `IsDescendantOf` | `bool IsDescendantOf(TransitionProperty other)` | 本路径是否延伸自 `other`。 |
| `Equals` / `GetHashCode` / `ToString` | 标准重写 | 按段与索引实参的值相等。 |

### 异常

| 类型 | 签名 | 条件 |
|---|---|---|
| `TransitionPathConflictException` | `public sealed class TransitionPathConflictException : Exception` | 路径声明在已有路径之上或之下。 |
| `TransitionPathUnsampleableException` | `public sealed class TransitionPathUnsampleableException : Exception` | 声明的引用类型路径没有采样器。 |

## VeloxDev.TransitionSystem

### 类：PathIndex

把过渡路径中的索引实参标记为只求值一次而非每帧求值。

**签名：** `public static class PathIndex`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Frozen<T>` | `static T Frozen<T>(T value)` | 在整个动画期间钉住索引实参。该调用从不执行；路径解析器结构化识别它并解包参数。 |

用法：`Transition<T>.Create().Property(x => x.Items[PathIndex.Frozen(i)].Width, end)`。该调用是路径身份的一部分，因此 `Items[i]` 与 `Items[Frozen(i)]` 是两条不同路径。终值必须落在它被读取的槽位时，就钉住索引。

### 类：TransitionCoreEx

对任意 `StateSnapshotCore` 的流式链构建。

**签名：** `public static class TransitionCoreEx`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Await<T>` | `static T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | 在下一段之前延时。 |
| `Then<T>` | `static T Then<T>(this T snapshot) where T : StateSnapshotCore, new()` | 立即开始一段。 |
| `AwaitThen<T>` | `static T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | 延时后开始一段。 |
| `Repeat<T>` | `static T Repeat<T>(this T snapshot, int count) where T : StateSnapshotCore, new()` | 额外循环迭代；只有末段的计数才重复整条链。 |
| `Interpolator<TSnapshot, TTarget, TValue>` | `static TSnapshot Interpolator<TSnapshot, TTarget, TValue>(this TSnapshot snapshot, Expression<Func<TTarget, TValue>> propertyLambda, ISampler interpolator)` | 覆盖某个属性的采样器。 |

## 示例

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var box = new Rectangle { RenderTransform = new TranslateTransform() };

var chain = Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0.25d)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 220d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1.5), Ease = Eases.Cubic.InOut });

chain.Execute(box);
Transition.Pause(box);
Transition.Seek(box, TimeSpan.FromMilliseconds(750));
Transition.Exit(box);
```

`Transition<T>` 是适配器前端；见[平台适配类型](../04_平台适配类型/index.md)。
