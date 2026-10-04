# Transition — Contracts: Host & Threading

The thread and liveness surface the engine asks of a host. It lives in two subsystems of `VeloxDev.Core` rather than in `VeloxDev.TransitionSystem` — `VeloxDev.Threading` (`Src/Core/VeloxDev.Core/Threading/*.cs`) and `VeloxDev.Lifetime` (`Src/Core/VeloxDev.Core/Lifetime/IApplicationState.cs`) — so that a host seam is not owned by the animation system. The composition that ties them together is declared **in** `VeloxDev.TransitionSystem`:

### Interface: `ITransitionHost<TPriorityCore>`

```csharp
public interface ITransitionHost<TPriorityCore> : IThreadDispatcher<TPriorityCore>, IApplicationState
{
}
```

**Notes:**
- A **composition, not a new contract** — it adds no member, and exists so an adapter declares one interface while the two subsystems underneath stay independently replaceable. It is the type parameter the engine threads through everything that touches a target: `SamplerSet<TPriorityCore>` is constructed with it, `InterpolatorCore.Prepare<TPriorityCore>` takes it, and both `SamplerSet.Apply` and the scheduler's `Awake` dispatch go through it.
- An adapter supplies one concrete implementation: it is the class each adapter ships as `UIThreadInspector` (see [adapter-provided/ui-inspector](../../03_adapter-provided/02_ui-inspector/index.md)).
- *Verified by:* every adapter's `PlatformAdapters/UIThreadInspector.cs`; `TransitionRunThreadAffinityTests`; the `AUTO TEST` suite case `ObservationSurface_IsReachableAndTicking`.

### Interface: `IThreadAffinity` (namespace `VeloxDev.Threading`)

```csharp
public interface IThreadAffinity
{
    ThreadRef ThreadFor(object target);
    bool IsCurrent(object target);
}
```

| Member | Description |
|---|---|
| `ThreadFor(target)` | Which thread owns `target`, as a `ThreadRef`. **Never mint one for the caller** — `Dispatcher.CurrentDispatcher` and its equivalents manufacture a dispatcher for the calling thread, pinning the consumer to a message pump nobody drives, with nothing to report it. |
| `IsCurrent(target)` | Whether the calling thread owns `target`. |

