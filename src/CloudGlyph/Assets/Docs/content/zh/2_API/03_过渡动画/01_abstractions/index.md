# Transition — 引擎实现：`VeloxDev.TransitionSystem.Abstractions`

`VeloxDev.Core` 程序集中的 `VeloxDev.TransitionSystem.Abstractions` 命名空间（源码：`Src/Core/VeloxDev.Core/TransitionSystem/*.cs`）。这些具体 / 抽象基础类型实现了 [00_transitionsystem](../00_transitionsystem/index.md) 记录的契约。各平台适配器子类化它们，产出你实际构造的 `VeloxDev.TransitionSystem` 类型（见 [03_adapter-provided](../03_adapter-provided/index.md)）。

## 快照构建器与状态

### 类：`TransitionCore<TTarget, TStateSnapshotCore>` / `TransitionCore`

```csharp
public abstract class TransitionCore
{
    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}

public class TransitionCore<TTarget, TStateSnapshotCore> : TransitionCore
    where TStateSnapshotCore : new()
{
    public static TStateSnapshotCore Create();

    public static void Execute<T>(T target, StateSnapshotCore value, bool CanMutualTask = true) where T : class, TTarget;
    public static void Execute(StateSnapshotCore values, bool CanMutualTask = true);
    public static void Execute<T>(T target, IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false) where T : class, TTarget;
    public static void Execute(IEnumerable<StateSnapshotCore> values, bool CanMutualTask = false);
}
```

| 成员 | 说明 |
|---|---|
| `Exit<T>(T target, bool IncludeMutual, bool IncludeNoMutual)` | 停止目标上正在运行的动画：`IncludeMutual` 时取消互斥调度器（以 `CanMutualTask: true` 启动的动画），`IncludeNoMutual` 时取消全部非互斥调度器。 |
| `Create()` | 返回一个新的 `TStateSnapshotCore`（全新的、未链接的快照）并把它标记为链的*根*，使后续 `Then()` / `AwaitThen()` 分段共享它。 |
| `Execute(...)` | 对 `target` 运行一个或多个快照（使用无 target 重载时对快照各自记录的目标运行）。单快照默认 `CanMutualTask: true`——使用该目标上的*互斥*调度器并打断正在运行的动画；`false` 时经一次性非互斥调度器并发运行。`IEnumerable` 重载默认 `CanMutualTask: false`。 |

**说明：** 各适配器暴露非泛型 `Transition : TransitionCore` 与 `Transition<T> : TransitionCore<T, Transition<T>.StateSnapshot>`——通常你调用 `Transition<T>.Create()`、`Transition.Exit(...)` 与 `Execute` 扩展（见 [03_adapter-provided](../03_adapter-provided/index.md)）。`AddNoMutual` / `RemoveNoMutual` 为 `internal`。*验证依据：* WPF 示例 `MainWindow.xaml.cs`。

### 类：`StateSnapshotCore`（流式构建器基础家族）

```csharp
public class StateSnapshotCore<T, TStateCore, TEffectCore, TInterpolatorCore, TUIThreadInspectorCore, TTransitionInterpreterCore> : StateSnapshotCore<T>
    where TStateCore : IFrameState, new()
    where TEffectCore : ITransitionEffectCore, new()
    where TInterpolatorCore : InterpolatorCore, new()
    where TUIThreadInspectorCore : IUIThreadInspector, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter, new()
{
    public TStateCore GetState();
}

public class StateSnapshotCore<T, TStateCore, TEffectCore, TInterpolatorCore, TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore> : StateSnapshotCore<T>
    where TStateCore : IFrameState, new()
    where TEffectCore : ITransitionEffect<TPriorityCore>, new()
    where TInterpolatorCore : InterpolatorCore, new()
    where TUIThreadInspectorCore : IUIThreadInspector<TPriorityCore>, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()
{
    public TStateCore GetState();
}

public abstract class StateSnapshotCore<T> : StateSnapshotCore { }
public abstract class StateSnapshotCore { }
```

