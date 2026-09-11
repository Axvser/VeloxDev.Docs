# Transition — 引擎实现：`VeloxDev.TransitionSystem.Abstractions`

`VeloxDev.Core` 程序集中的 `VeloxDev.TransitionSystem.Abstractions` 命名空间（源码：`Src/Core/VeloxDev.Core/TransitionSystem/*.cs`）。这些具体 / 抽象基础类型实现了 [00_transitionsystem](../00_transitionsystem/index.md) 记录的契约。各平台适配器子类化它们，产出你实际构造的 `VeloxDev.TransitionSystem` 类型（见 [03_adapter-provided](../03_adapter-provided/index.md)）。

## 状态构建器与状态

### 抽象类：`TransitionCore`（静态入口）

```csharp
public abstract class TransitionCore
{
    public static TSnapshot Create<TSnapshot>() where TSnapshot : StateSnapshotCore, new();
    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}
```

| 成员 | 说明 |
|---|---|
| `Create<TSnapshot>()` | 新建一个 `TSnapshot` 并调用它的 `AsRoot()`，把它标记为分段链的*根*，使后续 `Then()` / `AwaitThen()` 分段共享它。适配器把它包装成 `Transition<T>.Create()`。 |
| `Exit<T>(T target, bool IncludeMutual, bool IncludeNoMutual)` | 停止目标上正在运行的动画：`IncludeMutual` 时取消互斥调度器（以 `CanMutualTask: true` 启动的动画），`IncludeNoMutual` 时取消全部非互斥调度器。取消是*信号*——动画在下一个 await 点停止，因此本方法返回时它可能仍在释放调度器。 |

**说明：** `RejectUnsampleablePaths` / `AddNoMutual` / `RemoveNoMutual` 是 `internal`。*验证依据：* WPF 示例 `ExitAll`。

### 类：`TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore>`

```csharp
public class TransitionCore<
    T, TStateCore, TEffectCore, TInterpolatorCore,
    TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore> : StateSnapshotCore<T>
    where T : class
    where TStateCore : IFrameState, new()
    where TEffectCore : ITransitionEffect<TPriorityCore>, new()
    where TInterpolatorCore : InterpolatorCore, new()
    where TUIThreadInspectorCore : IUIThreadInspector<TPriorityCore>, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()
{
    public TStateCore GetState();

    public static void Execute(
        T target,
        IEnumerable<TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore,
            TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore>> values,
        bool CanMutualTask = false);
}
```

**说明：**
- **单一元数。** 先前的 6 元数与 7 元数两套近乎逐字拷贝的家族已合并为本类；无分发器优先级的宿主（MAUI / WinForms / Razor）用 `VeloxDev.TransitionSystem.NonPriority`（空 `readonly struct`，只填类型参数、从不实例化）填充 `TPriorityCore`。
- 唯一的 public 实例成员是 `GetState()`（返回底层 `TStateCore`，一个实现 `IFrameState` 的 `StateCore`）。`state` / `root` / `next` / `effect` / `interpolator` 为 `protected`；`CoreExecute` 遍历链接的分段（`next`），把每段的插值器 / 延迟 / 克隆效果 / 状态逐一交给调度器；`CoreThen` / `CoreAwaitThen` / `CoreEffect` / `CoreInterpolator` 是公开扩展与适配器重载调用的钩子。
- 静态 `Execute` 是**批量**入口：对同一个 `target` 启动一组 transition，默认 `CanMutualTask: false`（并发、互不打断——与单次执行的默认行为刻意相反），逐个先 `CoreValidate()` 再执行。
- *验证依据：* WPF 示例在 `Transition<Rectangle>` 上链式 `.Property(...)`、`.Effect(...)`、`.Await(...)`、`.AwaitThen(...)`，并遍历 `snapshot.GetState().Values`。

### 抽象类：`StateSnapshotCore` / `StateSnapshotCore<T>`

```csharp
public abstract class StateSnapshotCore<T> : StateSnapshotCore
    where T : class
{
    public void Execute(T target, bool CanMutualTask = true);
    public void Exit(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
}

public abstract class StateSnapshotCore
{
    internal abstract void AsRoot();
    internal abstract void CoreExecute(object target, bool CanMutualTask = true);
    internal abstract void CoreValidate();
    internal abstract T CoreAwait<T>(TimeSpan timeSpan) where T : StateSnapshotCore, new();
    internal abstract T CoreThen<T>() where T : StateSnapshotCore, new();
    internal abstract T CoreAwaitThen<T>(TimeSpan timeSpan) where T : StateSnapshotCore, new();
    // CoreInterpolator / CoreEffect / CoreRecordState 亦为 internal / protected
}
```

