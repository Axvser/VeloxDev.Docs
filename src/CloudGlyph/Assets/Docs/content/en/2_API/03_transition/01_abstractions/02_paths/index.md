# Transition — Abstractions: Property Paths

Namespace `VeloxDev.TransitionSystem.Abstractions` (source: `Src/Core/VeloxDev.Core/TransitionSystem/Binding/TransitionProperty.cs`, `PathSegment.cs`, `PathIndex.cs`). How one animatable value is addressed, how the path is used as a dictionary identity, and the two guards that reject a path which can never animate. The builder and state bag are on [builder](../00_builder/index.md); the engine is on [engine](../01_engine/index.md).

### Class: `TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>`

```csharp
public sealed class TransitionProperty : ITransitionProperty, IEquatable<TransitionProperty>
{
    public TransitionProperty(IEnumerable<PropertyInfo> segments);   // throws on empty / indexed properties
    public static TransitionProperty FromProperty(PropertyInfo propertyInfo);
    public static IReadOnlyList<ITransitionProperty> Members<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static IReadOnlyList<ITransitionProperty> ReadableMembers<TSource>(params Expression<Func<TSource, object?>>[] expressions);
    public static TransitionProperty Combine(TransitionProperty prefix, TransitionProperty suffix);
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
| Constructor | Builds from a chain of property segments; throws `ArgumentException` when `segments` is empty or contains an indexed property (an indexer needs its arguments — write it into an expression instead). |
| `FromProperty` | Wraps one `PropertyInfo` as a single-segment path; throws `ArgumentNullException` on null. **Memoized**: the same `PropertyInfo` always yields the same shared instance. |
| `Members` | Declares animatable member paths from expressions (for `ISampleable.GetAnimatableMembers`); keeps only readable **and** writable members. |
| `ReadableMembers` | Declares readable member paths only — for **struct** `ISampleable` assembly, where members are only read and rebuilt through the constructor, and a non-writable member is therefore fine. |
| `Combine` | Concatenates two paths — `prefix = target.Foo`, `suffix = Foo.Bar` → `target.Foo.Bar`. |
| `TryCreate` | Parses a lambda into a `TransitionProperty` — property segments, array elements, indexers and index expressions alike; returns `false` for an expression the walk cannot describe (an intermediate method call, an index argument with no stable identity) rather than truncating the path, because a truncated identity would let two different paths collide on one dictionary entry. |
| `UnreadablePath` | Sentinel returned by `GetValue` when an intermediate object's runtime type does not match the path. Callers skip such properties rather than interpolating them as `null`. |

**Notes:**
- A path is a chain of **property segments and index segments**, and both take part in the identity. Equality compares a property segment by **name + declaring type** rather than by its `PropertyInfo` instance (reflection does not keep that reference stable in the interface/implementation split), and an index segment by its index arguments; `GetHashCode` follows the same rule, so a `HashSet` or dictionary keeps equal paths as one entry. `IsDescendantOf` uses it to detect a parent/child path pair. `Path` / `ToString()` are **diagnostic only** — two paths that compare equal can render differently when the same index is written with a different lambda parameter name.
- Nothing in the identity depends on a target, and **accessibility is not consulted**: a path is judged by whether the member at its end can be read and written, never by how accessible it is. `private set` and `internal` members animate, and `FromProperty` takes any `PropertyInfo` you can obtain — deliberately, since narrowing that would silently stop animations that work today. Writability is asked of the **last segment only**: an indexer that cannot be assigned to is an ordinary read-only member, and a value type *earlier* on the path is harmless (a reference reached through it still points at the real object) while a **last** member declared on a value type cannot be written (the read yields a copy, so the assignment lands in a temporary).
- Getter and setter are compiled into single delegates on first use (`CompileGetter` / `CompileSetter`), eliminating per-frame reflection — the hot path of `SamplerSet.Apply` and of `host.Run`. The compiled accessor takes the index arguments as a runtime array rather than baking them into the expression, so freezing an argument does not cost a `Reflection.Emit` per animation. `Expression.MakeIndex` **throws** when an index is out of range, so the compiled body wraps the navigation in a `try/catch` that maps `IndexOutOfRangeException` / `ArgumentOutOfRangeException` / `KeyNotFoundException` to the silent outcome the caller already expects (`UnreadablePath` for the getter, `false` for the setter) instead of throwing out of `Prepare` and then again on every frame — from inside a dispatcher callback on the UI thread, where nothing catches.
- `FromProperty`'s memoization is what keeps the reflection-driven entry point cheap: the theme system rebuilds a path for every themed property of every registered target on **every** switch, and a fresh instance would compile its own getter and setter each time (measured at roughly two seconds of UI-thread stall for a thousand two-property elements, before the first frame). It is held in a `ConditionalWeakTable` keyed weakly on the `PropertyInfo`, because the entry is a strong chain — path → segment → `PropertyInfo` → `Type` → `Assembly` — and a strong key would pin the assembly for the life of the process, so a collectible `AssemblyLoadContext` could never unload.
- *Verified by:* `TransitionPropertyTests`, `TransitionPropertyIndexerTests`.

### Static Class: `PathIndex` (namespace `VeloxDev.TransitionSystem`)

```csharp
public static class PathIndex
{
    public static T Frozen<T>(T value);   // never executes — the parser recognises the call and unwraps it
}
```

**Notes:** a path may carry index arguments (`x.Items[0].Width`, `x.Map["player"].Color`, `x.Cells[1, 2]`), and they come in two gears. Their arguments are part of the path's **identity**, not of its value: `x => x.Items[idx].Width` parses to one path whatever `idx` happens to be, which is why a loop declaring five paths from five captured locals gets five entries. By default an argument is **live**: one that can change while the animation runs — a captured local, or a property of the target such as `x.SelectedIndex` — is re-evaluated on every frame, so the path follows it. `Frozen` pins the argument to one slot instead, resolved once in `Prepare`. Freeze whenever the **end value must land where it was read from**: the end value is read once, when the run started, so a live path that moves mid-flight writes an end value computed against the slot it started on. The marker is part of the path's identity, so `Items[i]` and `Items[Frozen(i)]` are two different paths — while a constant argument needs no marker at all (`[0]` and `[Frozen(0)]` are one path, pinned whichever way it is written). Only a frozen argument is wrapped, and only for the run that uses it, so an unindexed path pays nothing.
- *Verified by:* `TransitionPropertyIndexerTests` (`APlainIndexFollowsTheTarget`, `AFrozenIndexStaysWhereItStarted`, `AFrozenIndexIsNotTheSamePathAsALiveOne`, `PrepareFreezesTheIndexBeforeAnyFrameIsWritten`, `PrepareLeavesAPlainIndexFollowing`).

### Path validation

There is no capture / discovery API left in the engine: animated state is declared path by path, and the only path machinery is the two guards below. `TransitionProperty.IsDescendantOf` implements the first, and `TransitionCore.RejectUnsampleablePaths` (internal, called from `CoreValidate`) the second.

- **`TransitionPathConflictException`** — thrown from `StateCore.SetValue` while the transition is built, when an incoming path sits above or below one already on it (one object must be expressed by exactly one path; re-adding the identical path is a plain overwrite). Covers one transition's value paths only. *Verified by:* `TransitionPathConflictTests`.
- **`TransitionPathUnsampleableException`** — thrown synchronously by `Transition<T>.Execute`, when a declared path can never animate (a reference-type leaf with neither a custom interpolator nor a registered sampler). Value types are exempt. *Verified by:* `TransitionPathValidationTests`.

Both are documented in full with the contracts in [transitionsystem/sampling-capture](../../00_transitionsystem/00_sampling-capture/index.md).
