# Transition — Engine Implementation: `VeloxDev.TransitionSystem.Abstractions`

Namespace `VeloxDev.TransitionSystem.Abstractions` in the `VeloxDev.Core` assembly (source: `Src/Core/VeloxDev.Core/TransitionSystem/*.cs`). These concrete / abstract base types implement the contracts documented in [00_transitionsystem](../00_transitionsystem/index.md). Each platform adapter subclasses them to produce the `VeloxDev.TransitionSystem` types you actually construct (see [03_adapter-provided](../03_adapter-provided/index.md)).

## Snapshot builder & state

### Class: `TransitionCore<TTarget, TStateSnapshotCore>` / `TransitionCore`

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

| Member | Description |
|---|---|
| `Exit<T>(T target, bool IncludeMutual, bool IncludeNoMutual)` | Stops the target's running animations: cancels the mutual scheduler (animations started with `CanMutualTask: true`) when `IncludeMutual`, and/or all non-mutual schedulers when `IncludeNoMutual`. |
| `Create()` | Returns a new `TStateSnapshotCore` (a fresh, un-linked snapshot) and marks it as the *root* of a chain so subsequent `Then()` / `AwaitThen()` segments share it. |
| `Execute(...)` | Runs one or more snapshot(s) against `target` (or against each snapshot's recorded target when the target-less overload is used). A single snapshot defaults to `CanMutualTask: true` — the per-target *mutual* scheduler, interrupting a running animation; `false` runs concurrently via a one-off non-mutual scheduler. The `IEnumerable` overloads default to `CanMutualTask: false`. |

**Notes:** Each adapter exposes non-generic `Transition : TransitionCore` and `Transition<T> : TransitionCore<T, Transition<T>.StateSnapshot>` — you normally call `Transition<T>.Create()`, `Transition.Exit(...)`, and the `Execute` extension (see [03_adapter-provided](../03_adapter-provided/index.md)). `AddNoMutual` / `RemoveNoMutual` are `internal`. *Verified by:* WPF demo `MainWindow.xaml.cs`.

### Class: `StateSnapshotCore` (fluent-builder base family)

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

**Notes:**
- The two concrete generic classes differ only on the priority axis: the 6-generic variant is used by adapters without a dispatcher priority (MAUI, WinForms, Razor); the 7-generic one — adding `TPriorityCore` — by WPF, Avalonia, Jalium and WinUI.
- The only public member is `GetState()` (returns the underlying `TStateCore`, a `StateCore` implementing `IFrameState`). Everything else is `internal`/`protected` machinery: `CoreExecute` walks the linked segments (`next`) and hands each segment's interpolator / delay / cloned effect / state to the scheduler one by one; `CoreThen`/`CoreAwaitThen`/`CoreEffect`/`CoreInterpolator` are the hooks the public extensions and adapter overloads call.
- Because most members are protected, the builder's *public* vocabulary comes from `TransitionCoreEx` (below) and from each adapter's nested `StateSnapshot` overloads (`Property`, `Effect`).
- *Verified by:* WPF demo chains `.Property(...)`, `.Effect(...)`, `.Await(...)`, `.AwaitThen(...)` on `Transition<Rectangle>.StateSnapshot`, and iterates `snapshot.GetState().Values`.

### Static Class: `TransitionCoreEx` (extensions, namespace `VeloxDev.TransitionSystem`)

| Member | Signature | Description |
|---|---|---|
| `Await` | `T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Set a delay before this segment plays. |
| `Then` | `T Then<T>(this T snapshot) where T : StateSnapshotCore, new()` | Start a new linked segment after this one. |
| `AwaitThen` | `T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Wait `timeSpan`, then start a new linked segment. |
| `Interpolator` | `TSnapshot Interpolator<TSnapshot, TTarget, TValue>(this TSnapshot snapshot, Expression<Func<TTarget, TValue>> propertyLambda, ISampler interpolator) where TSnapshot : StateSnapshotCore, new()` | Override the per-property sampler for `propertyLambda`. |
| `Execute` | `void Execute<T>(this T snapshot, object target, bool CanMutualTask = true) where T : StateSnapshotCore` | Run the snapshot on `target`. |
| `Execute` | `void Execute<T>(this T snapshot, bool CanMutualTask = true) where T : StateSnapshotCore` | Run the snapshot on its recorded target. |

**Notes:** `Await` / `Then` / `AwaitThen` record their delay / link by mutating the snapshot chain (the delay is honored by `CoreExecute` as a `Task.Delay` before the segment runs). *Verified by:* WPF demo (`Animation0`/`Animation1`/`Animation2`).

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

    public virtual SamplerSet Prepare(object target, IFrameState state, ITransitionEffectCore effect, IUIThreadInspectorCore inspector);
}
```

| Member | Description |
|---|---|
| `NativeInterpolators` | The global registry keyed by `Type`. Its static constructor seeds: `double`, `float`, `int`, `long`, `System.Drawing.Point/PointF/Size/SizeF/Color/Rectangle/RectangleF`, and (only when not compiled for `netstandard2.0`) `System.Numerics.Vector2/Vector3/Vector4/Quaternion`. |
| `RegisterInterpolator` | Installs a sampler with **last-writer-wins** semantics (`AddOrUpdate`) — unconditional, atomic. Returns `true`. |
| `UnregisterInterpolator` | Removes the entry; reports it via `sampler`. |
| `TryGetInterpolator` | Looks up a type in the registry. |
| `Prepare` | Normalizes a recorded state into a runnable `SamplerSet`. |

**Notes on `Prepare`:** For every recorded value it reads the current value through `inspector.ProtectedGetValue`; an invalid path (`TransitionProperty.UnreadablePath`) is skipped. Sampler resolution order: (1) a per-property custom sampler from `state.Interpolators`; (2) the registry by `PropertyType`; (3) a *struct* value type implementing `ISampleable` → an internal struct-assembling sampler (member samplers must all resolve, otherwise skipped). It then calls `sampler.NormalizeStart(current, newValue, options)` / `NormalizeEnd(...)` once and stores `(property, sampler, normalizedStart, normalizedEnd, options)` per entry. Adapters derive `Interpolator : InterpolatorCore` and register platform types in their static constructor. *Verified by:* `InterpolatorCoreTests`.

### Class: `SamplerSet`

```csharp
public sealed class SamplerSet
{
    public SamplerSet(IUIThreadInspectorCore inspector);
    public bool CanSetValue();
    public void Apply(object target, double t, object? priority = default);
}
```

**Notes:** The constructor throws `ArgumentNullException` on a null inspector. `CanSetValue()` returns `inspector.IsAppAlive()`. `Apply` marshals per-property updates to the UI thread — it stores `t` in a field and reuses one cached UI-thread delegate per target (zero closure allocation per sample), then calls `inspector.ProtectedInvoke`; on the UI thread it runs each entry's `sampler.InsertFrame(target, property, ref working, start, end, options, t)`. `SetCancellation(cts)` (internal, called by the interpreter) lets the set carry the animation's `CancellationTokenSource`: once cancelled — or the app is dead — `Apply` returns immediately, so stale queued frames never overwrite a reset result. *Verified by:* `SamplerSetTests`.

### Class: `TransitionEffectCore : ITransitionEffectCore`

Default descriptor implementation. Defaults: `FPS = 60`, `Duration = 0`, `IsAutoReverse = false`, `LoopTime = 0`, `Ease = Eases.Default`.

| Member | Type / Signature |
|---|---|
| Properties | `virtual int FPS`, `virtual TimeSpan Duration`, `virtual bool IsAutoReverse`, `virtual int LoopTime`, `virtual IEaseCalculator Ease` (all `{ get; set; }`) |
| Events | `virtual event EventHandler<TransitionEventArgs>` — `Awaked`, `Start`, `Update`, `LateUpdate`, `Canceled`, `Completed`, `Finally` |
| Invokers | `virtual void InvokeAwake/InvokeStart/InvokeUpdate/InvokeLateUpdate/InvokeCompleted/InvokeCancled/InvokeFinally(object sender, TransitionEventArgs e)` |
| `Clone` | `ITransitionEffectCore Clone()` |

**Notes:** Events are backed by `WeakDelegate` (`VeloxDev.WeakTypes`), so short-lived handler owners do not leak; `Clone` deep-clones the event backing stores and copies all properties. `InvokeCancled` (sic) is the real member name. The subclass `TransitionEffectCore<TPriorityCore> : TransitionEffectCore, ITransitionEffect<TPriorityCore>` adds `virtual TPriorityCore Priority { get; set; }` and `new ITransitionEffect<TPriorityCore> Clone()`. Adapter effects derive from the priority variant where the platform marshals at a priority, else from the plain base. *Verified by:* `TransitionEffectCoreTests`.

### Abstract Class: `TransitionSchedulerCore : ITransitionSchedulerCore`

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

**Notes:** `MutualSchedulers` caches one *mutual* scheduler per target (a `ConditionalWeakTable`, collected with the target); `NoMutualSchedulers` holds the active one-off *non-mutual* schedulers per target. Two generic subclasses parameterize the concrete inspector / interpreter:
- `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore, TPriorityCore> : TransitionSchedulerCore, ITransitionScheduler<TPriorityCore>`
- `TransitionSchedulerCore<TUIThreadInspectorCore, TTransitionInterpreterCore> : TransitionSchedulerCore, ITransitionScheduler`

Their `Execute` resolves the target from the weak `TargetRef`, fires `effect.InvokeAwake` on the UI thread (at the effect's priority when priority-typed), calls `producer.Prepare(...)`, then hands the prepared set to a fresh interpreter. A `_gate` serializes executions; `Exit()` → `CancelCurrent()` cancels the running `cts`. Static `FindOrCreate<T>(T source, bool CanMutualTask = true)` returns the cached mutual scheduler (creating it if absent) or a fresh non-mutual one. *Verified by:* WPF demo `RepeatMutual` / `ExitAll`.

### Abstract Class: `TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable`

```csharp
public abstract class TransitionInterpreterCore : ITransitionInterpreterCore, IDisposable
{
    protected CancellationTokenSource? cts;
    public virtual TransitionEventArgs Args { get; set; }

