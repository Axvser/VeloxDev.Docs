# Scheduling and Events

The scheduler owns the loop; the interpreter produces frames; the host supplies thread affinity and liveness. Namespace for the runtime classes is `VeloxDev.TransitionSystem.Abstractions`; the three scheduler/host/interpreter interfaces are in `VeloxDev.TransitionSystem`.

## VeloxDev.TransitionSystem

### Interface: ITransitionSchedulerCore

**Signature:** `public interface ITransitionSchedulerCore`

| Member | Signature | Description |
|---|---|---|
| `Execute` | `Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | Runs `producer` against `state`. |
| `Exit` | `void Exit()` | Stops the scheduler. |

### Interface: ITransitionScheduler

An empty refinement of `ITransitionSchedulerCore`, used where the priority type is erased.

**Signature:** `public interface ITransitionScheduler : ITransitionSchedulerCore`

### Interface: ITransitionScheduler<TPriorityCore>

**Signature:** `public interface ITransitionScheduler<TPriorityCore> : ITransitionSchedulerCore`

| Member | Signature |
|---|---|
| `Execute` | `Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` |

### Interface: ITransitionHost<TPriorityCore>

A composition of `IThreadDispatcher<TPriorityCore>` and `IApplicationState`; it adds no members itself.

**Signature:** `public interface ITransitionHost<TPriorityCore> : IThreadDispatcher<TPriorityCore>, IApplicationState`

### Interface: ITransitionInterpreter<TPriorityCore>

**Signature:** `public interface ITransitionInterpreter<TPriorityCore> : IDisposable`

| Member | Type/Signature | Description |
|---|---|---|
| `Args` | `TransitionEventArgs { get; set; }` | The args of the current execution. |
| `Execute` | `Task Execute(object target, SamplerSet<TPriorityCore> samplerSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts)` | Runs one transition, one frame at a time. |
| `Exit` | `void Exit()` | Stops the interpreter. |

## VeloxDev.TransitionSystem.Abstractions

### Class: FramePacerCore

Decides when the sampling loop's next frame happens. The default waits on a thread-pool timer; a host with a UI thread overrides `Arm` / `Disarm` to wait on that thread, so the continuation resumes there and property writes need no dispatch.

**Signature:** `public abstract class FramePacerCore : IDisposable`

| Member | Signature | Description |
|---|---|---|
| `Schedule` | `void Schedule(Action continuation, TimeSpan interval, CancellationToken cancellationToken)` | Runs `continuation` once, no earlier than `interval`, or immediately when the token is already cancelled. A pending continuation is replaced, not queued. |
| `Arm` | `protected abstract void Arm(TimeSpan interval)` | Starts or re-arms the wait. Called once per frame. |
| `Disarm` | `protected abstract void Disarm()` | Ends the wait; must tolerate nothing being armed and must not allocate. |
| `Fire` | `protected void Fire()` | Invokes the pending continuation exactly once. Call it when the wait completes. |
| `Dispose` | `virtual void Dispose()` | Ends the wait and releases any pending continuation. |

The default pacer is supplied by the interpreter; an adapter overrides the pacer factory to bind the loop to its UI thread.

### Class: TransitionSchedulerCore

The non-generic scheduler.

**Signature:** `public abstract class TransitionSchedulerCore : ITransitionSchedulerCore`

| Member | Signature | Description |
|---|---|---|
| `MutualSchedulers` | `static ConditionalWeakTable<object, ITransitionSchedulerCore> { get; protected set; }` | The mutually-exclusive scheduler per target. |
| `NoMutualSchedulers` | `static ConditionalWeakTable<object, ConcurrentDictionary<ITransitionSchedulerCore, byte>> { get; }` | The concurrent schedulers per target (setter is internal). |
| `TryGetMutualScheduler` | `static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler)` | Finds the mutual scheduler. |
| `TryGetNoMutualScheduler` | `static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers)` | Finds the concurrent schedulers. |
| `RemoveNoMutualScheduler` | `static bool RemoveNoMutualScheduler(object source)` | Drops the concurrent scheduler set. |
| `TargetRef` | `virtual WeakReference<object>? TargetRef { get; }` | The target, weakly held. |
| `Execute` | `abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | Runs one pass. |
| `Exit` | `abstract void Exit()` | Stops the scheduler. |

