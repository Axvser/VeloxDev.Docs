# 过渡动画 — 契约：宿主与线程

引擎向宿主索取的线程与存活面。它位于 `VeloxDev.Core` 的两个子系统而不是 `VeloxDev.TransitionSystem` —— `VeloxDev.Threading`（`Src/Core/VeloxDev.Core/Threading/*.cs`）与 `VeloxDev.Lifetime`（`Src/Core/VeloxDev.Core/Lifetime/IApplicationState.cs`）—— 这样宿主接缝就不归动画系统所有。把两者绑在一起的那个组合声明**在** `VeloxDev.TransitionSystem` 里：

### 接口：`ITransitionHost<TPriorityCore>`

```csharp
public interface ITransitionHost<TPriorityCore> : IThreadDispatcher<TPriorityCore>, IApplicationState
{
}
```

**说明：**
- 一个**组合，不是新契约** —— 不新增任何成员，存在的意义是让适配器只声明一个接口，而底下两个子系统仍可各自替换。它是引擎贯穿一切触及目标的类型的形参：`SamplerSet<TPriorityCore>` 以它构造，`InterpolatorCore.Prepare<TPriorityCore>` 接收它，`SamplerSet.Apply` 与调度器的 `Awake` 派发都经它。
- 适配器提供一个具体实现：就是各适配器以 `UIThreadInspector` 之名单出的那个类（见 [adapter-provided/ui-inspector](../../03_适配器提供/02_UI线程检查器/index.md)）。
- *核验：* 各适配器的 `PlatformAdapters/UIThreadInspector.cs`；`TransitionRunThreadAffinityTests`；`AUTO TEST` 套件用例 `ObservationSurface_IsReachableAndTicking`。

### 接口：`IThreadAffinity`（命名空间 `VeloxDev.Threading`）

```csharp
public interface IThreadAffinity
{
    ThreadRef ThreadFor(object target);
    bool IsCurrent(object target);
}
```

| 成员 | 说明 |
|---|---|
| `ThreadFor(target)` | `target` 所属线程，以 `ThreadRef` 表示。**绝不为调用方现造一个** —— `Dispatcher.CurrentDispatcher` 及其同类会为调用线程造出一个 dispatcher，把消费者钉在一个没人驱动的消息泵上，且无从报告。 |
| `IsCurrent(target)` | 调用线程是否拥有 `target`。 |

**说明：** 每个成员都刻意相对于目标：把「我是不是 UI 线程」和「这个目标属于哪个线程」分开问，在宿主只有一个 UI 线程时两者一致，而恰好在其不然时分歧（Blazor 回路的 renderer 属于回路而不属于进程）。**这里任何成员都不得抛异常。** 它们从每帧跑一次的写路径被触达，那里异常与「工作失败」无法区分；拒绝经返回值报告。

### 接口：`IThreadDispatcher<TPriorityCore> : IThreadAffinity`（命名空间 `VeloxDev.Threading`）

```csharp
public interface IThreadDispatcher<TPriorityCore> : IThreadAffinity
{
    bool Post(object target, Action action, TPriorityCore priority);
    bool Post(object target, ThreadRef thread, Action action, TPriorityCore priority);
    Task<bool> PostAsync(object target, Action action, TPriorityCore priority);
    T Run<T>(object target, Func<T> body);
}
```

| 成员 | 说明 |
|---|---|
| `Post(target, action, priority)` | 把 `action` 排到 `target` 的线程上。不得阻塞。返回值是区分「动作被丢弃」与「动作已排队」的**唯一**依据；对永不运行的工作乐观地返回 `true`，会吊死等它的人。 |
| `Post(target, thread, action, priority)` | 把 `action` 交给调用方**已经解析好**的线程。拥有自己线程的一趟用这个：每帧重新 `ThreadFor` 对一个「答案取决于调用线程」的宿主会给出错误答案 —— 写路径跑在采样循环的线程上，而 Blazor 回路的 renderer 从那里无法被命名。 |
| `PostAsync(target, action, priority)` | 同 `Post`，但在 `action` 真正运行之后才完成。用于每次动画中必须在帧开始之前发生的那一次调用 —— effect 的 `Awake`。 |
| `Run<T>(target, body)` | 在目标线程上运行 `body` 并返回其结果；可以阻塞，且只会在本 dispatcher 确实排队了的工作上阻塞。排不进去时返回 `default` —— `T` 无约束，所以值类型的失败答案就是它的零值。 |

**说明：** `Run<T>` 是读路径 —— `InterpolatorCore.Prepare` 经它读取每个已声明属性的当前值，于是读取在所属线程上发生，而调用方无需自己编组。

### 结构体：`ThreadRef`（命名空间 `VeloxDev.Threading`）

一个线程，作为上层无法命名的句柄。

```csharp
public readonly struct ThreadRef : IEquatable<ThreadRef>
{
    public static ThreadRef None { get; }
    public bool IsNone { get; }
    public static ThreadRef From<T>(T? handle) where T : class;
    public bool TryGet<T>(out T handle) where T : class;
    // IEquatable<ThreadRef>：Equals / GetHashCode，以及 == 与 !=
}
```