**说明：**
- 两个具体泛型类仅在优先级轴上有别：6 泛型元数变体供无 dispatcher 优先级的适配器使用（MAUI、WinForms、Razor）；7 泛型元数变体——新增 `TPriorityCore`——供 WPF、Avalonia、Jalium 与 WinUI 使用。
- 唯一的 public 成员是 `GetState()`（返回底层 `TStateCore`，一个实现 `IFrameState` 的 `StateCore`）。其余都是 `internal`/`protected` 机制：`CoreExecute` 遍历链接的分段（`next`），把每段的插值器 / 延迟 / 克隆效果 / 状态逐一交给调度器；`CoreThen`/`CoreAwaitThen`/`CoreEffect`/`CoreInterpolator` 是公开扩展与适配器重载调用的钩子。
- 因为多数成员为 protected，构建器的*公开*词汇来自 `TransitionCoreEx`（下）以及各适配器嵌套 `StateSnapshot` 的重载（`Property`、`Effect`）。
- *验证依据：* WPF 示例在 `Transition<Rectangle>.StateSnapshot` 上链式 `.Property(...)`、`.Effect(...)`、`.Await(...)`、`.AwaitThen(...)`，并遍历 `snapshot.GetState().Values`。

### 静态类：`TransitionCoreEx`（扩展，命名空间 `VeloxDev.TransitionSystem`）

| 成员 | 签名 | 说明 |
|---|---|---|
| `Await` | `T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | 本段播放前等待一段时间。 |
| `Then` | `T Then<T>(this T snapshot) where T : StateSnapshotCore, new()` | 本段之后开启新的链接分段。 |
| `AwaitThen` | `T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | 等待 `timeSpan` 后再开启新的链接分段。 |
| `Interpolator` | `TSnapshot Interpolator<TSnapshot, TTarget, TValue>(this TSnapshot snapshot, Expression<Func<TTarget, TValue>> propertyLambda, ISampler interpolator) where TSnapshot : StateSnapshotCore, new()` | 为 `propertyLambda` 覆盖逐属性采样器。 |
| `Execute` | `void Execute<T>(this T snapshot, object target, bool CanMutualTask = true) where T : StateSnapshotCore` | 在 `target` 上运行快照。 |
| `Execute` | `void Execute<T>(this T snapshot, bool CanMutualTask = true) where T : StateSnapshotCore` | 在记录的目标上运行快照。 |

**说明：** `Await` / `Then` / `AwaitThen` 通过改动快照链记录其延迟 / 链接（延迟由 `CoreExecute` 在运行该段前以 `Task.Delay` 兑现）。*验证依据：* WPF 示例（`Animation0`/`Animation1`/`Animation2`）。

### 类：`StateCore : IFrameState`

`IFrameState` 的具体默认实现；适配器的 `State` 派生自它（见 [03_adapter-provided](../03_adapter-provided/index.md)）。

| 成员 | 类型 | 说明 |
|---|---|---|
| `Values` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Values { get; protected set; }` | 记录的目标值。 |
| `Interpolators` | `virtual ConcurrentDictionary<ITransitionProperty, ISampler> Interpolators { get; protected set; }` | 逐属性采样器覆盖。 |
| `Options` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Options { get; protected set; }` | 逐属性插值选项。 |
| `SetValue` / `TryGetValue` | 三种重载族 | `(Expression<Func<TSource, TValue>>, TValue?)`、`(ITransitionProperty, object?)`、`(PropertyInfo, object?)`；`Try*` 有对应 `out` 形式。 |
| `SetInterpolator` / `TryGetInterpolator` | 三种重载族 | 寻址相同，值为 `ISampler`。 |
| `SetOptions` / `TryGetOptions` | 三种 / 一种重载族 | `SetOptions` 有表达式 / `ITransitionProperty` / `PropertyInfo` 形式；`TryGetOptions` 只有 `ITransitionProperty` 形式。 |
| `Clone` | `virtual IFrameState Clone()` | 三个字典的独立浅拷贝。 |

**说明：** 表达式重载只记录可读且可写路径；字典为 `protected set`，派生适配器状态可替换它们。*验证依据：* `StateCoreTests`。

## 引擎：采样器注册表、预备集合、效果、调度器、解释器、检查器

### 抽象类：`InterpolatorCore`

```csharp
public abstract class InterpolatorCore
{
    static InterpolatorCore();   // 初始化默认注册表
    public static ConcurrentDictionary<Type, ISampler> NativeInterpolators { get; protected set; }

    public static bool TryGetInterpolator(Type type, out ISampler? sampler);
    public static bool RegisterInterpolator(Type type, ISampler sampler);
    public static bool UnregisterInterpolator(Type type, out ISampler? sampler);

    public virtual SamplerSet Prepare(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector);
}
```

| 成员 | 说明 |
|---|---|
| `NativeInterpolators` | 以 `Type` 为键的全局注册表。静态构造函数预置：`double`、`float`、`int`、`long`、`System.Drawing.Point/PointF/Size/SizeF/Color/Rectangle/RectangleF`，以及（仅当不以 `netstandard2.0` 为目标编译时）`System.Numerics.Vector2/Vector3/Vector4/Quaternion`。 |
| `RegisterInterpolator` | 以**后写者胜**语义（`AddOrUpdate`）安装采样器——无条件、原子。返回 `true`。 |
| `UnregisterInterpolator` | 移除条目；经 `sampler` 报告被移除者。 |
| `TryGetInterpolator` | 在注册表查找类型。 |
| `Prepare` | 把已记录状态归一化为可运行的 `SamplerSet`。 |

