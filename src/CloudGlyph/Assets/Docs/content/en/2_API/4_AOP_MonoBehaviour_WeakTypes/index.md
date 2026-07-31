# AOP, MonoBehaviour & WeakTypes — API Reference

## `VeloxDev.AspectOriented` (AOP runtime, `#if NET`)

### `AspectOrientedAttribute`

```csharp
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
    AllowMultiple = false, Inherited = false)]
public class AspectOrientedAttribute : Attribute { }
```

Marks methods / properties / fields of a `partial` class for proxy interception. The generator exposes the marked members on the generated AOP interface.

### `IAspectOriented`

```csharp
public interface IAspectOriented { }
```

Marker interface implemented (transitively) by every generated AOP proxy; used as the generic constraint for `CreateProxy` / `SetProxy` / `Aop.GetTarget`.

### `ProxyMembers`

```csharp
public enum ProxyMembers { Getter, Setter, Method }
```

Selects which hook table (`GetterActions` / `SetterActions` / `MethodActions`) a `SetProxy` call writes to.

### `ProxyHandler`

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

Hook signature. `parameters` is the member's arguments; `previous` chains the return value from the previous stage. A non-null `coverage` handler's return value replaces the original member's result.

### `ProxyEx` (static)

| Member | Signature |
|---|---|
| `CreateProxy` | `public static T CreateProxy<T>(this T target) where T : IAspectOriented` |
| `SetProxy` | `public static void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : class, IAspectOriented` |

`CreateProxy` calls `DispatchProxy.Create<T, ProxyInstance>()`, stores `_target` / `_targetType`, and registers the proxy in `ProxyInstance.ProxyIDs` / `ProxyInstances` (source: `ProxyEx.cs` lines 16-25).

### `ProxyInstance` (`DispatchProxy`)

```csharp
public class ProxyInstance : DispatchProxy
{
    public static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; } = [];
    public static Dictionary<object, Guid> ProxyIDs { get; internal set; } = [];

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args);
}
```

The single `Invoke` dispatches on the method name: `get_*` → `GetterActions`, `set_*` → `SetterActions`, otherwise → `MethodActions`. For each matched triple it runs start → (coverage, or reflection fallback) → end (source: `ProxyInstance.cs` lines 23-53).

### `Aop` (static)

| Member | Signature |
|---|---|
| `Map` | `public static void Map(object proxy, object target)` |
| `GetTarget` | `public static TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class` |

Maintains a `ConditionalWeakTable<object, object>` proxy-to-target mapping (reverse lookup); `Map` is called by generated extensions.

### `AopCache` (static)

```csharp
public static TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory)
    where TInterface : class, IAspectOriented
    where TClass : class;
```

Generic per-pair `ConditionalWeakTable<TClass, TInterface>` — one weak table per `(TClass, TInterface)` via CLR generic specialization; the proxy dies with its target (source: `AopCache.cs` lines 14-32).

### Generated API (source generator)

- Interface: `VeloxDev.AopInterfaces.{ClassName}_{Namespace}_Aop : IAspectOriented` (member declarations for every `[AspectOriented]` member).
- Extension: `public static {I..._Aop} Aop(this T instance)` in namespace `VeloxDev.AspectOriented`; caches the proxy through `AopCache.Resolve` and registers it with `Aop.Map`.

## `VeloxDev.TimeLine` (MonoBehaviour manager)

### `MonoBehaviourAttribute`

```csharp
public sealed class MonoBehaviourAttribute(string channel = MonoBehaviourManager.DEFAULT_CHANNEL, int fps = -1) : Attribute
{
    public string Channel { get; }
    public int TargetFPS { get; set; }
}
```

`Channel` selects the named loop; `TargetFPS` (-1 = leave channel setting) is applied via `MonoBehaviourManager.SetTargetFPS` on registration (source: `MonoWriter.cs` lines 76-78).

### `MonoBehaviourManager` (static)

Constant: `public const string DEFAULT_CHANNEL = "default";`

Lifecycle (all take `string channel = DEFAULT_CHANNEL`):

| Member | Signature |
|---|---|
| `Start` | `public static void Start(string channel = DEFAULT_CHANNEL)` |
| `StopAsync` | `public static Task StopAsync(string channel = DEFAULT_CHANNEL)` |
| `Pause` | `public static void Pause(string channel = DEFAULT_CHANNEL)` |
| `Resume` | `public static void Resume(string channel = DEFAULT_CHANNEL)` |
| `RestartAsync` | `public static Task RestartAsync(string channel = DEFAULT_CHANNEL)` |
| `TogglePause` | `public static void TogglePause(string channel = DEFAULT_CHANNEL)` |

Registration / configuration:

| Member | Signature |
|---|---|
| `RegisterBehaviour` | `public static void RegisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)` |
| `UnregisterBehaviour` | `public static void UnregisterBehaviour(IMonoBehaviour behavior, string channel = DEFAULT_CHANNEL)` |
| `SetTargetFPS` | `public static void SetTargetFPS(int fps, string channel = DEFAULT_CHANNEL)` (clamp 1..1000) |
| `SetFixedUpdateInterval` | `public static void SetFixedUpdateInterval(int intervalMs, string channel = DEFAULT_CHANNEL)` (clamp 1..1000) |
| `SetTimeScale` | `public static void SetTimeScale(float timeScale, string channel = DEFAULT_CHANNEL)` (clamp 0..10) |
| `ExecuteOnMainThread` | `public static void ExecuteOnMainThread(Action action, string channel = DEFAULT_CHANNEL)` |
| `SetUseAsyncLoop` | `public static void SetUseAsyncLoop(bool useAsyncLoop, string channel = DEFAULT_CHANNEL)` — throws `InvalidOperationException` if running |
| `ClearUseAsyncLoopOverride` | `public static void ClearUseAsyncLoopOverride(string channel = DEFAULT_CHANNEL)` — throws `InvalidOperationException` if running |

