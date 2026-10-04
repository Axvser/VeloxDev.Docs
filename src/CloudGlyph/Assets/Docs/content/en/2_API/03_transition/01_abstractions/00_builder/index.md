# Transition — Abstractions: Builder & State

Namespace `VeloxDev.TransitionSystem.Abstractions` in the `VeloxDev.Core` assembly (source: `Src/Core/VeloxDev.Core/TransitionSystem/Transition.cs`, `StateSnapshot.cs`, `State.cs`, `TransitionEx.cs`). These are the fluent builder, the segment-chain root and the declared-state bag. The rest of the namespace is on [engine](../01_engine/index.md) and [paths](../02_paths/index.md).

### Class: `TransitionCore`

The non-generic root: the static entry points that do not need a `T`.

```csharp
public abstract class TransitionCore
{
    public static TSnapshot Create<TSnapshot>() where TSnapshot : StateSnapshotCore, new();

    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Pause<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Resume<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void SetRate<T>(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Seek<T>(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static void Seek<T>(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;

    public static int Cycle<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static bool IsPaused<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static TimeSpan Position<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
    public static double Rate<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}
```

| Member | Description |
|---|---|
| `Create<TSnapshot>()` | Returns a fresh, un-linked builder and marks it as the *root* of a chain so subsequent `Then()` / `AwaitThen()` segments share it. |
| `Exit` | Cancels every animation running on `target`: the mutual scheduler (animations started with `CanMutualTask: true`) when `IncludeMutual`, and/or every non-mutual scheduler when `IncludeNoMutual`. Cancellation is a **signal** — the animation stops at its next await, so it may still be releasing its scheduler when this returns; a following mutual `Execute` queues behind it on the scheduler's own gate and lands one frame later at worst. |
| `Pause` / `Resume` | Freeze / unfreeze the run's timeline in place, without ending any animation. |
| `SetRate(target, rate)` | Changes the playback rate without moving the position; `0` freezes without pausing. A negative rate is rejected with `ArgumentOutOfRangeException` (there is no reverse playback). |
| `Seek(target, position)` / `Seek(target, cycle, position)` | Move within the running pass, or into the pass numbered `cycle`, keeping the rate. |
| `Cycle` / `IsPaused` / `Position` / `Rate` | The four queries; each answers for **nothing running** rather than throwing (`0` / `false` / `TimeSpan.Zero` / `0`). `IsPaused` is true only when there is at least one animation and every one of them is paused. |

**Notes:** the control operations act on the `ITimeSourceControl` each run is anchored to, so several animations sharing one timeline are steered together. They deliberately take **no** target lock (unlike `Exit`, whose lock serializes leaving against entering); they neither add nor remove a registration, so there is nothing to serialize and a run that starts mid-sweep is as controllable as one that started before it. `Exit` takes the lock only for the bookkeeping (removing the tracked tokens) and cancels *after* releasing it, because `CancellationTokenSource.Cancel()` runs its callbacks synchronously on the calling thread — holding the lock across them would block the dispatcher on a UI-thread `Exit` and deadlock on a callback that re-enters `Exit`. *Verified by:* WPF demo (`PauseAll`, `ResumeAll`, `SetRate`, `SeekNextPass`, `ExitAll`); `AUTO TEST` `TimelineControl_SteersTheRunningAnimation`; `TimelineControlTests`.

### Class: `TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore>`

```csharp
public class TransitionCore<
    T,
    TStateCore,
    TEffectCore,
    TInterpolatorCore,
    THost,
    TTransitionInterpreterCore,
    TPriorityCore> : StateSnapshotCore<T>
    where T : class
    where TStateCore : IFrameState, new()
    where TEffectCore : ITransitionEffect<TPriorityCore>, new()
    where TInterpolatorCore : InterpolatorCore, new()
    where THost : ITransitionHost<TPriorityCore>, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()
{
    public int RepeatTime { get; set; }         // additional iterations of this segment's loop
    public TStateCore GetState();
    public static void Execute(T target, IEnumerable<TransitionCore<...>> values, bool CanMutualTask = false);
}
```

