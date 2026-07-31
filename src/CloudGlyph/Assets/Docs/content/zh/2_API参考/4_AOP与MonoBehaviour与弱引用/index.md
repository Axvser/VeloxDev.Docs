# AOP、MonoBehaviour 与弱引用 — API 参考

## `VeloxDev.AspectOriented`（AOP 运行时，`#if NET`）

### `AspectOrientedAttribute`

```csharp
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
    AllowMultiple = false, Inherited = false)]
public class AspectOrientedAttribute : Attribute { }
```

标记 `partial` 类中需要被代理拦截的方法 / 属性 / 字段。生成器会把被标记成员暴露到生成的 AOP 接口上。

### `IAspectOriented`

```csharp
public interface IAspectOriented { }
```

标记接口；每个生成的 AOP 代理（传递性地）实现它，用作 `CreateProxy` / `SetProxy` / `Aop.GetTarget` 的泛型约束。

### `ProxyMembers`

```csharp
public enum ProxyMembers { Getter, Setter, Method }
```

选择 `SetProxy` 写入哪张钩子表（`GetterActions` / `SetterActions` / `MethodActions`）。

### `ProxyHandler`

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

钩子签名。`parameters` 是成员的实参；`previous` 串联上一阶段的返回值。`coverage` 处理器非空时，其返回值替换原成员的返回结果。

### `ProxyEx`（静态类）

| 成员 | 签名 |
|---|---|
| `CreateProxy` | `public static T CreateProxy<T>(this T target) where T : IAspectOriented` |
| `SetProxy` | `public static void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : class, IAspectOriented` |

`CreateProxy` 调用 `DispatchProxy.Create<T, ProxyInstance>()`，保存 `_target` / `_targetType`，并把代理登记到 `ProxyInstance.ProxyIDs` / `ProxyInstances`（出处：`ProxyEx.cs` 第 16-25 行）。

### `ProxyInstance`（继承 `DispatchProxy`）

```csharp
public class ProxyInstance : DispatchProxy
{
    public static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; } = [];
    public static Dictionary<object, Guid> ProxyIDs { get; internal set; } = [];

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args);
}
```

唯一拦截点 `Invoke` 按方法名分发：`get_*` → `GetterActions`，`set_*` → `SetterActions`，其余 → `MethodActions`。每个匹配的三元组执行 start →（coverage，或反射回退）→ end（出处：`ProxyInstance.cs` 第 23-53 行）。

### `Aop`（静态类）

| 成员 | 签名 |
|---|---|
| `Map` | `public static void Map(object proxy, object target)` |
| `GetTarget` | `public static TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class` |

维护一张 `ConditionalWeakTable<object, object>` 的代理→目标映射（逆向查找）；`Map` 由生成的扩展方法调用。

### `AopCache`（静态类）

```csharp
public static TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory)
    where TInterface : class, IAspectOriented
    where TClass : class;
```

利用 CLR 泛型特化，为每一对 `(TClass, TInterface)` 生成独立的 `ConditionalWeakTable<TClass, TInterface>` 弱表；代理随目标一起被回收（出处：`AopCache.cs` 第 14-32 行）。

### 生成器产物（源生成器）

- 接口：`VeloxDev.AopInterfaces.{ClassName}_{Namespace}_Aop : IAspectOriented`（为每个 `[AspectOriented]` 成员生成声明）。
- 扩展：`public static {I..._Aop} Aop(this T instance)`（命名空间 `VeloxDev.AspectOriented`）；通过 `AopCache.Resolve` 缓存代理并用 `Aop.Map` 登记。

## `VeloxDev.TimeLine`（MonoBehaviour 管理器）

### `MonoBehaviourAttribute`

```csharp
public sealed class MonoBehaviourAttribute(string channel = MonoBehaviourManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
{
    public string Channel { get; }
    public int TargetFPS { get; set; }
}
```