**说明：**
- 泛型层固定目标类型 `T`，因此 `Execute` 的 target 类型在编译期检查；`Execute` 先**同步**调用 `CoreValidate()`（`CoreExecute` 是 `async void`，从中抛出会逃逸到同步上下文而不是交给调用方），再启动动画。
- `Execute(target, CanMutualTask)` —— 单次执行默认 `CanMutualTask: true`：使用该目标上的*互斥*调度器并打断正在运行的动画；`false` 时经一次性非互斥调度器并发运行。
- `Exit(target, IncludeMutual, IncludeNoMutual)` 等价于 `TransitionCore.Exit`。
- 因为多数成员为 `internal` / `protected`，构建器的**公开**词汇来自 `TransitionCoreEx`（下）以及各适配器 `Transition<T>` 的 `Property` / `Effect` 重载。
- *验证依据：* WPF 示例（`Animation0`/`Animation1`/`Animation2`、`CreateResetRec0`）。

### 静态类：`TransitionCoreEx`（扩展，命名空间 `VeloxDev.TransitionSystem`）

```csharp
public static class TransitionCoreEx
{
    public static T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new();
    public static T Then<T>(this T snapshot) where T : StateSnapshotCore, new();
    public static T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new();
    public static TSnapshot Interpolator<TSnapshot, TTarget, TValue>(
        this TSnapshot snapshot,
        Expression<Func<TTarget, TValue>> propertyLambda,
        ISampler interpolator) where TSnapshot : StateSnapshotCore, new();
}
```

| 成员 | 说明 |
|---|---|
| `Await` | 本段播放前等待一段时间（写本段的 `delay`）。作为首个调用可让整条动画延迟开始。 |
| `Then` | 本段之后立即开启新的链接分段（新建同类节点并经 `next` 链接）。 |
| `AwaitThen` | 等待 `timeSpan` 后再开启新的链接分段。 |
| `Interpolator` | 为 `propertyLambda` 覆盖逐属性采样器（`state.SetInterpolator`）。 |

**说明：** 这个类**只含流程扩展**——运行/取消不是扩展方法：运行是 `StateSnapshotCore<T>.Execute(T target, bool CanMutualTask = true)` 实例方法（或静态 `TransitionCore<...>.Execute` 批量入口），取消是 `TransitionCore.Exit`。*验证依据：* WPF 示例（`Animation0`/`Animation1`/`Animation2`）。

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
| `Clone` | `virtual IFrameState Clone()` | 三个字典的独立拷贝。 |

