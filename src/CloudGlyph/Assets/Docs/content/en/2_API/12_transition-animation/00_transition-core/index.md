# Transition Core

The chain model, the per-target control plane, and the frame state. Namespaces: `VeloxDev.TransitionSystem.Abstractions` (chain, state, property) and `VeloxDev.TransitionSystem` (fluent extensions, exceptions).

## VeloxDev.TransitionSystem.Abstractions

### Class: TransitionCore

The non-generic control plane. Every member is static and addressed by target, not by snapshot.

**Signature:** `public abstract class TransitionCore`

| Member | Signature | Description |
|---|---|---|
| `Create<TSnapshot>` | `static TSnapshot Create<TSnapshot>() where TSnapshot : StateSnapshotCore, new()` | Creates a snapshot and marks it as the chain root. |
| `Exit<T>` | `static void Exit<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | Cancels every selected run on `target`. The stop is a signal; the run may still be releasing its scheduler when the call returns. |
| `Pause<T>` | `static void Pause<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | Freezes the selected timelines; paused time is excluded from the animation. |
| `Resume<T>` | `static void Resume<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | Resumes at the rate last set. |
| `SetRate<T>` | `static void SetRate<T>(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | Multiplies elapsed time. Zero freezes without setting `IsPaused`; a negative rate throws `ArgumentOutOfRangeException`. |
| `Seek<T>` | `static void Seek<T>(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | Moves within the running pass. A position past the end finishes it; a negative one pins to the start. |
| `Seek<T>` | `static void Seek<T>(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | Moves within a named pass. |
| `Cycle<T>` | `static int Cycle<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | The pass being played, or 0 when nothing runs. |
| `IsPaused<T>` | `static bool IsPaused<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | True when every selected run is paused and at least one exists. |
| `Position<T>` | `static TimeSpan Position<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | How far into the current pass, or `TimeSpan.Zero`. |
| `Rate<T>` | `static double Rate<T>(T target, bool IncludeMutual = true, bool IncludeNoMutual = false) where T : class` | The configured rate, remembered across a pause, or 0 when nothing runs. |

`IncludeMutual` addresses the run that a later `Execute` supersedes; `IncludeNoMutual` addresses concurrent runs started with `CanMutualTask: false`.

### Class: TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore>

The typed chain segment.

**Signature:**
`public class TransitionCore<T, TStateCore, TEffectCore, TInterpolatorCore, THost, TTransitionInterpreterCore, TPriorityCore> : StateSnapshotCore<T> where T : class where TStateCore : IFrameState, new() where TEffectCore : ITransitionEffect<TPriorityCore>, new() where TInterpolatorCore : InterpolatorCore, new() where THost : ITransitionHost<TPriorityCore>, new() where TTransitionInterpreterCore : ITransitionInterpreter<TPriorityCore>, new()`

| Member | Signature | Description |
|---|---|---|
| `RepeatTime` | `int RepeatTime { get; set; }` | Additional iterations of the chain from its first segment through this one. `0` runs once; `int.MaxValue` runs forever. |
| `GetState` | `TStateCore GetState()` | The segment's frame state. |
| `Execute` | `static void Execute(T target, IEnumerable<TransitionCore<…>> values, bool CanMutualTask = false)` | Starts a batch of snapshots, non-mutual by default. |

Protected fields: `state`, `root`, `next`, `effect`, `interpolator`.

### Class: StateSnapshotCore<T>

The typed snapshot base and the public execution surface on a chain segment.

**Signature:** `public abstract class StateSnapshotCore<T> : StateSnapshotCore where T : class`

| Member | Signature | Description |
|---|---|---|
| `Execute` | `void Execute(T target, bool CanMutualTask = true)` | Validates the chain and starts it. `CanMutualTask: true` cancels the previous run on the target. |
| `Execute` | `void Execute(T target, ITimeSourceControl timeline, bool CanMutualTask = true)` | Starts against a shared timeline; pauses and rates then move every animation anchored to it. |
| `Exit` | `void Exit(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent to `TransitionCore.Exit`. |
| `Pause` | `void Pause(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent to `TransitionCore.Pause`. |
| `Resume` | `void Resume(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent to `TransitionCore.Resume`. |
| `SetRate` | `void SetRate(T target, double rate, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent to `TransitionCore.SetRate`. |
| `Seek` | `void Seek(T target, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent to `TransitionCore.Seek`. |
| `Seek` | `void Seek(T target, int cycle, TimeSpan position, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent to the cycle overload. |
| `IsPaused` | `bool IsPaused(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent query. |
| `Position` | `TimeSpan Position(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent query. |
| `Cycle` | `int Cycle(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent query. |
| `Rate` | `double Rate(T target, bool IncludeMutual = true, bool IncludeNoMutual = false)` | Equivalent query. |

**Exceptions:** `TransitionPathUnsampleableException` from `Execute` when a declared path can never animate; `ArgumentNullException` when `timeline` is null.

### Class: StateSnapshotCore

The non-generic snapshot contract. Its members are internal abstracts implemented by `TransitionCore<…>`; it is not used directly.

**Signature:** `public abstract class StateSnapshotCore`

### Class: StateCore

The default frame state: values, samplers and per-property options keyed by `ITransitionProperty`.

**Signature:** `public class StateCore : IFrameState`

| Member | Type | Description |
|---|---|---|
| `Values` | `virtual ConcurrentDictionary<ITransitionProperty, object?>` | The end value of each animated property. |
| `Interpolators` | `virtual ConcurrentDictionary<ITransitionProperty, ISampler>` | A per-property sampler override. |
| `Options` | `virtual ConcurrentDictionary<ITransitionProperty, object?>` | Per-property options handed to the sampler. |

| Method | Signature |
|---|---|
| `SetInterpolator` | `virtual void SetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, ISampler interpolator)` |
| `SetValue` | `virtual void SetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, TValue? value)` |
| `TryGetInterpolator` | `virtual bool TryGetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out ISampler? interpolator)` |
| `TryGetValue` | `virtual bool TryGetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out TValue? value)` |
| `SetInterpolator` | `virtual void SetInterpolator(ITransitionProperty propertyInfo, ISampler interpolator)` |
| `SetValue` | `virtual void SetValue(ITransitionProperty propertyInfo, object? value)` |
| `TryGetInterpolator` | `virtual bool TryGetInterpolator(ITransitionProperty propertyInfo, out ISampler? interpolator)` |
| `TryGetValue` | `virtual bool TryGetValue(ITransitionProperty propertyInfo, out object? value)` |
| `SetInterpolator` | `virtual void SetInterpolator(PropertyInfo propertyInfo, ISampler interpolator)` |
| `SetValue` | `virtual void SetValue(PropertyInfo propertyInfo, object? value)` |
| `TryGetInterpolator` | `virtual bool TryGetInterpolator(PropertyInfo propertyInfo, out ISampler? interpolator)` |
| `TryGetValue` | `virtual bool TryGetValue(PropertyInfo propertyInfo, out object? value)` |
| `SetOptions` | `virtual void SetOptions<TSource, TValue>(Expression<Func<TSource, TValue>> expression, object? options)` |
| `SetOptions` | `virtual void SetOptions(ITransitionProperty property, object? options)` |
| `SetOptions` | `virtual void SetOptions(PropertyInfo propertyInfo, object? options)` |
| `TryGetOptions` | `virtual bool TryGetOptions(ITransitionProperty property, out object? options)` |
| `Clone` | `virtual IFrameState Clone()` |

`SetValue` rejects a path that is a descendant or an ancestor of one already declared, throwing `TransitionPathConflictException`; re-adding the same path is a plain overwrite.

### Class: TransitionProperty

A compiled path to one animatable value. It is both the accessor and the dictionary key, so equality is load-bearing.

**Signature:** `public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

| Member | Signature | Description |
|---|---|---|
| Constructor | `TransitionProperty(IEnumerable<PropertyInfo> segments)` | A property-only path; rejects index segments. |
| `Path` | `string Path { get; }` | The path text, for diagnostics only. |
| `PropertyType` | `Type PropertyType { get; }` | The value type at the end of the path. |
| `CanRead` / `CanWrite` | `bool { get; }` | Whether every segment can be read / the last can be written. |
| `UnreadablePath` | `static readonly object` | Sentinel returned by `GetValue` when a path does not match the target. |
| `GetValue` | `object? GetValue(object? target)` | Reads, or returns `UnreadablePath` on a runtime-type mismatch. |
| `SetValue` | `bool SetValue(object target, object? value)` | Writes; false when the path does not apply. |
| `TryCreate` | `static bool TryCreate(LambdaExpression expression, out TransitionProperty? property)` | Parses a lambda, including nested property and index segments. |
| `FromProperty` | `static TransitionProperty FromProperty(PropertyInfo propertyInfo)` | Wraps a single member. |
| `Members<TSource>` | `static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | Declares members for `ISampleable.GetAnimatableMembers`. |
| `ReadableMembers<TSource>` | `static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions)` | The readable subset. |
| `Combine` | `static TransitionProperty Combine(TransitionProperty prefix, TransitionProperty suffix)` | Concatenates two paths. |
| `IsDescendantOf` | `bool IsDescendantOf(TransitionProperty other)` | Whether this path extends `other`. |
| `Equals` / `GetHashCode` / `ToString` | standard overrides | Value equality over segments and index arguments. |

### Exceptions

| Type | Signature | Condition |
|---|---|---|
| `TransitionPathConflictException` | `public sealed class TransitionPathConflictException : Exception` | A path is declared above or below an existing one. |
| `TransitionPathUnsampleableException` | `public sealed class TransitionPathUnsampleableException : Exception` | A declared reference-typed path has no sampler. |

## VeloxDev.TransitionSystem

### Class: PathIndex

Marks an index argument in a transition path so it is evaluated once instead of every frame.

**Signature:** `public static class PathIndex`

| Member | Signature | Description |
|---|---|---|
| `Frozen<T>` | `static T Frozen<T>(T value)` | Pins the index argument for the whole animation. The call never executes; the path parser recognises it structurally and unwraps its argument. |

Use it as `Transition<T>.Create().Property(x => x.Items[PathIndex.Frozen(i)].Width, end)`. The call is part of the path's identity, so `Items[i]` and `Items[Frozen(i)]` are different paths. Pin the index whenever the end value must land on the slot it was read from.

### Class: TransitionCoreEx

Fluent chain building over any `StateSnapshotCore`.

**Signature:** `public static class TransitionCoreEx`

| Member | Signature | Description |
|---|---|---|
| `Await<T>` | `static T Await<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Delays before the next segment. |
| `Then<T>` | `static T Then<T>(this T snapshot) where T : StateSnapshotCore, new()` | Starts a segment immediately. |
| `AwaitThen<T>` | `static T AwaitThen<T>(this T snapshot, TimeSpan timeSpan) where T : StateSnapshotCore, new()` | Delays, then starts a segment. |
| `Repeat<T>` | `static T Repeat<T>(this T snapshot, int count) where T : StateSnapshotCore, new()` | Additional loop iterations; only a count on the last segment repeats the whole chain. |
| `Interpolator<TSnapshot, TTarget, TValue>` | `static TSnapshot Interpolator<TSnapshot, TTarget, TValue>(this TSnapshot snapshot, Expression<Func<TTarget, TValue>> propertyLambda, ISampler interpolator)` | Overrides the sampler for one property. |

## Example

```csharp
using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Shapes;
using VeloxDev.TransitionSystem;

var box = new Rectangle { RenderTransform = new TranslateTransform() };

var chain = Transition<Rectangle>.Create()
    .Property(r => r.Opacity, 0.25d)
    .Property(r => ((TranslateTransform)r.RenderTransform).X, 220d)
    .Effect(new TransitionEffect { Duration = TimeSpan.FromSeconds(1.5), Ease = Eases.Cubic.InOut });

chain.Execute(box);
Transition.Pause(box);
Transition.Seek(box, TimeSpan.FromMilliseconds(750));
Transition.Exit(box);
```

`Transition<T>` is the adapter front end; see [Platform adapter types](../04_platform-adapter-types/index.md).