| Member | Description |
|---|---|
| `RepeatTime` | How many further times this segment's loop runs: `0` — the default — runs it once, and `int.MaxValue` runs it forever. Set through the `Repeat(count)` extension. |
| `GetState()` | The underlying `TStateCore` (a `StateCore` implementing `IFrameState`) — the declared values / samplers / options of this segment. |
| `Execute(target, values, CanMutualTask)` | Runs each builder in the batch on `target`. Non-mutual by default: they run concurrently and do **not** cancel each other — deliberately the opposite of the single-builder `Execute(target)` instance method. |

**Notes:**
- There is **one arity only**: the host's dispatcher priority is a type parameter for every adapter, and a priority-free host passes `NonPriority`. The 5th parameter is the **host** (`THost : ITransitionHost<TPriorityCore>`, `new()`), not a bare thread inspector — the engine asks the host for a thread, a dispatch and a liveness answer through one object (see [host](../../00_transitionsystem/03_host/index.md)).
- A chain's loops are described by `RepeatTime`, and a segment's loop wraps the chain **from its first segment through this one**; loops nest by where they end. See `Repeat` below.
- Each adapter exposes non-generic `Transition : TransitionCore` and `Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>` — you normally call `Transition<T>.Create()`, `Transition.Exit(...)`, and the inherited instance `Execute` (see [adapter-provided](../../03_adapter-provided/index.md)). `AddNoMutual` / `RemoveNoMutual` / `RejectUnsampleablePaths` / `CoreExecute` are `internal`. *Verified by:* WPF demo `MainWindow.xaml.cs`.

### Classes: `StateSnapshotCore` / `StateSnapshotCore<T>`

```csharp
public abstract class StateSnapshotCore<T> : StateSnapshotCore where T : class
{
    public void Execute(T target, bool CanMutualTask = true);
    public void Execute(T target, ITimeSourceControl timeline, bool CanMutualTask = true);

    public void Exit(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Pause(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Resume(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void SetRate(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Seek(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public void Seek(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public bool IsPaused(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public TimeSpan Position(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public int Cycle(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
    public double Rate(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
}

public abstract class StateSnapshotCore
{
    // internal: AsRoot / CoreExecute / CoreValidate / CoreThen / CoreAwait / CoreAwaitThen /
    //           CoreRepeat / CoreInterpolator / CoreEffect / CoreRecordState
}
```

**Notes:**
- The abstract root of the concrete builder (`TransitionCore<...>`, above). `Execute(target, CanMutualTask)` is the public one-shot entry: the target type is fixed by `T`, so it is checked at compile time; it validates the declared paths (a path that can never animate throws `TransitionPathUnsampleableException`) and then runs the chain. Validation happens here rather than inside `CoreExecute`, because that one is `async void` — a throw from it would escape to the synchronization context instead of reaching the caller.
- `Execute(target, timeline, CanMutualTask)` is the **shared-timeline** overload. Animations sharing a timeline share a transport: pausing, changing the rate or seeking one moves all of them together, while each keeps its own pass and its own place in it. That is what a choreographed group needs — several animations staying in lockstep without any of them knowing about the others. Throws `ArgumentNullException` when `timeline` is null.
- The nine control members are the instance forms of `TransitionCore`'s statics — `Exit`/`Pause`/`Resume`/`SetRate`/`Seek`/`IsPaused`/`Position`/`Cycle`/`Rate` — included so a builder can drive its own target without naming `Transition` or `TransitionCore`.
- Everything else is `internal`/`protected` machinery: `CoreExecute` walks the linked segments (`next`) and hands each segment's interpolator / delay / cloned effect / state to the scheduler one by one; `CoreThen` / `CoreAwaitThen` / `CoreRepeat` / `CoreEffect` / `CoreInterpolator` are the hooks the public extensions and adapter overloads call.
- There is no separate `StateSnapshotCore<...>` builder class, and no top-level `StateSnapshot` or `Transition<T>.StateSnapshot` type: the concrete builder is `TransitionCore<...>`. The builder's *public* vocabulary comes from `TransitionCoreEx` (below) and from each adapter's `Property` / `Effect` overloads.
- *Verified by:* WPF demo chains `.Property(...)`, `.Effect(...)`, `.Await(...)`, `.AwaitThen(...)` on `Transition<Rectangle>` and iterates `GetState().Values`; `ChainRepeatTests`.