`Channel` 选择命名循环；`TargetFPS`（-1 = 沿用通道设置）在注册时通过 `MonoBehaviourManager.SetTargetFPS` 应用（出处：`MonoWriter.cs` 第 76-78 行）。

### `MonoBehaviourManager`（静态类）

常量：`public const string DEFAULT_CHANNEL = "default";`

生命周期（均带 `string channel = DEFAULT_CHANNEL`）：

| 成员 | 签名 |
|---|---|
| `Start` | `public static void Start(string channel = DEFAULT_CHANNEL)` |
| `StopAsync` | `public static Task StopAsync(string channel = DEFAULT_CHANNEL)` |
| `Pause` | `public static void Pause(string channel = DEFAULT_CHANNEL)` |
| `Resume` | `public static void Resume(string channel = DEFAULT_CHANNEL)` |
| `RestartAsync` | `public static Task RestartAsync(string channel = DEFAULT_CHANNEL)` |
| `TogglePause` | `public static void TogglePause(string channel = DEFAULT_CHANNEL)` |

注册 / 配置：

| 成员 | 签名 |
|---|---|
| `RegisterBehaviour` | `public static void RegisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)` |
| `UnregisterBehaviour` | `public static void UnregisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)` |
| `SetTargetFPS` | `public static void SetTargetFPS(int fps, string channel = DEFAULT_CHANNEL)`（钳位 1..1000） |
| `SetFixedUpdateInterval` | `public static void SetFixedUpdateInterval(int intervalMs, string channel = DEFAULT_CHANNEL)`（钳位 1..1000） |
| `SetTimeScale` | `public static void SetTimeScale(float timeScale, string channel = DEFAULT_CHANNEL)`（钳位 0..10） |
| `ExecuteOnMainThread` | `public static void ExecuteOnMainThread(Action action, string channel = DEFAULT_CHANNEL)` |
| `SetUseAsyncLoop` | `public static void SetUseAsyncLoop(bool useAsyncLoop, string channel = DEFAULT_CHANNEL)` — 运行中调用抛 `InvalidOperationException` |
| `ClearUseAsyncLoopOverride` | `public static void ClearUseAsyncLoopOverride(string channel = DEFAULT_CHANNEL)` — 运行中调用抛 `InvalidOperationException` |

状态查询（均带 `string channel = DEFAULT_CHANNEL`）：

| 成员 | 返回 |
|---|---|
| `IsRunning` / `IsPaused` | `bool` |
| `CurrentFPS` / `TargetFPS` | `int` |
| `TotalTime` | `TimeSpan` |
| `TotalTimeMs` / `TotalFrames` | `long` |
| `ActiveBehaviorCount` | `int` |
| `TimeScale` | `float` |
| `SystemStatus` | `string` — `"Stopped"` / `"Paused"` / `"Running"` |
| `IsUpdateThreadAlive` / `IsFixedUpdateThreadAlive` | `bool`（带 2 秒无活动超时） |

事件与属性：

```csharp
public static bool UseAsyncLoop { get; set; }               // WASM / iOS 上自动启用
public static IEnumerable<string> ChannelNames { get; }     // 已创建的通道
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStarted;
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelPaused;
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelResumed;
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStopped;
```

### `TimeLineEventArgs` / `FrameEventArgs`

```csharp
public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; }   // True = 终止时间线
}

public class FrameEventArgs : TimeLineEventArgs
{
    public TimeSpan DeltaTime { get; internal set; }
    public TimeSpan TotalTime { get; internal set; }
    public int CurrentFPS { get; internal set; }
    public int TargetFPS { get; internal set; }
}
```

在 `Update` / `LateUpdate` / `FixedUpdate` 中把 `Handled` 置 `true` 会短路该帧剩余的行为调用。