**`Prepare` 说明：** 对每个记录值经 `inspector.ProtectedGetValue` 读取当前值；无效路径（`TransitionProperty.UnreadablePath`）被跳过。采样器解析顺序：(1) `state.Interpolators` 中的逐属性自定义采样器；(2) 按 `PropertyType` 查注册表；(3) 实现了 `ISampleable` 的*结构体*值类型 → 内部结构体重组采样器（各成员采样器须全部可解析，否则跳过）。随后各调用一次 `sampler.NormalizeStart(current, newValue, options)` / `NormalizeEnd(...)`，逐条存入 `(property, sampler, normalizedStart, normalizedEnd, options)`。适配器派生 `Interpolator : InterpolatorCore` 并在静态构造函数注册平台类型。*验证依据：* `InterpolatorCoreTests`。

### 类：`SamplerSet`

```csharp
public sealed class SamplerSet
{
    public SamplerSet(IUIThreadInspectorCore inspector);
    public bool CanSetValue();
    public void Apply(object target, double t, object? priority = default);
}
```

**说明：** 构造函数对 null 检查器抛 `ArgumentNullException`。`CanSetValue()` 返回 `inspector.IsAppAlive()`。`Apply` 把逐属性更新编组到 UI 线程——把 `t` 存入字段并复用一个按目标缓存的 UI 线程委托（每次采样零闭包分配），再调用 `inspector.ProtectedInvoke`；在 UI 线程上依序执行每个条目的 `sampler.InsertFrame(target, property, ref working, start, end, options, t)`。`SetCancellation(cts)`（internal，由解释器调用）让集合携带动画的 `CancellationTokenSource`：一旦取消——或应用已死——`Apply` 立即返回，因此已入队的过期帧永远不会覆盖重置结果。*验证依据：* `SamplerSetTests`。

### 类：`TransitionEffectCore : ITransitionEffectCore`

默认描述符实现。默认值：`FPS = 60`、`Duration = 0`、`IsAutoReverse = false`、`LoopTime = 0`、`Ease = Eases.Default`。

| 成员 | 类型 / 签名 |
|---|---|
| 属性 | `virtual int FPS`、`virtual TimeSpan Duration`、`virtual bool IsAutoReverse`、`virtual int LoopTime`、`virtual IEaseCalculator Ease`（均为 `{ get; set; }`） |
| 事件 | `virtual event EventHandler<TransitionEventArgs>`——`Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally` |
| 调用器 | `virtual void InvokeAwake/InvokeStart/InvokeUpdate/InvokeLateUpdate/InvokeCompleted/InvokeCancled/InvokeFinally(object sender, TransitionEventArgs e)` |
| `Clone` | `ITransitionEffectCore Clone()` |

**说明：** 事件由 `WeakDelegate`（`VeloxDev.WeakTypes`）支撑，因此短命处理函数持有者不会泄漏；`Clone` 深克隆事件后备存储并复制全部属性。`InvokeCancled`（原文拼写如此）是真实成员名。子类 `TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>` 增加 `virtual TPriorityCore Priority { get; set; }` 与 `new ITransitionEffect<TPriorityCore> Clone()`。平台以优先级编组的适配器效果派生自优先级变体，否则派生自普通基类。*验证依据：* `TransitionEffectCoreTests`。

### 抽象类：`TransitionSchedulerCore : ITransitionSchedulerCore`

