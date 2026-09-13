# Transition — Engine Implementation: `VeloxDev.TransitionSystem.Abstractions`

Namespace `VeloxDev.TransitionSystem.Abstractions` in the `VeloxDev.Core` assembly (source: `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`). These concrete / abstract base types implement the contracts documented in [00_transitionsystem](../00_transitionsystem/index.md). Each platform adapter subclasses them to produce the `VeloxDev.TransitionSystem` types you actually construct (see [03_adapter-provided](../03_adapter-provided/index.md)).

## Builder & state

### Class: `TransitionCore` / `TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore>`

```csharp
public abstract class TransitionCore
{
    public static TSnapshot Create<TSnapshot>() where TSnapshot : StateSnapshotCore, new();
    public static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class;
}

public class TransitionCore<
    T,
    TStateCore,
    TEffectCore,
    TInterpolatorCore,
    TUIThreadInspectorCore,
    TTransitionInterpreterCore,
    TPriorityCore> : StateSnapshotCore<T>
    where T : class
    where TStateCore : IFrameState, new()
    where TEffectCore : ITransitionEffect<TPriorityCore>, new()
    where TInterpolatorCore : InterpolatorCore, new()
    where TUIThreadInspectorCore : IUIThreadInspector<TPriorityCore>, new()
    where TTransitionInterpreterCore : class, ITransitionInterpreter<TPriorityCore>, new()
{
    protected TStateCore state = new();
    protected TransitionCore<...>? root;
    protected TransitionCore<...>? next;

    public TStateCore GetState();
    public static void Execute(T target, IEnumerable<TransitionCore<...>> values, bool CanMutualTask = false);
}
```

| Member | Description |
|---|---|
| `Exit<T>(T target, bool IncludeMutual, bool IncludeNoMutual)` | Stops the target's running animations: cancels the mutual scheduler (animations started with `CanMutualTask: true`) when `IncludeMutual`, and/or every non-mutual scheduler when `IncludeNoMutual`. |
| `Create<TSnapshot>()` | Returns a fresh, un-linked builder and marks it as the *root* of a chain so subsequent `Then()` / `AwaitThen()` segments share it. |
| `GetState()` | The underlying `TStateCore` (a `StateCore` implementing `IFrameState`) — the declared values / samplers / options of this segment. |
| `Execute(target, values, CanMutualTask)` | Runs each builder in the batch on `target`. Non-mutual by default: they run concurrently and do **not** cancel each other — deliberately the opposite of the single-builder `Execute(target)` instance method. |

**Notes:**
- There is **one arity only**: the host's dispatcher priority is a type parameter for every adapter, and a priority-free host passes `NonPriority`. The former 6-generic, priority-free copy of this family no longer exists.
- Each adapter exposes non-generic `Transition : TransitionCore` and `Transition<T> : TransitionCore<T, State, TransitionEffect, Interpolator, UIThreadInspector, TransitionInterpreter, TPriorityCore>` — you normally call `Transition<T>.Create()`, `Transition.Exit(...)`, and the inherited instance `Execute(target, CanMutualTask)` (see [03_adapter-provided](../03_adapter-provided/index.md)). `AddNoMutual` / `RemoveNoMutual` / `RejectUnsampleablePaths` are `internal`. *Verified by:* WPF demo `MainWindow.xaml.cs`.

### Classes: `StateSnapshotCore` / `StateSnapshotCore<T>`

```csharp
public abstract class StateSnapshotCore<T> : StateSnapshotCore where T : class
{
    public void Execute(T target, bool CanMutualTask = true);
    public void Exit(T target, bool IncludeMutual = true, bool IncludeNoMutual = false);
}

public abstract class StateSnapshotCore
{
    // internal: AsRoot / CoreExecute / CoreValidate / CoreThen / CoreAwait / CoreAwaitThen /
    // CoreInterpolator / CoreEffect / CoreRecordState
}
```