**说明：** 包装宿主用来标识线程的任何东西 —— 一个 `Dispatcher`、`DispatcherQueue`、`IDispatcher`、`SynchronizationContext`。「没有线程拥有它」变成一个**有名字**的答案（`None`），而不是每个调用方都要强制转换并祈祷的 `null`。`TryGet<T>` 的 out 形参声明为非可空，好让检查返回值的调用方能直接使用它 —— 它在返回 `false` 时是 `null`，这正是那个检查不可省的原因。相等性是被包装句柄的引用相等。

### 结构体：`NonPriority`（命名空间 `VeloxDev.Threading`）

```csharp
public readonly struct NonPriority { }
```

**说明：** 调度器不携带优先级的宿主的优先级类型。它填的是一个类型形参，而不是一个被传递的值：没有实例要传、类型实参不分配，且 `default(NonPriority)` 是真实的值，因此能原样穿过既有的 `is TPriorityCore` 检查。MAUI、WinForms、Razor 三个适配器用它。

### 接口：`IApplicationState`（命名空间 `VeloxDev.Lifetime`）

```csharp
public interface IApplicationState
{
    bool IsAlive { get; }
}
```

**说明：** 宿主一旦开始关闭即为 `false`；**是提示，绝不是抛异常的理由**。`SamplerSet.CanSetValue()` 返回它，`Apply` 在它为 false 时提前返回 —— 这是「过期帧」守卫，阻止已排队的帧在宿主消失后覆盖一次重置。

### 类：`ApplicationState : IApplicationState`（命名空间 `VeloxDev.Lifetime`）

```csharp
public sealed class ApplicationState : IApplicationState
{
    public bool IsAlive { get; }
    public void SetAlive(bool alive);
}
```

**说明：** 能观察到自身退出的宿主写入的存活标志。`SetAlive` 刻意**不是单程**的：一个从一个信号报告死亡、随后发现信号是误报的宿主 —— WinUI 在一次入队被拒时会清掉它的标志 —— 必须能收回，否则每个消费者都会在进程余下的生命里保持死亡，且什么都不记录。

### 类：`ThreadDispatcherBase<TPriorityCore> : IThreadDispatcher<TPriorityCore>`（命名空间 `VeloxDev.Threading`）

```csharp
public abstract class ThreadDispatcherBase<TPriorityCore> : IThreadDispatcher<TPriorityCore>
{
    public abstract ThreadRef ThreadFor(object target);
    public virtual bool IsCurrent(object target);
    protected virtual bool IsCurrentFor(object target, ThreadRef thread);
    protected abstract bool IsCurrentThread(ThreadRef thread);
    protected abstract bool PostCore(object target, ThreadRef thread, Action action, TPriorityCore priority);
    protected virtual TPriorityCore InternalPriority { get; }
    public bool Post(object target, Action action, TPriorityCore priority);
    public bool Post(object target, ThreadRef thread, Action action, TPriorityCore priority);
    public async Task<bool> PostAsync(object target, Action action, TPriorityCore priority);
    public virtual T Run<T>(object target, Func<T> body);
}
```

**说明：**
- `IThreadDispatcher<TPriorityCore>` 的派生面，只实现一次，于是没有宿主能与别的宿主派生出不同行为。宿主提供 `ThreadFor`、`IsCurrentThread`、`PostCore`，其余都在这里。`IsCurrentFor(target, thread)` 是写路径用的形式，于是线程查找只做一次 —— 能对某个目标给出更精确答案的宿主重写它而不是 `IsCurrent`。
- `PostCore` 不得阻塞并返回动作是否被接受；需要的是**目标**而不是线程的宿主（WinForms 经它拿到的 `Control` 投递）可以自由忽略 `thread`。`InternalPriority` 有默认值而非必须重写，因为对没有优先级的宿主 `default(NonPriority)` 就是全部答案；有优先级的宿主**必须**重写，因为 `default(DispatcherPriority)` 是 `Inactive`，会把一次阻塞读取排到所有普通消息之后。
- *核验：* `ThreadDispatcherBase` 是每个适配器宿主的基类；`TransitionRunThreadAffinityTests`、`TransitionSchedulerAwakeTests`。

### 类：`TransitionHostBase<TPriorityCore> : ThreadDispatcherBase<TPriorityCore>, ITransitionHost<TPriorityCore>`（命名空间 `VeloxDev.TransitionSystem.Abstractions`）

```csharp
public abstract class TransitionHostBase<TPriorityCore> : ThreadDispatcherBase<TPriorityCore>, ITransitionHost<TPriorityCore>
{
    protected ApplicationState Lifetime { get; }
    public virtual bool IsAlive { get; }
}
```

**说明：** 适配器宿主派生的基类 —— dispatcher 的派生面外加一个存活标志。`IsAlive` 默认取自受保护的 `Lifetime`（`ApplicationState`）；只能**问**自己是否活着的宿主（MAUI 数 `Application.Current.Windows`，WinForms 听 `ApplicationExit`）改为重写 `IsAlive`，并在能报的地方写入 `Lifetime`。*核验：* 各适配器的 `UIThreadInspector`。