Status queries (all take `string channel = DEFAULT_CHANNEL`):

| Member | Returns |
|---|---|
| `IsRunning` / `IsPaused` | `bool` |
| `CurrentFPS` / `TargetFPS` | `int` |
| `TotalTime` | `TimeSpan` |
| `TotalTimeMs` / `TotalFrames` | `long` |
| `ActiveBehaviorCount` | `int` |
| `TimeScale` | `float` |
| `SystemStatus` | `string` — `"Stopped"` / `"Paused"` / `"Running"` |
| `IsUpdateThreadAlive` / `IsFixedUpdateThreadAlive` | `bool` (with 2s inactivity timeout) |

Events & properties:

```csharp
public static bool UseAsyncLoop { get; set; }               // auto-enabled on WASM / iOS
public static IEnumerable<string> ChannelNames { get; }     // created channels
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStarted;
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelPaused;
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelResumed;
public static event EventHandler<MonoBehaviourChannelEventArgs>? OnChannelStopped;
```

### `TimeLineEventArgs` / `FrameEventArgs`

```csharp
public abstract class TimeLineEventArgs
{
    public virtual bool Handled { get; set; }   // True = stop the timeline
}

public class FrameEventArgs : TimeLineEventArgs
{
    public TimeSpan DeltaTime { get; internal set; }
    public TimeSpan TotalTime { get; internal set; }
    public int CurrentFPS { get; internal set; }
    public int TargetFPS { get; internal set; }
}
```

Setting `Handled = true` inside `Update` / `LateUpdate` / `FixedUpdate` short-circuits the remaining behaviors for that frame.

### `ThreadSafeFrameEventArgs`

```csharp
public class ThreadSafeFrameEventArgs : FrameEventArgs
{
    public new bool Handled { get; set; }   // lock-protected, safe across the update + fixed threads
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

## `VeloxDev.MonoBehaviour` (`IMonoBehaviour`)

```csharp
public interface IMonoBehaviour
{
    void InitializeMonoBehaviour();     // calls RegisterBehaviour(this, channel)
    void CloseMonoBehaviour();          // calls UnregisterBehaviour(this, channel)
    void InvokeAwake();
    void InvokeStart();
    void InvokeUpdate(FrameEventArgs e);
    void InvokeLateUpdate(FrameEventArgs e);
    void InvokeFixedUpdate(FrameEventArgs e);
}
```

`Invoke*` methods are the bridge the manager calls; they forward to the user-written `partial void Awake() / Start() / Update / LateUpdate / FixedUpdate` hooks generated by `MonoWriter.cs` (lines 91-120).

## `VeloxDev.WeakTypes`

### `WeakDelegate<TDelegate>` where `TDelegate : Delegate`

| Member | Signature |
|---|---|
| `AddHandler` | `public void AddHandler(TDelegate? handler, bool CanUpdateCache = true)` |
| `RemoveHandler` | `public void RemoveHandler(TDelegate? handler, bool CanUpdateCache = true)` |
| `GetInvocationList` | `public TDelegate? GetInvocationList()` — prunes collected handlers, returns cached combined delegate |
| `Invoke` | `public void Invoke(object?[] objects)` — `DynamicInvoke` on the cached combined delegate |
| `Clone` | `public WeakDelegate<TDelegate> Clone()` — rebuilds from live handlers |

### `WeakQueue<T>` where `T : class`, `IEnumerable<T>`

| Member | Signature |
|---|---|
| `Count` | `public int Count { get; }` — prunes first |
| `IsEmpty` | `public bool IsEmpty { get; }` |
| `Enqueue` | `public void Enqueue(T item)` — throws `ArgumentNullException` on `null` |
| `EnqueueRange` | `public int EnqueueRange(IEnumerable<T> items)` |
| `TryDequeue` | `public bool TryDequeue(out T? item)` — skips collected refs |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` | `public void TrimExcess()` |
| `Clear` | `public void Clear()` |

### `WeakStack<T>` where `T : class`, `IEnumerable<T>`

| Member | Signature |
|---|---|
| `Count` / `IsEmpty` | `public int Count { get; }` / `public bool IsEmpty { get; }` |
| `Push` | `public void Push(T item)` — throws `ArgumentNullException` on `null` |
| `PushRange` | `public int PushRange(IEnumerable<T> items)` — preserves input order on top |
| `TryPop` | `public bool TryPop(out T? item)` — skips collected refs |
| `TryPeek` | `public bool TryPeek(out T? item)` |
| `TrimExcess` / `Clear` | `public void TrimExcess()` / `public void Clear()` |

### `WeakCache<TTargetKey, TCacheKey>` where `TTargetKey : class`, `TCacheKey : class`

| Member | Signature |
|---|---|
| `AddOrUpdate` | `public void AddOrUpdate(TTargetKey target, TCacheKey cache)` |
| `TryGetCache` | `public bool TryGetCache(TTargetKey target, out TCacheKey? cache)` |
| `Remove` | `public void Remove(TTargetKey target)` |
| `ForeachCache` | `public void ForeachCache(Action<TTargetKey, TCacheKey> action)` — prunes collected targets first |

Backed by a `ConditionalWeakTable<TTargetKey, TCacheKey>` plus a `List<WeakReference<TTargetKey>>` sweep list; cleanup is triggered when an insert counter crosses an adaptive `_perceptionThreshold` (source: `WeakCache.cs` lines 12, 44-62).