**Notes:**
- The abstract root of the concrete builder (`TransitionCore<...>`, above). `Execute` is the public one-shot entry: the target type is fixed by `T`, so it is checked at compile time; it validates the declared paths (a path that can never animate throws `TransitionPathUnsampleableException`) and then runs the chain. Validation happens here rather than inside `CoreExecute`, because that one is `async void` — a throw from it would escape to the synchronization context instead of reaching the caller.
- `Exit(target, ...)` is the instance form of `TransitionCore.Exit`.
- Everything else is `internal`/`protected` machinery: `CoreExecute` walks the linked segments (`next`) and hands each segment's interpolator / delay / cloned effect / state to the scheduler one by one; `CoreThen` / `CoreAwaitThen` / `CoreEffect` / `CoreInterpolator` are the hooks the public extensions and adapter overloads call.
- There is no separate `StateSnapshotCore<...>` builder class, and no top-level `StateSnapshot` or `Transition<T>.StateSnapshot` type: the concrete builder is `TransitionCore<...>`. The builder's *public* vocabulary comes from `TransitionCoreEx` (below) and from each adapter's `Property` / `Effect` overloads.
- *Verified by:* WPF demo chains `.Property(...)`, `.Effect(...)`, `.Await(...)`, `.AwaitThen(...)` on `Transition<Rectangle>` and iterates `GetState().Values`.

### Static Class: `TransitionCoreEx` (extensions, namespace `VeloxDev.TransitionSystem`)

| Member | Signature | Description |
|---|---|---|
| `Await` | `T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Set a delay before this segment plays. |
| `Then` | `T Then<T>(this T snapshot) where T : StateSnapshotCore, new()` | Start a new linked segment after this one. |
| `AwaitThen` | `T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Wait `timeSpan`, then start a new linked segment. |
| `Interpolator` | `TSnapshot Interpolator<TSnapshot, TTarget, TValue>(this TSnapshot snapshot, Expression<Func<TTarget, TValue>> propertyLambda, ISampler interpolator) where TSnapshot : StateSnapshotCore, new()` | Override the per-property sampler for `propertyLambda`. |

**Notes:** these four are the **entire** public surface of `TransitionCoreEx` — there is no `Execute` extension (running is the inherited instance method `Execute(target, CanMutualTask)`). `Await` / `Then` / `AwaitThen` record their delay / link by mutating the builder chain (the delay is honored by `CoreExecute` as a wait before the segment runs, and a `Pause` on the target does not consume it). *Verified by:* WPF demo (`Animation0`/`Animation1`/`Animation2`).

### Class: `StateCore : IFrameState`

Concrete default implementation of `IFrameState`; the adapter's `State` derives from it (see [03_adapter-provided](../03_adapter-provided/index.md)).

| Member | Type | Description |
|---|---|---|
| `Values` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Values { get; protected set; }` | Recorded target values. |
| `Interpolators` | `virtual ConcurrentDictionary<ITransitionProperty, ISampler> Interpolators { get; protected set; }` | Per-property sampler overrides. |
| `Options` | `virtual ConcurrentDictionary<ITransitionProperty, object?> Options { get; protected set; }` | Per-property interpolation options. |
| `SetValue` / `TryGetValue` | three overload families | `(Expression<Func<TSource, TValue>>, TValue?)`, `(ITransitionProperty, object?)`, `(PropertyInfo, object?)`; `Try*` has the matching `out` form. |
| `SetInterpolator` / `TryGetInterpolator` | three overload families | Same addressing, values are `ISampler`. |
| `SetOptions` / `TryGetOptions` | three / one overload family | `SetOptions` has expression / `ITransitionProperty` / `PropertyInfo` forms; `TryGetOptions` has the `ITransitionProperty` form. |
| `Clone` | `virtual IFrameState Clone()` | Independent shallow copy of all three dictionaries. |

**Notes:** Expression overloads record only readable-and-writable paths; the dictionaries are `protected set` so derived adapter states can swap them. *Verified by:* `StateCoreTests`.

## Engine: sampler registry, prepared set, effect, scheduler, interpreter, inspector

### Abstract Class: `InterpolatorCore`

```csharp
public abstract class InterpolatorCore
{
    static InterpolatorCore();   // seeds the default registry
    public static ConcurrentDictionary<Type, ISampler> NativeInterpolators { get; protected set; }

