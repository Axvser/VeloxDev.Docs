# Transition — Contracts: Sampling & Property Addressing

Namespace `VeloxDev.TransitionSystem`. These four contracts describe how a value is sampled and how a target property is addressed and declared; the two exceptions at the end reject a declared path that is invalid for the transition or can never animate.

### Interface: `ISampler`

```csharp
public interface ISampler
{
    object? NormalizeStart(object? start, object? end, object? options);
    object? NormalizeEnd(object? start, object? end, object? options);
    void InsertFrame(object target, ITransitionProperty property, ref object? working, object? start, object? end, object? options, double t);
}
```

**Signature notes:**
| Member | Description |
|---|---|
| `NormalizeStart` | Returns the value written at `t <= 0`. Default returns `start` as-is; a sampler may return a copy (e.g. a clone of a mutable reference type) so the target never aliases the shared start instance. |
| `NormalizeEnd` | Returns the value written at `t >= 1`. Default returns `end` as-is; may return a copy for the same aliasing reason. |
| `InsertFrame` | Computes the frame at `t ∈ [0, 1]` and writes it to `property` on `target`. `working` is a per-animation reusable scratch object (created lazily via `ref` on the first middle-frame call, then reused — zero per-frame allocation); value-type samplers ignore it. |

**Notes:**
- Implementations are stateless, thread-safe shared singletons registered in `Abstractions.InterpolatorCore.NativeInterpolators` (or supplied as a per-property override in `IFrameState.Interpolators`).
- Endpoints are handled *inside* `InsertFrame`: `t <= 0` writes the exact (normalized) start, `t >= 1` writes the exact end. No `Update`/`Sample` method exists — this three-method shape replaces the older `IValueInterpolator`/`IInPlaceSampler` designs.
- Implementations **must not mutate** the `start` / `end` arguments: they are shared with the transition declaration that recorded them, so mutating them pollutes it.
- `options` still carries the `RotationDirection` for angular samplers (see [02_eases](../02_eases/index.md)).
- *Verified by:* `NativeSamplersTests` (`DoubleSampler_Endpoints_AreExact`, `DoubleSampler_NullStart_TreatsAsZero`), `NativeSamplersExtendedTests` (per-sampler `_BasicLinear`), `SamplerSetTests`.

### Interface: `ISampleable`

```csharp
public interface ISampleable
{
    IReadOnlyList<ITransitionProperty> GetAnimatableMembers();
    object? CreateFrameValue(IReadOnlyList<object?> memberValues);
}
```

**Notes:**
- Declares how a composite **value type** is animated as a whole — *one level, not recursive*. Only value types take this path: a struct's members cannot be written back in place, so the whole value has to be rebuilt every frame.
- `GetAnimatableMembers` returns the animatable members (paths relative to this type, in `CreateFrameValue` order). Prefer declaring them with `TransitionProperty.Members<Foo>(f => f.Bar, ...)` (see [01_abstractions](../../01_abstractions/index.md)).
- `CreateFrameValue` reconstructs the value from its interpolated members, in `GetAnimatableMembers` order — implementations build it through their constructor (compile-time, zero reflection).
- `InterpolatorCore.Prepare` reaches for this interface **last**: a *struct* value type that implements `ISampleable` and has no registered sampler is handed to the internal `StructAssembler`, which interpolates each declared member with its own registered sampler and reassembles the struct through `CreateFrameValue`. If any member sampler does not resolve, the property is skipped.
- Reference types do **not** use this interface. `Offset` / `Anchor` / `Size` / `Scale` (WorkflowSystem) no longer implement it; only `Viewport` (a struct) does. A property holding a reference type is animated through explicit member paths (`Property(x => x.Foo.Bar, end)`) or by a dedicated `ISampler` that performs decomposition / normalization / interpolation internally — otherwise `Transition<T>.Execute` rejects the path (see below).
- *Verified by:* `StructAssemblerTests`, `NativeSamplersExtendedTests` (test structs).

### Interface: `ITransitionProperty`

```csharp
public interface ITransitionProperty
{
    string Path { get; }
    Type PropertyType { get; }
    PropertyInfo PropertyInfo { get; }
    IReadOnlyList<PropertyInfo> Segments { get; }
    bool CanRead { get; }
    bool CanWrite { get; }
    object? GetValue(object target);
    bool SetValue(object target, object? value);
}
```

| Member | Type | Description |
|---|---|---|
| `Path` | `string` | Dot-separated nested property path (e.g. `"RenderTransform.X"`). |
| `PropertyType` | `Type` | Type of the leaf property. |
| `PropertyInfo` | `PropertyInfo` | Metadata of the leaf property. |
| `Segments` | `IReadOnlyList<PropertyInfo>` | The full property chain (read-only). |
| `CanRead` / `CanWrite` | `bool` | Whether the whole chain supports reading / the leaf supports writing. |
| `GetValue` | `object? GetValue(object target)` | Reads through the chain. Returns `Abstractions.TransitionProperty.UnreadablePath` when an intermediate object's *type* does not match the path (invalid path) and `null` when an intermediate is genuinely null. |
| `SetValue` | `bool SetValue(object target, object? value)` | Writes through the chain. Returns `false` (no `TargetException`) when an intermediate type mismatches or is null; a `null` value on a reference-type leaf is allowed and returns `true`. |