**说明：**
- 表达式重载只记录可读**且**可写路径；`PropertyInfo` 重载经 `TransitionProperty.FromProperty` 转发到基于键的形式。字典为 `protected set`，派生适配器状态可替换它们。
- `SetValue(ITransitionProperty, object?)` 会先做**父子冲突检查**：若新路径位于已有路径之上或之下（同一 transition 内），抛 `TransitionPathConflictException`；重复添加**同一条**路径是允许的（普通覆盖）。经 `SetInterpolator` / `SetOptions` 注册的路径不参与该检查。
- *验证依据：* `StateCoreTests`、`TransitionPathConflictTests`。

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

    public virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(
        object target, IFrameState state, ITransitionEffectCore effect,
        IUIThreadInspector<TPriorityCore> inspector);
}
```

| 成员 | 说明 |
|---|---|
| `NativeInterpolators` | 以 `Type` 为键的全局注册表。静态构造函数预置：`double`、`float`、`int`、`long`、`System.Drawing.Point/PointF/Size/SizeF/Color/Rectangle/RectangleF`，以及（仅当不以 `netstandard2.0` 为目标编译时）`System.Numerics.Vector2/Vector3/Vector4/Quaternion`。 |
| `RegisterInterpolator` | 以**后写者胜**语义（`AddOrUpdate`）安装采样器——无条件、原子。返回 `true`。 |
| `UnregisterInterpolator` | 移除条目；经 `sampler` 报告被移除者。 |
| `TryGetInterpolator` | 在注册表查找类型。 |
| `Prepare<TPriorityCore>` | 把已记录状态归一化为可运行的 `SamplerSet<TPriorityCore>`；优先级经**类型参数**传入（而非 `object?`），因此热路径不装箱。 |

**`Prepare` 说明：** 对每个记录值经 `inspector.ProtectedGetValue` 读取当前值；无效路径（`TransitionProperty.UnreadablePath`）被跳过。采样器解析顺序：(1) `state.Interpolators` 中的逐属性自定义采样器；(2) 按 `PropertyType` 查注册表；(3) 仅当 `PropertyType.IsValueType` 且 `currentValue is ISampleable` → `StructAssembler.Create`（各成员采样器须全部可解析，否则返回 `null` 并被跳过）。**引用类型永远不会在此展开**。随后各调用一次 `sampler.NormalizeStart(current, newValue, options)` / `NormalizeEnd(...)`，逐条存入 `(property, sampler, normalizedStart, normalizedEnd, options)`。适配器派生 `Interpolator : InterpolatorCore` 并在静态构造函数注册平台类型。*验证依据：* `InterpolatorCoreTests`。

### 类：`SamplerSet<TPriorityCore>`

```csharp
public sealed class SamplerSet<TPriorityCore>
{
    public SamplerSet(IUIThreadInspector<TPriorityCore> inspector);
    public bool CanSetValue();
    public void Apply(object target, double t, TPriorityCore priority = default!);
}
```

**说明：** 构造函数对 null 检查器抛 `ArgumentNullException`。`CanSetValue()` 返回 `inspector.IsAppAlive()`。`Apply` 把逐属性更新编组到 UI 线程——把 `t` 存入字段并复用一个按目标缓存的 UI 线程委托（每次采样零闭包分配），再调用 `inspector.ProtectedInvoke(target, apply, priority)`；在 UI 线程上依序执行每个条目的 `sampler.InsertFrame(target, property, ref working, start, end, options, t)`。省略 `priority` 时传 `default(TPriorityCore)`——对 `NonPriority` 而言这就是全部内容。`SetCancellation(cts)`（internal，由解释器调用）让集合携带动画的 `CancellationTokenSource`：一旦取消——或应用已死——`Apply` 立即返回，因此已入队的过期帧永远不会覆盖重置结果。*验证依据：* `SamplerSetTests`。

### 类：`TransitionEffectCore` / `TransitionEffectCore<TPriorityCore>`

默认描述符实现。默认值：`FPS = 60`、`Duration = 0`、`IsAutoReverse = false`、`LoopTime = 0`、`Ease = Eases.Default`。

| 成员 | 类型 / 签名 |
|---|---|
| 属性 | `virtual int FPS`、`virtual TimeSpan Duration`、`virtual bool IsAutoReverse`、`virtual int LoopTime`、`virtual IEaseCalculator Ease`（均为 `{ get; set; }`） |
| 事件 | `virtual event EventHandler<TransitionEventArgs>`——`Awaked`、`Start`、`Update`、`LateUpdate`、`Canceled`、`Completed`、`Finally` |
| 调用器 | `virtual void InvokeAwake/InvokeStart/InvokeUpdate/InvokeLateUpdate/InvokeCompleted/InvokeCancled/InvokeFinally(object sender, TransitionEventArgs e)` |
| `Clone` | `ITransitionEffectCore Clone()` |

**说明：** 事件由 `WeakDelegate`（`VeloxDev.WeakTypes`）支撑，因此短命处理函数持有者不会泄漏；`Clone` 深克隆事件后备存储并复制全部属性。`InvokeCancled`（原文拼写如此）是真实成员名。`TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>` 增加 `virtual TPriorityCore Priority { get; set; }` 与 `new ITransitionEffect<TPriorityCore> Clone()`；无优先级基类 `TransitionEffectCore` 实现 `ITransitionEffect<NonPriority>`，其 `Priority` 恒为 `default`。*验证依据：* `TransitionEffectCoreTests`。

### 抽象类：`TransitionSchedulerCore` 与 `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore>`

```csharp
public abstract class TransitionSchedulerCore : ITransitionSchedulerCore
{
    public static ConditionalWeakTable<object, ITransitionSchedulerCore> MutualSchedulers { get; protected set; }
    public static ConditionalWeakTable<object, ConcurrentDictionary<ITransitionSchedulerCore, byte>> NoMutualSchedulers { get; internal set; }