    public static bool TryGetInterpolator(Type type, out ISampler? sampler);
    public static bool RegisterInterpolator(Type type, ISampler sampler);
    public static bool UnregisterInterpolator(Type type, out ISampler? sampler);

    public virtual TransitionSchedulerCore? CreateScheduler(object target, ITransitionEffectCore effect);   // base returns null

    public virtual SamplerSet<TPriorityCore> Prepare<TPriorityCore>(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspector<TPriorityCore> inspector);
}
```

| Member | Description |
|---|---|
| `NativeInterpolators` | The global registry keyed by `Type`. Its static constructor seeds: `double`, `float`, `int`, `long`, `System.Drawing.Point/PointF/Size/SizeF/Color/Rectangle/RectangleF`, and (only when not compiled for `netstandard2.0`) `System.Numerics.Vector2/Vector3/Vector4/Quaternion`. |
| `RegisterInterpolator` | Installs a sampler with **last-writer-wins** semantics (`AddOrUpdate`) — unconditional, atomic. Returns `true`. |
| `UnregisterInterpolator` | Removes the entry; reports it via `sampler`. |
| `TryGetInterpolator` | Resolves the sampler for a *property* type: the exact type, then base classes nearest-first, then interfaces. |
| `CreateScheduler` | The scheduler this platform animates `target` with, for a caller that knows the target only as an `object`; `null` when this platform cannot carry `effect`. |
| `Prepare<TPriorityCore>` | Normalizes a declared state into a runnable `SamplerSet<TPriorityCore>`. |

**Notes on `TryGetInterpolator` (resolution order):** the lookup is not an exact match. The exact type is tried first; then the base-class chain, nearest first; then the type's interfaces, and when several interfaces match, the one whose full name sorts first (ordinal). Interfaces come last and their tie-break is explicit because reflection's own order is not specified. The reason for the walk is that a framework property is very often declared as a subclass of what the adapter registered — a `LinearGradientBrush` property against WPF's registered `Brush` — so an exact match alone would leave it unanimated and report it unsampleable. What that means for a registration: register the **general** type (a concrete-type registration is redundant once a base class or an interface is registered); a general registration must handle its whole family, because the walk will hand it subclasses; and the lookup is per *property type*, so a path declared as `LinearGradientBrush` finds a `Brush` sampler. The walk runs once per property per animation, inside `Prepare` — never per frame. *Verified by:* `InterpolatorCoreTests` (`TryGetInterpolator_FallsBackToABaseClass`, `TryGetInterpolator_PrefersTheNearestBaseClass`, `TryGetInterpolator_FallsBackToAnInterface`, `TryGetInterpolator_PrefersABaseClassOverAnInterface`, `TryGetInterpolator_WithTwoMatchingInterfaces_IsDeterministic`).

**Notes on `CreateScheduler`:** the seam the theme system runs on. A theme switch spans targets of many runtime types, so Core cannot name the type argument of `Transition<T>`, and which inspector, interpreter and dispatcher priority make up a scheduler is the one thing only the platform knows. The base returns `null`; every adapter overrides it and hands out the scheduler it parameterizes (see [03_adapter-provided/01_effect-interpolator](../03_adapter-provided/01_effect-interpolator/index.md)). `null` is the honest answer both for "this platform has not opted in" and for "this effect does not belong to this platform" — the second mirroring the cast the scheduler itself performs before running — and the caller then falls back to switching without animating rather than starting a run that draws nothing. An override must return the instance `TransitionSchedulerCore<...>.FindOrCreate` gives it, never a scheduler it constructed itself: only that path files the scheduler under the target, and that registration is what a later `Transition.Pause` / `Transition.Seek` / `Transition.Exit(target)` reads. *Verified by:* all seven adapters' `PlatformAdapters/Interpolator.cs`; `ThemeManager.SetPlatformInterpolator` / `RunSwitch`.

**Notes on `Prepare<TPriorityCore>`:** For every declared value it reads the current value through `inspector.ProtectedGetValue`; an invalid path (`TransitionProperty.UnreadablePath`) is skipped. Sampler resolution order: (1) a per-property custom sampler from `state.Interpolators`; (2) the registry by `PropertyType`; (3) a *struct* value type implementing `ISampleable` → an internal struct-assembling sampler (member samplers must all resolve, otherwise skipped). **Reference types are never expanded** here — they must be expressed as explicit member paths or handled by a dedicated sampler. It then calls `sampler.NormalizeStart(current, newValue, options)` / `NormalizeEnd(...)` once and stores `(property, sampler, normalizedStart, normalizedEnd, options)` per entry. Adapters derive `Interpolator : InterpolatorCore`, register platform types in their static constructor, and override `CreateScheduler`. *Verified by:* `InterpolatorCoreTests`.

### Class: `SamplerSet<TPriorityCore>`

```csharp
public sealed class SamplerSet<TPriorityCore>
{
    public SamplerSet(IUIThreadInspector<TPriorityCore> inspector);
    public bool CanSetValue();
    public void Apply(object target, double t, TPriorityCore priority = default!);
}
```

**Notes:** The type parameter is the host's dispatcher priority (or `NonPriority`), carried as a type parameter rather than as `object?` so `Apply` hands the priority to the inspector **unboxed** — the previous `object?` parameter boxed a `DispatcherPriority` on every frame of every animation. The constructor throws `ArgumentNullException` on a null inspector. `CanSetValue()` returns `inspector.IsAppAlive()`. `Apply` marshals per-property updates to the UI thread — it stores `t` in a field and reuses one cached UI-thread delegate per target (zero closure allocation per sample), then calls `inspector.ProtectedInvoke`; on the UI thread it runs each entry's `sampler.InsertFrame(target, property, ref working, start, end, options, t)`. `SetCancellation(cts)` (internal, called by the interpreter) lets the set carry the animation's `CancellationTokenSource`: once cancelled — or the app is dead — `Apply` returns immediately (the check is repeated inside the queued write too, so a frame already queued to the UI thread cannot overwrite a reset). *Verified by:* `SamplerSetTests`.

### Class: `TransitionEffectCore : ITransitionEffectCore`

Default descriptor implementation. Defaults: `FPS = 60`, `Duration = 0`, `IsAutoReverse = false`, `LoopTime = 0`, `Ease = Eases.Default`.

| Member | Type / Signature |
|---|---|
| Properties | `virtual int FPS`, `virtual TimeSpan Duration`, `virtual bool IsAutoReverse`, `virtual int LoopTime`, `virtual IEaseCalculator Ease` (all `{ get; set; }`) |
| Events | `virtual event EventHandler<TransitionEventArgs>` — `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally` |
| Invokers | `virtual void InvokeAwake/InvokeStart/InvokeUpdate/InvokeLateUpdate/InvokeCompleted/InvokeCancled/InvokeFinally(object sender, TransitionEventArgs e)` |
| `Clone` | `ITransitionEffectCore Clone()` |

**Notes:** Events are backed by `WeakDelegate` (`VeloxDev.WeakTypes`), so short-lived handler owners do not leak; `Clone` deep-clones the event backing stores and copies all properties. `InvokeCancled` (sic) is the real member name. The plain base itself implements `ITransitionEffect<NonPriority>` (with an explicit `NonPriority` priority that is always `default`), so a priority-free adapter can use it directly; the subclass `TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>` adds `virtual TPriorityCore Priority { get; set; }` and `new ITransitionEffect<TPriorityCore> Clone()`. Adapter effects derive from the priority variant where the platform marshals at a priority, else from the plain base. *Verified by:* `TransitionEffectCoreTests`.

### Abstract Class: `TransitionSchedulerCore : ITransitionSchedulerCore`

```csharp
public abstract class TransitionSchedulerCore : ITransitionSchedulerCore
{
    public static ConditionalWeakTable<object, ITransitionSchedulerCore> MutualSchedulers { get; protected set; }
    public static ConditionalWeakTable<object, ConcurrentDictionary<ITransitionSchedulerCore, byte>> NoMutualSchedulers { get; internal set; }