### Class: TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore>

**Signature:**
`public class TransitionSchedulerCore<THost, TTransitionInterpreterCore, TPriorityCore> : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore> where THost : ITransitionHost<TPriorityCore>, new() where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()`

| Member | Signature | Description |
|---|---|---|
| `Execute` | `override Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default)` | The erased entry point; returns immediately when the effect is not typed for this priority. |
| `Execute` | `virtual Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` | The typed pass. |
| `ExecuteCapturing` | `virtual Task<SamplerSet<TPriorityCore>?> ExecuteCapturing(InterpolatorCore producer, IFrameState state, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` | Runs a segment and returns the prepared frame set for replay. |
| `Replay` | `virtual Task Replay(SamplerSet<TPriorityCore> frameSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource? externCts = default)` | Runs the same segment again against the same endpoints, without re-reading the target or re-raising `Awake`. |
| `Exit` | `override void Exit()` | Stops the scheduler. |
| `FindOrCreate<T>` | `static ITransitionScheduler<TPriorityCore> FindOrCreate<T>(T source, bool CanMutualTask = true) where T : class` | Resolves the scheduler filed under `source`; this is the only path that registers it, so a later control call can find the animation. |

A protected static `host` field holds the `THost` instance.

### Class: TransitionInterpreterCore

**Signature:** `public abstract class TransitionInterpreterCore : IDisposable`

| Member | Signature | Description |
|---|---|---|
| `Args` | `virtual TransitionEventArgs Args { get; set; }` | The args handed to every effect callback. |
| `Exit` | `virtual void Exit()` | Stops the sampling loop. |
| `Dispose` | `virtual void Dispose()` | Releases the run's resources. |

Protected state includes `cts`. Derived types override `CreateFramePacer` (via the protected surface) to supply the host's own pacer.

### Class: TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore>

**Signature:** `public abstract class TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore> where TTransitionEffectCore : ITransitionEffect<TPriorityCore>`

| Member | Signature |
|---|---|
| `Execute` | `virtual Task Execute(object target, SamplerSet<TPriorityCore> frameSet, ITransitionEffect<TPriorityCore> effect, CancellationTokenSource cts)` |

### Class: TransitionInterpreterCore<TTransitionEffectCore>

The priority-free variant for hosts that do not use a dispatcher priority.

**Signature:** `public abstract class TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter<NonPriority> where TTransitionEffectCore : ITransitionEffectCore`

| Member | Signature |
|---|---|
| `Execute` | `virtual Task Execute(object target, SamplerSet<NonPriority> frameSet, ITransitionEffect<NonPriority> effect, CancellationTokenSource cts)` |

### Class: TransitionHostBase<TPriorityCore>

**Signature:** `public abstract class TransitionHostBase<TPriorityCore> : ThreadDispatcherBase<TPriorityCore>, ITransitionHost<TPriorityCore>`

| Member | Type | Description |
|---|---|---|
| `IsAlive` | `virtual bool IsAlive { get; }` | Whether the lifetime is still alive; the sampling loop stops when it is not. |

The inherited `IThreadDispatcher<TPriorityCore>` members (`ThreadFor`, `Post`, and their siblings) carry work to the target's thread.

## Events

The effect's callbacks receive `TransitionEventArgs` or `TransitionEventArgs<TStage, TValue>`; both types, and the `ErrorStage` / `WarnStage` enums, are documented under [Effects and easing](../01_effects-and-easing/index.md).

## Example

```csharp
using System.Windows.Threading;
using VeloxDev.TransitionSystem;

// An adapter supplies this pair; the WPF package already does.
var scheduler = TransitionSchedulerCore<UIThreadInspector, TransitionInterpreter, DispatcherPriority>
    .FindOrCreate(box);
```

Application code normally reaches a scheduler only through `Transition<T>.Execute`, `ThemeManager.Transition`, or `InterpolatorCore.CreateScheduler`. See [Platform adapter types](../04_platform-adapter-types/index.md).