    public static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler);
    public static bool RemoveMutualScheduler(object source);
    public static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers);
    public static bool RemoveNoMutualScheduler(object source);

    public virtual WeakReference<object>? TargetRef { get; protected set; }
    public abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**说明：** `MutualSchedulers` 每目标缓存一个*互斥*调度器（`ConditionalWeakTable`，随目标一起被回收）；`NoMutualSchedulers` 保存每目标当前活动的一次性*非互斥*调度器集合。`SemaphoreSlim` 门控（`_gate`）串行化执行；`Exit()` → `CancelDrained(DrainActive())` 取消该调度器当前持有的全部 `cts`。唯一的泛型子类是 3 元数：

- `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore> : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore>`，约束两个具体类型为 `IUIThreadInspector<TPriorityCore>` / `ITransitionInterpreter<TPriorityCore>` 且 `new()`；静态 `FindOrCreate<T>(T source, bool CanMutualTask = true) where T : class` 返回缓存的互斥调度器（不存在则经 `GetValue` 原子创建）或全新的非互斥调度器。

**Awake 时序：** 每次 `Execute` 在进入采样循环**之前**先 **await** `inspector.ProtectedInvokeAsync(target, …, effect.Priority)` 触发 `effect.InvokeAwake`——不是 fire-and-forget。这样 Awake 可以在值归一化前完成并可否决动画（`Args.Handled`），也可以把目标置为动画的起点；从后台线程启动同样成立。若检查器报告该 action 根本没入队（返回 `false`），`Execute` 直接放弃，不启动一个画不出帧的动画。*验证依据：* `TransitionSchedulerAwakeTests`、`TransitionSchedulerExitTests`、WPF 示例 `RepeatMutual` / `ExitAll`。

### 抽象类：`TransitionInterpreterCore`（及其泛型子类）

```csharp
public abstract class TransitionInterpreterCore : IDisposable
{
    protected CancellationTokenSource? cts;
    public virtual TransitionEventArgs Args { get; set; }

    public virtual void Exit();
    public virtual void Dispose();   // 取消当前 CancellationTokenSource

    protected Task ExecuteSamplingLoopAsync<TPriorityCore>(
        object target, SamplerSet<TPriorityCore> frameSet, ITransitionEffectCore effect,
        CancellationTokenSource cts, Action<double> apply);
}
```

**说明：** 非泛型的 `ITransitionInterpreter` / `ITransitionInterpreterCore` 接口**已删除**；`TransitionInterpreterCore` 只实现 `IDisposable`，两个泛型子类各自实现带优先级的 `ITransitionInterpreter<TPriorityCore>`：

- `TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore>`（约束 `TTransitionEffectCore : ITransitionEffect<TPriorityCore>`）——`Execute(object target, SamplerSet<TPriorityCore> frameSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts)`，按 `easedT => frameSet.Apply(target, easedT, effect.Priority)` 应用。
- `TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter<NonPriority>`（约束 `TTransitionEffectCore : ITransitionEffectCore`）——按 `easedT => frameSet.Apply(target, easedT)` 应用，采样留在无优先级路径上。

**采样循环语义**（`ExecuteSamplingLoopAsync`）：Stopwatch 驱动连续采样，而非帧泵。归一化时间每轮由墙钟经过时间推出（`t = elapsed / Duration`），因此 `Task.Delay` 绝不是计时来源；让步间隔上限为 `1000 / FPS` ms（`FPS` 是最大采样率，不是帧网格）。每程把原始时间钳制后应用缓动（`Back`/`Elastic` 过冲会再钳回 `[0, 1]`），然后 `InvokeUpdate` → `apply(easedT)` → `InvokeLateUpdate`；每程末帧为**精确端点**（`t >= 1` → 正程缓动 1 / 反程 0），与 `Ease(1)` 是否精确等于 1 无关。循环前触发一次 `Start`；`IsAutoReverse` 追加反程；`LoopTime` 重复（`int.MaxValue` = 无限）。正常完成触发 `Completed`；取消——取消的 `cts` **或** `Args.Handled = true` → `OperationCanceledException`——触发 `Canceled`；`Finally` 在每条结束路径触发。*验证依据：* `SamplingLoopTests`、`TransitionEffectCoreTests`。

### 抽象类：`UIThreadInspectorBase`、`UIThreadInspectorCore`、`UIThreadInspectorCore<TPriorityCore>`