    public static bool TryGetMutualScheduler(object source, out ITransitionSchedulerCore? scheduler);
    public static bool RemoveMutualScheduler(object source);
    public static bool TryGetNoMutualScheduler(object source, out ITransitionSchedulerCore[] schedulers);
    public static bool RemoveNoMutualScheduler(object source);

    protected readonly SemaphoreSlim _gate = new(1, 1);
    internal WeakReference<object>? targetref;
    public virtual WeakReference<object>? TargetRef { get; protected set; }

    public abstract Task Execute(InterpolatorCore producer, IFrameState state, ITransitionEffectCore effect, CancellationTokenSource? externCts = default);
    public abstract void Exit();
}
```

**Notes:** `MutualSchedulers` caches one *mutual* scheduler per target (a `ConditionalWeakTable`, collected with the target); `NoMutualSchedulers` holds the active one-off *non-mutual* schedulers per target as a concurrent **set** (animations register/unregister themselves from several threads at once, so a plain `List` would lose entries and `Exit` would miss a live run). One generic subclass parameterizes the concrete inspector / interpreter:

- `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore> : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore>` (constraints `TUIThreadInspectorCore : IUIThreadInspector<TPriorityCore>, new()` and `TTransitionInterpreterCore : ITransitionInterpreter<TPriorityCore>, new()`)

Its `Execute` resolves the target from the weak `TargetRef`, **awaits** `ProtectedInvokeAsync` of `effect.InvokeAwake` on the UI thread (awaited, not fire-and-forget, so `Awake` finishes before `Prepare` reads the target — it may veto the animation through `Args.Handled` and may put the target into the state the animation starts from), calls `producer.Prepare<TPriorityCore>(...)`, then hands the prepared set to a fresh interpreter. A `_gate` serializes executions, and each animation registers its `CancellationTokenSource` for its **whole lifetime** (including the `Await` gaps between segments) so `Exit()` can cancel a run that is not currently executing a segment; a generation counter lets a run still queued on the gate give up when an `Exit` lands first. Static `FindOrCreate<T>(T source, bool CanMutualTask = true)` returns the cached mutual scheduler (atomically via `GetValue`) or a fresh non-mutual one. *Verified by:* WPF demo `RepeatMutual` / `ExitAll`, `TransitionSchedulerExitTests`, `NoMutualSchedulerRegistryTests`.

### Abstract Class: `TransitionInterpreterCore : IDisposable`

```csharp
public abstract class TransitionInterpreterCore : IDisposable
{
    protected CancellationTokenSource? cts;
    public virtual TransitionEventArgs Args { get; set; }