**Notes:**
- The concrete type `TransitionProperty` (namespace `VeloxDev.TransitionSystem.Abstractions`) compiles the getter / setter into single delegates on first use — no per-frame reflection (see [01_abstractions](../../01_abstractions/index.md)).
- *Verified by:* `TransitionPropertyTests` (`GetValue_ReadsFromTarget`, `SetValue_WritesToTarget`, `GetValue_IntermediateTypeMismatch_ReturnsUnreadablePath_NotTargetException`, `SetValue_IntermediateTypeMismatch_ReturnsFalse_NotTargetException`, `GetValue_NullIntermediate_ReturnsNull_NotUnreadable`).

### Interface: `IFrameState`

```csharp
public interface IFrameState
{
    ConcurrentDictionary<ITransitionProperty, object?> Values { get; }
    ConcurrentDictionary<ITransitionProperty, ISampler> Interpolators { get; }
    ConcurrentDictionary<ITransitionProperty, object?> Options { get; }

    void SetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, ISampler interpolator);
    void SetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, TValue? value);
    bool TryGetInterpolator<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out ISampler? interpolator);
    bool TryGetValue<TSource, TValue>(Expression<Func<TSource, TValue>> expression, out TValue? value);

    void SetInterpolator(ITransitionProperty property, ISampler interpolator);
    void SetValue(ITransitionProperty property, object? value);
    bool TryGetInterpolator(ITransitionProperty property, out ISampler? interpolator);
    bool TryGetValue(ITransitionProperty property, out object? value);

    void SetInterpolator(PropertyInfo propertyInfo, ISampler interpolator);
    void SetValue(PropertyInfo propertyInfo, object? value);
    bool TryGetInterpolator(PropertyInfo propertyInfo, out ISampler? interpolator);
    bool TryGetValue(PropertyInfo propertyInfo, out object? value);

    void SetOptions<TSource, TValue>(Expression<Func<TSource, TValue>> expression, object? options);
    void SetOptions(ITransitionProperty property, object? options);
    void SetOptions(PropertyInfo propertyInfo, object? options);
    bool TryGetOptions(ITransitionProperty property, out object? options);

    IFrameState Clone();
}
```

**Notes:**
- A bag of three `ConcurrentDictionary`s keyed by `ITransitionProperty`: recorded target `Values`, per-property `ISampler` overrides, and per-property `Options` (e.g. a `RotationDirection`).
- Every `Set*/TryGet*` operation has three overload families — expression lambda, `ITransitionProperty`, and `PropertyInfo`. Expression / `PropertyInfo` overloads address the same path as the key-based forms.
- The expression overloads record only paths that are readable **and** writable (the concrete `StateCore` refuses to store a read-only or non-writable path).
- `Clone()` returns an independent copy of all three dictionaries.
- `InterpolatorCore.Prepare` consumes a state: it reads `state.Values`, consults `state.Interpolators` for a per-property sampler override, and `state.Options` for the options argument.
- *Verified by:* `StateCoreTests` (`SetValue_Expression_CanRetrieve`, `SetInterpolator_Expression_CanRetrieve`, `Clone_ReturnsIndependentCopy`).

### Exception: `TransitionPathConflictException`

Thrown by the concrete `StateCore.SetValue` while a transition is being **built**, when the incoming path sits above or below a path already on the same transition. One object must be expressed by exactly one path: with both a whole-object path and one of its sub-leaf paths present, a whole-object sampler and a sub-leaf sampler would write the same object every frame and the result would depend on the order they happened to run in. Re-declaring the very same path is a plain overwrite and is allowed.

```csharp
public sealed class TransitionPathConflictException : Exception
{
    public TransitionPathConflictException(ITransitionProperty existing, ITransitionProperty conflicting);
    public ITransitionProperty Existing { get; }
    public ITransitionProperty Conflicting { get; }
}
```

**Notes:** the check covers the value paths of **one** transition (the funnel every value path passes through). Two transitions targeting the same object each keep their own state, so a conflict between them is not detected — nor are paths registered through `SetInterpolator` / `SetOptions`. *Verified by:* `TransitionPathConflictTests`.

### Exception: `TransitionPathUnsampleableException`

Thrown **synchronously by `Transition<T>.Execute(...)`** when a declared path can never animate: its leaf is a reference type with no custom interpolator and no registered sampler, so there is nothing to interpolate with. A value type is exempt — one can still be assembled member by member.

```csharp
public sealed class TransitionPathUnsampleableException : Exception
{
    public TransitionPathUnsampleableException(ITransitionProperty property);
    public ITransitionProperty Property { get; }
}
```

**Notes:** it is raised when the transition runs rather than while it is built — the first moment every path, every interpolator and every sampler registered by the adapter is known, so a path that only looks unsampleable until its interpolator is declared is not rejected by mistake. It is unrelated to `TransitionProperty.UnreadablePath`, where a path is valid but does not match the current target's runtime type: that stays a per-frame skip. Express the value member by member instead, or register a dedicated `ISampler` for the type. *Verified by:* `TransitionPathValidationTests`.