```csharp
public abstract class UIThreadInspectorBase : IUIThreadInspectorCore
{
    public abstract bool IsAppAlive();
    public abstract bool IsUIThread();
    public abstract object? ProtectedGetValue(object target, ITransitionProperty property);
}

public abstract class UIThreadInspectorCore<TPriorityCore> : UIThreadInspectorBase, IUIThreadInspector<TPriorityCore>
{
    public abstract bool ProtectedInvoke(object target, Action action, TPriorityCore priority);
    public virtual Task<bool> ProtectedInvokeAsync(object target, Action action, TPriorityCore priority);
}

public abstract class UIThreadInspectorCore : UIThreadInspectorBase, IUIThreadInspector<NonPriority>
{
    public abstract bool ProtectedInvoke(object target, Action action);
    public virtual bool ProtectedInvoke(object target, Action action, NonPriority priority) => ProtectedInvoke(target, action);
    public virtual Task<bool> ProtectedInvokeAsync(object target, Action action, NonPriority priority);
}
```

**说明：**
- 非泛型接口 `IUIThreadInspector` **已删除**；现在只有 `IUIThreadInspector<TPriorityCore>` 与共享基接口 `IUIThreadInspectorCore`。
- `ProtectedInvoke` **返回 `bool`**：该 action 是否真的入队（宿主的 dispatcher 已消失、或目标还没有队列时返回 `false`）——这是调用方区分「被丢弃」与「已入队」的唯一途径。
- `ProtectedInvokeAsync` 与 `ProtectedInvoke` 相同，但只在 action **真的执行完**后才完成；专供每次动画一次、必须发生在帧开始之前的调用（效果的 Awake），帧本身仍是 fire-and-forget。返回 `false` 表示从未入队，没有可等待的对象。
- 这些是骨架类——每个抽象成员（线程身份、编组、读编组、存活）都由各适配器的 `UIThreadInspector` 填入（见 [03_adapter-provided](../03_adapter-provided/index.md)）。

## 属性路径

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

    public object? GetValue(object? target);
    public bool SetValue(object target, object? value);
    public bool IsDescendantOf(TransitionProperty other);
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
| `IsDescendantOf` | 本条路径是否位于 `other` 之下。`StateCore` 的父子冲突检查用它（两个方向各判一次）。 |

**说明：** getter 与 setter 在首次使用时编译为单个委托（`CompileGetter` / `CompileSetter`），消除逐帧反射——`SamplerSet.Apply` / `ProtectedGetValue` 的热路径。`GetValue` 区分确实为 null 的中间对象（`null`，插值从 identity/默认开始）与类型不匹配的中间对象（`UnreadablePath`）。`SetValue` 在中间类型不匹配或为 null、或叶子无 setter 时返回 `false`（不抛 `TargetException`）；向引用类型叶子写 `null` 被允许。相等性按段链比较；`ToString()` 返回 `Path`。*验证依据：* `TransitionPropertyTests`。

## 路径校验与两个异常

两个异常都位于命名空间 `VeloxDev.TransitionSystem`（源码 `Src/Core/VeloxDev.Core/TransitionSystem/TransitionPath*Exception.cs`），在 transition 的**定义**或**执行**阶段同步抛出：

| 类型 | 抛出点 | 触发条件 |
|---|---|---|
| `TransitionPathConflictException : Exception` | `StateCore.SetValue(ITransitionProperty, …)`（即每条 value 路径的漏斗） | 同一 transition 内，新路径与已有路径构成父子关系。带 `Existing` / `Conflicting` 两个 `ITransitionProperty` 属性。 |
| `TransitionPathUnsampleableException : Exception` | `TransitionCore.RejectUnsampleablePaths`，由 `CoreValidate()` 在 `Execute` 中同步调用 | 声明的路径**永远无法动画**：叶子是引用类型且既无自定义采样器、也无已注册采样器。值类型豁免（结构体仍可逐成员装配）。 |

**边界（务必分清）：** 冲突检查只覆盖**单条** transition 的 value 路径——跨 transition 的冲突、以及经 `SetInterpolator` / `SetOptions` 注册的路径都**不检查**。这两个异常与 `TransitionProperty.UnreadablePath` 是两件事：后者指路径合法但对当前 target 的运行时类型无效（`GetValue` 返回哨兵），`Prepare` 每帧跳过它，不抛异常。*验证依据：* `TransitionPathConflictTests`、`TransitionPathValidationTests`。