    public virtual void Exit();
    public virtual void Dispose();   // cancels the active CancellationTokenSource

    protected Task ExecuteSamplingLoopAsync<TPriorityCore>(object target, SamplerSet<TPriorityCore> frameSet,
        ITransitionEffectCore effect, CancellationTokenSource cts, Action<double> apply);
}
```

**Notes:** Two generic subclasses wire the loop to the sampler set's `Apply`:
- `TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore>` (constraint `TTransitionEffectCore : ITransitionEffect<TPriorityCore>`) — applies `easedT => frameSet.Apply(target, easedT, effect.Priority)`.
- `TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter<NonPriority>` (constraint `TTransitionEffectCore : ITransitionEffectCore`) — applies `easedT => frameSet.Apply(target, easedT)`; a priority-free host keeps sampling on the priority-free path, so `NonPriority` costs nothing per frame.

**Sampling-loop semantics** (`ExecuteSamplingLoopAsync`): Stopwatch-driven continuous sampling, not a frame pump. Normalized time derives from elapsed wall-clock time each iteration (`t = elapsed / Duration`), so `Task.Delay` is never a timing source; the yield interval is capped at `1000 / FPS` ms (`FPS` is a maximum sample rate, not a frame grid). Each pass clamps raw time, applies easing (clamped back into `[0, 1]` for `Back`/`Elastic` overshoot), then `InvokeUpdate` → `apply(easedT)` → `InvokeLateUpdate`; the final frame of each pass is the **exact endpoint** (`t >= 1` → eased `1` forward / `0` reverse), independent of whether `Ease(1)` is exactly `1`. `Start` fires once before the loop; `IsAutoReverse` adds a reverse pass; `LoopTime` repeats (`int.MaxValue` = forever). Normal completion fires `Completed`; cancellation — a cancelled `cts` **or** `Args.Handled = true` → `OperationCanceledException` — fires `Canceled`; `Finally` fires on every end path. *Verified by:* `SamplingLoopTests`, `TransitionEffectCoreTests`.

### Abstract Classes: `UIThreadInspectorBase`, `UIThreadInspectorCore`, `UIThreadInspectorCore<TPriorityCore>`

```csharp
public abstract class UIThreadInspectorBase : IUIThreadInspectorCore
{
    public abstract bool IsAppAlive();
    public abstract bool IsUIThread();
    public abstract object? ProtectedGetValue(object target, ITransitionProperty property);