    public abstract Task Execute(object target, SamplerSet frameSet, ITransitionEffectCore effect, CancellationTokenSource cts);
    public virtual void Exit();
    public virtual void Dispose();   // cancels the active CancellationTokenSource

    protected Task ExecuteSamplingLoopAsync(object target, SamplerSet frameSet, ITransitionEffectCore effect,
        CancellationTokenSource cts, Action<double> apply);
}
```

**Notes:** Two generic subclasses wire the loop to the sampler set's `Apply`:
- `TransitionInterpreterCore<TTransitionEffectCore> : TransitionInterpreterCore, ITransitionInterpreter` (constraint `TTransitionEffectCore : ITransitionEffectCore`) — applies `easedT => frameSet.Apply(target, easedT)`.
- `TransitionInterpreterCore<TTransitionEffectCore, TPriorityCore> : TransitionInterpreterCore, ITransitionInterpreter<TPriorityCore>` (constraint `TTransitionEffectCore : ITransitionEffect<TPriorityCore>`) — applies `easedT => frameSet.Apply(target, easedT, effect.Priority)`.

**Sampling-loop semantics** (`ExecuteSamplingLoopAsync`): Stopwatch-driven continuous sampling, not a frame pump. Normalized time derives from elapsed wall-clock time each iteration (`t = elapsed / Duration`), so `Task.Delay` is never a timing source; the yield interval is capped at `1000 / FPS` ms (`FPS` is a maximum sample rate, not a frame grid). Each pass clamps raw time, applies easing (clamped back into `[0, 1]` for `Back`/`Elastic` overshoot), then `InvokeUpdate` → `apply(easedT)` → `InvokeLateUpdate`; the final frame of each pass is the **exact endpoint** (`t >= 1` → eased `1` forward / `0` reverse), independent of whether `Ease(1)` is exactly `1`. `Start` fires once before the loop; `IsAutoReverse` adds a reverse pass; `LoopTime` repeats (`int.MaxValue` = forever). Normal completion fires `Completed`; cancellation — a cancelled `cts` **or** `Args.Handled = true` → `OperationCanceledException` — fires `Canceled`; `Finally` fires on every end path. *Verified by:* `SamplingLoopTests`, `TransitionEffectCoreTests`.

### Abstract Classes: `UIThreadInspectorBase`, `UIThreadInspectorCore`, `UIThreadInspectorCore<TPriorityCore>`

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
    public override void ProtectedInvoke(object target, Action action, object? priority = default); // no-op unless priority is TPriorityCore
}
```