### Static Class: `TransitionCoreEx` (extensions, namespace `VeloxDev.TransitionSystem`)

| Member | Signature | Description |
|---|---|---|
| `Await` | `T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Set a delay before this segment plays. |
| `Then` | `T Then<T>(this T snapshot) where T : StateSnapshotCore, new()` | Start a new linked segment immediately after this one. |
| `AwaitThen` | `T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Wait `timeSpan`, then start a new linked segment. |
| `Repeat` | `T Repeat<T>(this T snapshot, int count) where T : StateSnapshotCore, new()` | Runs this segment's loop `count` **further** times. `0` runs it once, `int.MaxValue` runs it forever. |
| `Interpolator` | `TSnapshot Interpolator<TSnapshot, TTarget, TValue>(this TSnapshot snapshot, Expression<Func<TTarget, TValue>> propertyLambda, ISampler interpolator) where TSnapshot : StateSnapshotCore, new()` | Override the per-property sampler for `propertyLambda`. |

**Notes:** these five are the **entire** public surface of `TransitionCoreEx` — there is no `Execute` extension (running is the inherited instance method `Execute`). `Await` / `Then` / `AwaitThen` / `Repeat` record their delay / link / loop by mutating the builder chain. *Verified by:* WPF demo (`Animation0`/`Animation1`/`Animation2`), `ChainRepeatTests`.

#### `Repeat` semantics

A segment's loop wraps the chain **from its first segment through this one**, and loops nest by where they end: three segments each carrying `Repeat(1)` run `1, 1, 2, 1, 1, 2, 3, 1, 1, 2, 1, 1, 2, 3`, so only a count on the **last** segment repeats the whole chain. The count is the number of *additional* iterations — the rule the effect's `LoopTime` already follows. Every iteration after a segment's first **replays the frame set that first iteration prepared**, rather than re-reading the target: otherwise a repeated segment would start from where the last iteration stopped, and a chain whose endpoint differs from its start would walk backwards, while a segment writing a property no earlier segment touched would drift a little per iteration. `Awake` is **not** re-raised on a replay (it is the hook that puts the target into the state the segment starts from, and a replay is defined by not depending on the target's state at all); `Start`, `Update`, `LateUpdate`, `Completed` and the diagnostics fire exactly as they do for any other pass.

### Class: `StateCore : IFrameState`

Concrete default implementation of `IFrameState`; the adapter's `State` derives from it (see [adapter-provided](../../03_adapter-provided/index.md)).

| Member | Type | Description |
|---|---|---|
| `Values` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Values { get; protected set; }` | Recorded target values. |
| `Interpolators` | `virtual ConcurrentDictionary<ITransitionProperty, ISampler> Interpolators { get; protected set; }` | Per-property sampler overrides. |
| `Options` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Options { get; protected set; }` | Per-property interpolation options. |
| `SetValue` / `TryGetValue` | three overload families | `(Expression<Func<TSource, TValue>>, TValue?)`, `(ITransitionProperty, object?)`, `(PropertyInfo, object?)`; `Try*` has the matching `out` form. |
| `SetInterpolator` / `TryGetInterpolator` | three overload families | Same addressing, values are `ISampler`. |
| `SetOptions` / `TryGetOptions` | three / one overload family | `SetOptions` has expression / `ITransitionProperty` / `PropertyInfo` forms; `TryGetOptions` has the `ITransitionProperty` form. |
| `Clone` | `virtual IFrameState Clone()` | Independent shallow copy of all three dictionaries. |

**Notes:** the value form of `SetValue` is the funnel that runs the parent/child conflict check (`RejectPathConflict` → `TransitionPathConflictException`). Expression overloads record only readable-and-writable paths; the dictionaries are `protected set` so derived adapter states can swap them. *Verified by:* `StateCoreTests`, `TransitionPathConflictTests`.