    protected static Task<bool> DispatchAsync(Func<Action, bool> enqueue, bool onUIThread, Action action);
}

public abstract class UIThreadInspectorCore : UIThreadInspectorBase, IUIThreadInspector<NonPriority>
{
    public abstract bool ProtectedInvoke(object target, Action action);
    public virtual bool ProtectedInvoke(object target, Action action, NonPriority priority) => ProtectedInvoke(target, action);
    public virtual Task<bool> ProtectedInvokeAsync(object target, Action action, NonPriority priority);
}

public abstract class UIThreadInspectorCore<TPriorityCore> : UIThreadInspectorBase, IUIThreadInspector<TPriorityCore>
{
    public abstract bool ProtectedInvoke(object target, Action action, TPriorityCore priority);
    public virtual Task<bool> ProtectedInvokeAsync(object target, Action action, TPriorityCore priority);
}
```

**Notes:** These are skeleton classes — every abstract member (thread identity, marshaling, read marshaling, aliveness) is filled by each adapter's `UIThreadInspector` (see [03_adapter-provided](../03_adapter-provided/index.md)). The base declares no `ProtectedInvoke` at all: it only provides `DispatchAsync`, which queues the action and — unless the call already runs on the UI thread — waits for it to have run, giving up (`false`) when the queue rejected the action. `UIThreadInspectorCore` (the priority-free variant) takes the single-argument `ProtectedInvoke` and implements `IUIThreadInspector<NonPriority>` by forwarding the marker away; `UIThreadInspectorCore<TPriorityCore>` takes the priority-typed one. There is no priority-free inspector *interface* — a host without a priority still implements `IUIThreadInspector<NonPriority>`.

## Property path & validation

### Class: `TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>
{
    public TransitionProperty(IEnumerable<PropertyInfo> segments);   // throws on empty / indexed properties
    public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
    public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static TransitionProperty Combine(ITransitionProperty prefix, ITransitionProperty suffix);
    public static bool TryCreate(LambdaExpression expression, out TransitionProperty? property);

    public string Path { get; }
    public Type PropertyType { get; }
    public bool CanRead { get; }
    public bool CanWrite { get; }

    public static readonly object UnreadablePath;

    public object? GetValue(object? target);
    public bool SetValue(object target, object? value);
    public bool IsDescendantOf(TransitionProperty other);
    // + IEquatable<TransitionProperty>: Equals / GetHashCode / ToString() == Path
}
```

| Member | Description |
|---|---|
| Constructor | Builds from the segment chain; throws `ArgumentException` when `segments` is empty or contains an indexed property. |
| `FromProperty` | Wraps one `PropertyInfo` as a single-segment path; throws `ArgumentNullException` on null. **Memoized**: the same `PropertyInfo` always yields the same shared instance. |
| `Members` | Declares animatable member paths from expressions (for `ISampleable.GetAnimatableMembers`); keeps only readable **and** writable members. |
| `ReadableMembers` | Declares readable member paths only (for struct `ISampleable` assembly — members are read and rebuilt through the constructor). |
| `Combine` | Concatenates two paths — `prefix = target.Foo`, `suffix = Foo.Bar` → `target.Foo.Bar`. |
| `TryCreate` | Parses a lambda (unwrapping `Convert`/`ConvertChecked`) into a `TransitionProperty` — property segments, array elements and indexers alike; returns `false` for an expression the walk cannot describe (an intermediate method call, an index argument with no stable identity) rather than truncating the path. |
| `UnreadablePath` | Sentinel returned by `GetValue` when an intermediate object's runtime type does not match the path. Callers skip such properties rather than interpolating them as `null`. |

**Notes:** Getter and setter are compiled into single delegates on first use (`CompileGetter` / `CompileSetter`), eliminating per-frame reflection — the hot path of `SamplerSet.Apply` / `ProtectedGetValue`. `GetValue` distinguishes a genuinely-null intermediate (`null`, interpolation starts from identity/default) from a type-mismatch intermediate (`UnreadablePath`). `SetValue` returns `false` (no `TargetException`) when an intermediate type mismatches or is null or the leaf has no setter; writing `null` to a reference-type leaf is allowed. A path is a chain of property segments and index segments, and both take part in the identity: `PathSegment.SameAs` compares a property segment by **name + declaring type** rather than by its `PropertyInfo` instance (reflection does not keep that reference stable), and an index segment by its index arguments, with `GetHashCode` following the same rule; `IsDescendantOf` uses it to detect a parent/child path pair. `FromProperty`'s memoization is what keeps the reflection-driven entry point cheap: the theme system rebuilds a path for every themed property of every registered target on **every** switch, and a fresh instance would compile its own getter and setter each time (measured at roughly two seconds of UI-thread stall for a thousand two-property elements, before the first frame). Sharing is safe because a path is immutable and `BindTo` returns the instance itself when there are no index arguments to freeze — always the case for a `FromProperty` path — and the lazy compile is idempotent. `ToString()` returns `Path`. *Verified by:* `TransitionPropertyTests`.

### Static Class: `PathIndex` (namespace `VeloxDev.TransitionSystem`)

```csharp
public static class PathIndex
{
    public static T Frozen<T>(T value);   // never executes — the parser recognises the call structurally and unwraps it
}
```

**Notes:** a path may carry index arguments (`x.Items[0].Width`, `x.Map["player"].Color`), and they come in two gears. By default the argument is **live**: one that can change while the animation runs — a captured local, or a property of the target such as `x.SelectedIndex` — is re-evaluated on every frame, so the path follows it. `Frozen` pins the argument to one slot instead, resolved once in `Prepare`. Freeze whenever the end value must land where it was read from: the end value is read once, when the animation starts, so a live path that moves mid-flight writes an end value computed against the slot it started on. The marker is part of the path's identity, so `Items[i]` and `Items[Frozen(i)]` are two different paths — while a constant argument needs no marker at all: `[0]` and `[Frozen(0)]` are one path, pinned whichever way it is written. Only a frozen argument is wrapped, and only for the run that uses it, so an unindexed path pays nothing. *Verified by:* `TransitionPropertyIndexerTests` (`APlainIndexFollowsTheTarget`, `AFrozenIndexStaysWhereItStarted`, `AFrozenIndexIsNotTheSamePathAsALiveOne`, `PrepareFreezesTheIndexBeforeAnyFrameIsWritten`, `PrepareLeavesAPlainIndexFollowing`).

### Path validation

There is no capture / discovery API left in the engine: animated state is declared path by path, and the only path machinery is the two guards below. `TransitionProperty.IsDescendantOf` implements the first, and `TransitionCore.RejectUnsampleablePaths` (internal, called from `CoreValidate`) the second.

- **`TransitionPathConflictException`** — thrown from `StateCore.SetValue` while the transition is built, when an incoming path sits above or below one already on it (one object must be expressed by exactly one path; re-adding the identical path is a plain overwrite). Covers one transition's value paths only. *Verified by:* `TransitionPathConflictTests`.
- **`TransitionPathUnsampleableException`** — thrown synchronously by `Transition<T>.Execute`, when a declared path can never animate (a reference-type leaf with neither a custom interpolator nor a registered sampler). Value types are exempt. *Verified by:* `TransitionPathValidationTests`.

Both are documented in full with the contracts in [00_transitionsystem/00_sampling-capture](../00_transitionsystem/00_sampling-capture/index.md).