```csharp
public abstract class TransitionSchedulerCore : ITransitionSchedulerCore
{
    public static ConditionalWeakTable<object, ITransitionSchedulerCore> MutualSchedulers { get; protected set; }
    public static ConditionalWeakTable<object, List<ITransitionSchedulerCore>> NoMutualSchedulers { get; internal set; }

    public static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler);
    public static bool RemoveMutualScheduler(object source);
    public static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers);
    public static bool RemoveNoMutualScheduler(object source);

    protected readonly SemaphoreSlim _gate = new(1, 1);
    internal WeakReference<object>? targetref;
    public virtual WeakReference<object>? TargetRef { get; protected set; }
    internal CancellationTokenSource? cts { get; set; }

    protected void CancelCurrent();
    public abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**说明：** `MutualSchedulers` 每目标缓存一个*互斥*调度器（`ConditionalWeakTable`，随目标一起被回收）；`NoMutualSchedulers` 保存每目标当前活动的一次性*非互斥*调度器列表。两个泛型子类参数化具体检查器 / 解释器：
- `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore> : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore>`
- `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore> : TransitionSchedulerCore, ITransitionScheduler`

它们的 `Execute` 从弱 `TargetRef` 解析目标、在 UI 线程触发 `effect.InvokeAwake`（优先级类型化时带效果优先级）、调用 `producer.Prepare(...)`、再把准备好的集合交给新的解释器。`_gate` 串行化执行；`Exit()` → `CancelCurrent()` 取消正在运行的 `cts`。静态 `FindOrCreate<T>(T source, bool CanMutualTask = true)` 返回缓存的互斥调度器（不存在则创建）或新的非互斥调度器。*验证依据：* WPF 示例 `RepeatMutual` / `ExitAll`。

### 抽象类：`TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable`

```csharp
public abstract class TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable
{
    protected CancellationTokenSource? cts;
    public virtual TransitionEventArgs Args { get; set; }

    public abstract Task Execute(object target, SamplerSet frameSet, ITransitionEffectCore effect, CancellationTokenSource cts);
    public virtual void Exit();
    public virtual void Dispose();   // 取消当前 CancellationTokenSource

    protected Task ExecuteSamplingLoopAsync(object target, SamplerSet frameSet, ITransitionEffectCore effect,
        CancellationTokenSource cts, Action<double> apply);
}
```

**说明：** 两个泛型子类把循环接到采样集的 `Apply`：
- `TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter`（约束 `TTransitionEffectCore : ITransitionEffectCore`）——按 `easedT => frameSet.Apply(target, easedT)` 应用。
- `TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore>`（约束 `TTransitionEffectCore : ITransitionEffect<TPriorityCore>`）——按 `easedT => frameSet.Apply(target, easedT, effect.Priority)` 应用。

**采样循环语义**（`ExecuteSamplingLoopAsync`）：Stopwatch 驱动连续采样，而非帧泵。归一化时间每轮由墙钟经过时间推出（`t = elapsed / Duration`），因此 `Task.Delay` 绝不是计时来源；让步间隔上限为 `1000 / FPS` ms（`FPS` 是最大采样率，不是帧网格）。每程把原始时间钳制后应用缓动（`Back`/`Elastic` 过冲会再钳回 `[0, 1]`），然后 `InvokeUpdate` → `apply(easedT)` → `InvokeLateUpdate`；每程末帧为**精确端点**（`t >= 1` → 正程缓动 1 / 反程 0），与 `Ease(1)` 是否精确等于 1 无关。循环前触发一次 `Start`；`IsAutoReverse` 追加反程；`LoopTime` 重复（`int.MaxValue` = 无限）。正常完成触发 `Completed`；取消——取消的 `cts` **或** `Args.Handled = true` → `OperationCanceledException`——触发 `Canceled`；`Finally` 在每条结束路径触发。*验证依据：* `SamplingLoopTests`、`TransitionEffectCoreTests`。

### 抽象类：`UIThreadInspectorBase`、`UIThreadInspectorCore`、`UIThreadInspectorCore<TPriorityCore>`

```csharp
public abstract class UIThreadInspectorBase : IUIThreadInspectorCore
{
    public abstract bool IsAppAlive();
    public abstract bool IsUIThread();
    public abstract object? ProtectedGetValue(object target, ITransitionProperty property);
    public abstract void ProtectedInvoke(object target, Action action, object? priority = default);
}

public abstract class UIThreadInspectorCore : UIThreadInspectorBase, IUIThreadInspector
{
    public abstract void ProtectedInvoke(object target, Action action);
    public override void ProtectedInvoke(object target, Action action, object? priority = default);
}