### `ThreadSafeFrameEventArgs`

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    public new bool Handled { get; set; }   // 加锁保护，可在 update 与 fixed 线程间安全读写
}
```

### `MonoBehaviourChannelEventArgs`

```csharp
public sealed class MonoBehaviourChannelEventArgs(string channelName) : EventArgs
{
    public string ChannelName { get; }
}
```

### `TransitionEventArgs`

```csharp
public sealed class TransitionEventArgs : TimeLineEventArgs { }
```

## `VeloxDev.MonoBehaviour`（`IMonoBehaviour`）

```csharp
public interface IMonoBehaviour
{
    void InitializeMonoBehaviour();     // 调用 RegisterBehaviour(this, channel)
    void CloseMonoBehaviour();          // 调用 UnregisterBehaviour(this, channel)
    void InvokeAwake();
    void InvokeStart();
    void InvokeUpdate(FrameEventArgs e);
    void InvokeLateUpdate(FrameEventArgs e);
    void InvokeFixedUpdate(FrameEventArgs e);
}
```

`Invoke*` 方法是管理器调用的桥接方法，转发到由 `MonoWriter.cs`（第 91-120 行）生成的用户 partial 钩子 `Awake() / Start() / Update / LateUpdate / FixedUpdate`。

## `VeloxDev.WeakTypes`

### `WeakDelegate<TDelegate>`（`TDelegate : Delegate`）

| 成员 | 签名 |
|---|---|
| `AddHandler` | `public void AddHandler(TDelegate? handler, bool CanUpdateCache = true)` |
| `RemoveHandler` | `public void RemoveHandler(TDelegate? handler, bool CanUpdateCache = true)` |
| `GetInvocationList` | `public TDelegate? GetInvocationList()` — 先清扫已回收处理器，返回缓存后的组合委托 |
| `Invoke` | `public void Invoke(object?[] objects)` — 对缓存组合委托执行 `DynamicInvoke` |
| `Clone` | `public WeakDelegate<TDelegate> Clone()` — 从存活处理器重建 |

### `WeakQueue<T>`（`T : class`，`IEnumerable<T>`）

| 成员 | 签名 |
|---|---|
| `Count` | `public int Count { get; }` — 先剪除死引用 |
| `IsEmpty` | `public bool IsEmpty { get; }` |
| `Enqueue` | `public void Enqueue(T item)` — `null` 抛 `ArgumentNullException` |
| `EnqueueRange` | `public int EnqueueRange(IEnumerable<T> items)` |
| `TryDequeue` | `public bool TryDequeue(out T? item)` — 跳过已回收引用 |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` | `public void TrimExcess()` |
| `Clear` | `public void Clear()` |

### `WeakStack<T>`（`T : class`，`IEnumerable<T>`）

| 成员 | 签名 |
|---|---|
| `Count` / `IsEmpty` | `public int Count { get; }` / `public bool IsEmpty { get; }` |
| `Push` | `public void Push(T item)` — `null` 抛 `ArgumentNullException` |
| `PushRange` | `public int PushRange(IEnumerable<T> items)` — 保持输入顺序在栈顶 |
| `TryPop` | `public bool TryPop(out T? item)` — 跳过已回收引用 |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` / `Clear` | `public void TrimExcess()` / `public void Clear()` |

### `WeakCache<TTargetKey, TCacheKey>`（`TTargetKey : class`，`TCacheKey : class`）

| 成员 | 签名 |
|---|---|
| `AddOrUpdate` | `public void AddOrUpdate(TTargetKey target, TCacheKey cache)` |
| `TryGetCache` | `public bool TryGetCache(TTargetKey target, out TCacheKey? cache)` |
| `Remove` | `public void Remove(TTargetKey target)` |
| `ForeachCache` | `public void ForeachCache(Action<TTargetKey, TCacheKey> action)` — 先清扫已回收目标 |

由 `ConditionalWeakTable<TTargetKey, TCacheKey>` 加 `List<WeakReference<TTargetKey>>` 清扫列表支撑；当插入计数器超过自适应 `_perceptionThreshold` 时触发清理（出处：`WeakCache.cs` 第 12、44-62 行）。