**Notes:** These are skeleton classes — every abstract member (thread identity, marshaling, read marshaling, aliveness) is filled by each adapter's `UIThreadInspector` (see [03_adapter-provided](../03_adapter-provided/index.md)). Priority-typed inspectors accept the adapter's dispatcher priority; non-priority inspectors marshal at the framework default.

## Property path & capture

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
    public PropertyInfo PropertyInfo { get; }
    public bool CanRead { get; }
    public bool CanWrite { get; }
    public IReadOnlyList<PropertyInfo> Segments { get; }

    public static readonly object UnreadablePath;

    public object? GetValue(object target);
    public bool SetValue(object target, object? value);
    // + IEquatable<TransitionProperty>: Equals / GetHashCode / ToString() == Path
}
```

| Member | Description |
|---|---|
| Constructor | Builds from the segment chain; throws `ArgumentException` when `segments` is empty or contains an indexed property. |
| `FromProperty` | Single-segment property; throws `ArgumentNullException` on null. |
| `Members` | Declares animatable member paths from expressions (for `ISampleable.GetAnimatableMembers`); keeps only readable **and** writable members. |
| `ReadableMembers` | Declares readable member paths only (for struct `ISampleable` assembly — members are read and rebuilt through the constructor). |
| `Combine` | Concatenates two paths — `prefix = target.Foo`, `suffix = Foo.Bar` → `target.Foo.Bar`. |
| `TryCreate` | Parses a lambda (unwrapping `Convert`/`ConvertChecked`) into a `TransitionProperty`; returns `false` for non-member / indexed expressions. |
| `UnreadablePath` | Sentinel returned by `GetValue` when an intermediate object's runtime type does not match the path. Callers skip such properties rather than interpolating them as `null`. |

**Notes:** Getter and setter are compiled into single delegates on first use (`CompileGetter` / `CompileSetter`), eliminating per-frame reflection — the hot path of `SamplerSet.Apply` / `ProtectedGetValue`. `GetValue` distinguishes a genuinely-null intermediate (`null`, interpolation starts from identity/default) from a type-mismatch intermediate (`UnreadablePath`). `SetValue` returns `false` (no `TargetException`) when an intermediate type mismatches or is null or the leaf has no setter; writing `null` to a reference-type leaf is allowed. Equality compares segment chains; `ToString()` returns `Path`. *Verified by:* `TransitionPropertyTests`.

### Static Class: `TransitionSnapshotHelper`

| Member | Signature | Description |
|---|---|---|
| `CaptureSpecific` | `void CaptureSpecific<T>(T target, IFrameState state, IEnumerable<Expression<Func<T, object?>>>? expressions) where T : class` | Records exactly the explicit expression paths (readable & writable). |
| `CaptureAll` | `void CaptureAll<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? extraExpressions = null) where T : class` | Records every discovered animatable path plus any extra explicit expressions. |
| `CaptureAllExcept` | `void CaptureAllExcept<T>(T target, IFrameState state, Func<Type, bool> canAnimateType, IEnumerable<Expression<Func<T, object?>>>? excludedExpressions = null) where T : class` | Records discovery minus the excluded paths **and their child paths**. |
| `DiscoverAnimatableProperties` | `IReadOnlyCollection<ITransitionProperty> DiscoverAnimatableProperties(object target, Func<Type, bool> canAnimateType)` | Walks the object graph and returns the set of animatable leaf paths. |
| `TryGetPropertyFromExpression` | `bool TryGetPropertyFromExpression<T>(Expression<Func<T, object?>> expression, out ITransitionProperty? property) where T : class` | Parses a single expression (must be readable & writable, non-indexed). |
| `CaptureProperties` | `void CaptureProperties(object target, IFrameState state, IEnumerable<ITransitionProperty> properties)` | Records each readable & writable property's current value into the state. |

**Notes on discovery (`DiscoverAnimatableProperties`):** Recursive, cycle-guarded walk (an object back-reference or a member type already on the path stops recursion — there is **no depth limit**; indexed properties are skipped). For each public readable + writable instance property: the type is animatable (`canAnimateType(type)` **or** `typeof(ISampler).IsAssignableFrom(type)`) → the whole path is a leaf; otherwise the value implements `ISampleable` → a *struct* is recorded as a whole path (rebuilt via `CreateFrameValue`) and a reference type has its declared members expanded recursively; otherwise the type is descendable (`string`, `object`, primitives, enums, value types, `IEnumerable`, `Delegate` are not, after nullable unwrapping) and the value is non-null → recurse into its sub-leaves. `CaptureAll` / `CaptureAllExcept` are the engine behind `TransitionEx.SnapshotAll` / `SnapshotExcept`. *Verified by:* `TransitionSnapshotHelperTests`.