public abstract class UIThreadInspectorCore<TPriorityCore> : UIThreadInspectorBase, IUIThreadInspector<TPriorityCore>
{
    public abstract void ProtectedInvoke(object target, Action action, TPriorityCore priority);
    public override void ProtectedInvoke(object target, Action action, object? priority = default); // priority 非 TPriorityCore 时为空操作
}
```

**说明：** 这些是骨架类——每个抽象成员（线程身份、编组、读编组、存活）都由各适配器的 `UIThreadInspector` 填入（见 [03_adapter-provided](../03_adapter-provided/index.md)）。优先级类型化检查器接受适配器的 dispatcher 优先级；非优先级检查器按框架默认编组。

## 属性路径与捕获

### 类：`TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>
{
    public TransitionProperty(IEnumerable<PropertyInfo> segments);   // 空或带索引的属性会抛出 ArgumentException
    public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
    public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static TransitionProperty Combine(ITransitionProperty prefix, ITransitionProperty suffix);
    public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);

    public string Path { get; }
    public Type PropertyType { get; }
    public PropertyInfo PropertyInfo { get; }
    public bool CanRead { get; }
    public bool CanWrite { get; }
    public IReadOnlyList<PropertyInfo> Segments { get; }

    public static readonly object UnreadablePath;

    public object? GetValue(object target);
    public bool SetValue(object target, object? value);
    // + IEquatable<TransitionProperty>：Equals / GetHashCode / ToString() == Path
}
```

| 成员 | 说明 |
|---|---|
| 构造函数 | 由分段链构建；`segments` 为空或含带索引的属性时抛 `ArgumentException`。 |
| `FromProperty` | 单分段属性；null 时抛 `ArgumentNullException`。 |
| `Members` | 由表达式声明可动画成员路径（供 `ISampleable.GetAnimatableMembers`）；只保留可读**且**可写成员。 |
| `ReadableMembers` | 只声明可读成员路径（用于结构体 `ISampleable` 组装——成员只读再经构造函数重建）。 |
| `Combine` | 拼接两条路径——`prefix = target.Foo`、`suffix = Foo.Bar` → `target.Foo.Bar`。 |
| `TryCreate` | 把 lambda（展开 `Convert`/`ConvertChecked`）解析为 `TransitionProperty`；非成员 / 带索引表达式返回 `false`。 |
| `UnreadablePath` | 中间对象运行时类型不匹配路径时 `GetValue` 返回的哨兵。调用方应跳过此类属性而非按 `null` 插值。 |

**说明：** getter 与 setter 在首次使用时编译为单个委托（`CompileGetter` / `CompileSetter`），消除逐帧反射——`SamplerSet.Apply` / `ProtectedGetValue` 的热路径。`GetValue` 区分确实为 null 的中间对象（`null`，插值从 identity/默认开始）与类型不匹配的中间对象（`UnreadablePath`）。`SetValue` 在中间类型不匹配或为 null、或叶子无 setter 时返回 `false`（不抛 `TargetException`）；向引用类型叶子写 `null` 被允许。相等性按段链比较；`ToString()` 返回 `Path`。*验证依据：* `TransitionPropertyTests`。

### 静态类：`TransitionSnapshotHelper`

| 成员 | 签名 | 说明 |
|---|---|---|
| `CaptureSpecific` | `void CaptureSpecific<T>(T target, IFrameState state, IEnumerable<Expression<Func<T, object?>>>? expressions) where T : class` | 只记录显式表达式路径（可读且可写）。 |
| `CaptureAll` | `void CaptureAll<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? extraExpressions = null) where T : class` | 记录所有发现的可动画路径加额外显式表达式。 |
| `CaptureAllExcept` | `void CaptureAllExcept<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? excludedExpressions = null) where T : class` | 记录发现结果，排除被排除路径**及其子路径**。 |
| `DiscoverAnimatableProperties` | `IReadOnlyCollection<ITransitionProperty> DiscoverAnimatableProperties(object target, Func<Type, bool> canAnimateType)` | 遍历对象图并返回可动画叶子路径集合。 |
| `TryGetPropertyFromExpression` | `bool TryGetPropertyFromExpression<T>(Expression<Func<T, object?>> expression, out ITransitionProperty? property) where T : class` | 解析单个表达式（须可读且可写、非带索引）。 |
| `CaptureProperties` | `void CaptureProperties(object target, IFrameState state, IEnumerable<ITransitionProperty> properties)` | 把每个可读且可写属性的当前值记录进 state。 |

**发现（`DiscoverAnimatableProperties`）说明：** 递归、带环守卫的遍历（对象回引或路径上已有的成员类型都会终止递归——**没有深度上限**；跳过带索引属性）。对每个 public 可读 + 可写实例属性：类型可动画（`canAnimateType(type)` **或** `typeof(ISampler).IsAssignableFrom(type)`）→ 整条路径即为叶子；否则值实现了 `ISampleable` → *结构体*记录整条路径（经 `CreateFrameValue` 重建）、引用类型递归展开其声明成员；否则类型可下钻（nullable 展开后，`string`、`object`、基元、枚举、值类型、`IEnumerable`、`Delegate` 均不可）且值非 null → 递归到子叶。`CaptureAll` / `CaptureAllExcept` 是 `TransitionEx.SnapshotAll` / `SnapshotExcept` 背后的引擎。*验证依据：* `TransitionSnapshotHelperTests`。