**Notes:** every member is target-relative, deliberately: asking "am I the UI thread" globally and "which thread owns this target" separately agrees whenever a host has one UI thread, and disagrees exactly when it does not (a Blazor circuit's renderer belongs to the circuit, not the process). **Nothing here may throw.** These members are reached from a write path that runs once per frame, where an exception is indistinguishable from the work having failed; a refusal is reported through the return value.

### Interface: `IThreadDispatcher<TPriorityCore> : IThreadAffinity` (namespace `VeloxDev.Threading`)

```csharp
public interface IThreadDispatcher<TPriorityCore> : IThreadAffinity
{
    bool Post(object target, Action action, TPriorityCore priority);
    bool Post(object target, ThreadRef thread, Action action, TPriorityCore priority);
    Task<bool> PostAsync(object target, Action action, TPriorityCore priority);
    T Run<T>(object target, Func<T> body);
}
```

| Member | Description |
|---|---|
| `Post(target, action, priority)` | Queues `action` on `target`'s thread. Must not block. The return value is the **only** way to tell a dropped action from a queued one; an optimistic `true` for work that never runs hangs whoever waits on it. |
| `Post(target, thread, action, priority)` | Hands `action` to a thread the caller already resolved. What a run that has a thread of its own uses: asking `ThreadFor` again per frame gives the wrong answer for a host whose answer depends on the calling thread — the write path runs on the sampling loop's thread, and a Blazor circuit's renderer cannot be named from there. |
| `PostAsync(target, action, priority)` | Same as `Post`, but completes once `action` has actually run. Used for the one call per animation that must happen before the frames start — the effect's `Awake`. |
| `Run<T>(target, body)` | Runs `body` on the target's thread and returns its result; may block, and only ever on work this dispatcher actually queued. Returns `default` when it could not queue it — `T` is unconstrained, so a value type's failure answer is its zero. |

**Notes:** `Run<T>` is the read path — `InterpolatorCore.Prepare` reads each declared property's current value through it, so the read happens on the owning thread without the caller having to marshal.

### Struct: `ThreadRef` (namespace `VeloxDev.Threading`)

A thread, as an opaque handle the layer above cannot name.

```csharp
public readonly struct ThreadRef : IEquatable<ThreadRef>
{
    public static ThreadRef None { get; }
    public bool IsNone { get; }
    public static ThreadRef From<T>(T? handle) where T : class;
    public bool TryGet<T>(out T handle) where T : class;
    // IEquatable<ThreadRef>: Equals / GetHashCode, plus == and !=
}
```

**Notes:** wraps whatever the host uses to identify a thread — a `Dispatcher`, a `DispatcherQueue`, an `IDispatcher`, a `SynchronizationContext`. "No thread owns this" becomes an answer with a name (`None`) instead of a `null` every caller has to cast and hope about. `TryGet<T>`'s out parameter is declared non-nullable so a caller that checks the return value can use it directly — it is null whenever the call returns `false`, which is why the check is load-bearing. Equality is reference equality on the wrapped handle.

### Struct: `NonPriority` (namespace `VeloxDev.Threading`)

```csharp
public readonly struct NonPriority { }
```

**Notes:** the priority type of a host whose dispatcher carries none. It fills a type parameter rather than being a value that is passed: no instance to hand around, no allocation for the type argument, and `default(NonPriority)` is a real value, so it flows through the existing `is TPriorityCore` checks unchanged. Adapters MAUI, WinForms and Razor use it.

### Interface: `IApplicationState` (namespace `VeloxDev.Lifetime`)

```csharp
public interface IApplicationState
{
    bool IsAlive { get; }
}
```

**Notes:** `false` once the host has begun shutting down; **a hint, never a reason to throw**. `SamplerSet.CanSetValue()` returns it, and `Apply` returns early when it is false — this is the "stale frame" guard that stops queued frames from overwriting a reset after the host is gone.

### Class: `ApplicationState : IApplicationState` (namespace `VeloxDev.Lifetime`)

```csharp
public sealed class ApplicationState : IApplicationState
{
    public bool IsAlive { get; }
    public void SetAlive(bool alive);
}
```

**Notes:** the liveness flag a host reports into, for the hosts that can observe their own exit. `SetAlive` is deliberately **not one-way**: a host that reports death from one signal and later finds the signal was spurious — WinUI clears its flag when a single enqueue is refused — has to be able to take it back, or every consumer stays dead for the rest of the process with nothing logged.

### Class: `ThreadDispatcherBase<TPriorityCore> : IThreadDispatcher<TPriorityCore>` (namespace `VeloxDev.Threading`)

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

**Notes:**
- The derived surface of `IThreadDispatcher<TPriorityCore>`, implemented once so no host can derive it differently from another. A host supplies `ThreadFor`, `IsCurrentThread` and `PostCore`; everything else lives here. `IsCurrentFor(target, thread)` is the form the write path uses, so the thread lookup happens once — a host that can answer more precisely for a target overrides it rather than `IsCurrent`.
- `PostCore` must not block and returns whether the action was accepted; a host that needs the *target* rather than the thread (WinForms posts through the `Control` it was given) is free to ignore `thread`. `InternalPriority` is defaulted rather than required because `default(NonPriority)` is the whole story for a host that has no priority; a host that has one **must** override it, since `default(DispatcherPriority)` is `Inactive`, which would park a blocking read behind every normal message.
- *Verified by:* `ThreadDispatcherBase` is the base of every adapter host; `TransitionRunThreadAffinityTests`, `TransitionSchedulerAwakeTests`.

### Class: `TransitionHostBase<TPriorityCore> : ThreadDispatcherBase<TPriorityCore>, ITransitionHost<TPriorityCore>` (namespace `VeloxDev.TransitionSystem.Abstractions`)

```csharp
public abstract class TransitionHostBase<TPriorityCore> : ThreadDispatcherBase<TPriorityCore>, ITransitionHost<TPriorityCore>
{
    protected ApplicationState Lifetime { get; }
    public virtual bool IsAlive { get; }
}
```

**Notes:** the base an adapter's host derives from — the dispatcher's derived surface plus a liveness flag. `IsAlive` comes from the protected `Lifetime` (`ApplicationState`) by default; a host that can only *ask* whether it is alive (MAUI counts `Application.Current.Windows`, WinForms listens for `ApplicationExit`) overrides `IsAlive` instead and reports into `Lifetime` where it can. *Verified by:* every adapter's `UIThreadInspector`.
