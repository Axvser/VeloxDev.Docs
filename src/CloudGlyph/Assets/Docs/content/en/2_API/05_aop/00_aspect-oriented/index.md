# AOP — `VeloxDev.AspectOriented` (AOP runtime, `#if NET`)

The runtime namespace. Every source file is wrapped in `#if NET`, so these types are only available on the `net5.0+` targets of the package.

### Type: `AspectOrientedAttribute`

```csharp
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
    AllowMultiple = false, Inherited = false)]
public class AspectOrientedAttribute : Attribute { }
```

Marks methods, properties, and fields of a `partial` class for proxy interception. The source generator exposes the marked members on the generated AOP interface and extends the class to implement it.

#### AspectOrientedAttribute.AspectOrientedAttribute

**Signature:**
`AspectOrientedAttribute()`

| Parameter | Type | Description |
|---|---|---|
| *(none)* | | Parameterless constructor (the attribute carries no state) |

**Returns:** `AspectOrientedAttribute`

**Exceptions:** none

**Example:**
```text
// Source: Examples/AOP/WPF/Demo/TeamViewModel.cs
[VeloxProperty][AspectOriented] private string _name = string.Empty;
```

**Notes:**
- Applies to `Method`, `Property`, and `Field` targets only. `AllowMultiple = false`, `Inherited = false`.
- A marked member must be `public` for the generator to expose it on the proxy interface (fields marked `[VeloxProperty]` / `[Observable]` become properties).

### Type: `IAspectOriented`

```csharp
public interface IAspectOriented { }
```

Empty marker interface. Every generated AOP proxy interface derives from it; it is used as the generic constraint for `ProxyEx.CreateProxy` / `ProxyEx.SetProxy` / `Aop.GetTarget`.

**Members:** none.

### Type: `ProxyMembers` (enum)

```csharp
public enum ProxyMembers { Getter, Setter, Method }
```

Selects which hook table a `SetProxy` call writes to.

| Member | Description |
|---|---|
| `ProxyMembers.Getter` | Property getter hooks — stored in `ProxyInstance.GetterActions`, matched by `get_*` method names |
| `ProxyMembers.Setter` | Property setter hooks — stored in `ProxyInstance.SetterActions`, matched by `set_*` method names |
| `ProxyMembers.Method` | Plain method hooks — stored in `ProxyInstance.MethodActions`, matched by the method name |

### Type: `ProxyHandler` (delegate)

```csharp
public delegate object? ProxyHandler(object?[]? parameters, object? previous);
```

Hook signature used for `start`, `coverage`, and `end` handlers.

#### ProxyHandler.Invoke

**Signature:**
`object? Invoke(object?[]? parameters, object? previous)`

| Parameter | Type | Description |
|---|---|---|
| `parameters` | `object?[]?` | The intercepted member's arguments (boxed). For a setter, `parameters[0]` is the new value |
| `previous` | `object?` | The return value chained from the previous stage: `null` for `start`, the `start` result `R0` for `coverage`, the `coverage`/reflection result `R1` for `end` |

**Returns:** `object?` — the stage result. A non-null `coverage` handler's return value replaces the original member's result.

**Exceptions:** none declared (a handler may throw; the exception propagates out of `ProxyInstance.Invoke` to the proxy caller).

**Example:**
```text
// Source: Examples/AOP/WPF/Demo/MainWindow.xaml.cs
(_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; }
```

### Type: `ProxyEx` (static)

Factory and hook-registration helper.

#### ProxyEx.CreateProxy\<T\>

**Signature:**
`T CreateProxy<T>(this T target) where T : IAspectOriented`

| Parameter | Type | Description |
|---|---|---|
| `target` | `T` | The target instance to wrap (the generated interface type) |

**Returns:** `T` — a `DispatchProxy` implementing `T` that forwards interception to `ProxyInstance`.

**Exceptions:**
| Exception | Condition |
|---|---|
| `InvalidOperationException` | `DispatchProxy.Create<T, ProxyInstance>()` returned `null` |

**Example:**
```text
// Source: generated Aop() extension (Writers/AopWriter.cs)
var p = ProxyEx.CreateProxy<TInterface>(x);
```

**Notes:**
- Calls `DispatchProxy.Create<T, ProxyInstance>()`, sets the internal `_target` / `_targetType` fields via dynamic dispatch, and registers the proxy in `ProxyInstance.ProxyIDs` (proxy → local `Guid`) so later `SetProxy` calls can find it.
- Normally you call the generated `Aop(this T)` extension instead of `CreateProxy` directly.

#### ProxyEx.SetProxy\<T\>

**Signature:**
`void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : class, IAspectOriented`

| Parameter | Type | Description |
|---|---|---|
| `target` | `T` | The proxy instance (returned by `Aop()`), which must be registered in `ProxyInstance.ProxyIDs` |
| `memberType` | `ProxyMembers` | `Getter` / `Setter` / `Method` — selects the hook table |
| `memberName` | `string` | Member name without prefix (e.g. `nameof(TeamViewModel.Name)`, `nameof(TeamViewModel.Reset)`); the implementation prepends `get_` / `set_` for property accessors |
| `start` | `ProxyHandler?` | Runs before the member body; `null` to skip |
| `coverage` | `ProxyHandler?` | Replaces the member body when non-null; `null` to fall back to reflection on the real target |
| `end` | `ProxyHandler?` | Runs after the member body; `null` to skip |

**Returns:** `void`

**Exceptions:** none declared. If `target` is not a registered proxy, the call is a silent no-op.

**Example:**
```text
// Source: Examples/AOP/WPF/Demo/MainWindow.xaml.cs (ConfigureAOP)
p.SetProxy(ProxyMembers.Getter, nameof(TeamViewModel.Name),
    start, null, null);   // fires BEFORE Name is read
p.SetProxy(ProxyMembers.Method, nameof(TeamViewModel.Reset),
    null, coverage, null); // replaces the default Reset() logic
```

**Notes:**
- One `SetProxy` call writes the **whole** `(start, coverage, end)` triple; calling `SetProxy` again for the same member overwrites the stored triple.
- The `target` must be the proxy (not the raw instance); `SetProxy` locates the `ProxyInstance` through `ProxyIDs` → `ProxyInstances`.

### Type: `ProxyInstance` (`DispatchProxy`)

```csharp
public class ProxyInstance : DispatchProxy
{
    public static Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; } = [];
    public static Dictionary<object, Guid> ProxyIDs { get; internal set; } = [];

    protected override object? Invoke(MethodInfo? targetMethod, object?[]? args);
}
```

The single interception point shared by every generated proxy. The internal state (`_target`, `_targetType`, `_localid`) and the three hook tables (`GetterActions`, `SetterActions`, `MethodActions`) are set up by `ProxyEx.CreateProxy` / `SetProxy`.

#### ProxyInstance.ProxyInstances

**Signature:**
`Dictionary<Guid, ProxyInstance> ProxyInstances { get; internal set; }`

| Parameter | Type | Description |
|---|---|---|
| *(none)* | | Static property — the global registry mapping a proxy's local `Guid` to its `ProxyInstance` |

**Returns:** `Dictionary<Guid, ProxyInstance>`

**Notes:** Registered in the `ProxyInstance` constructor and by `ProxyEx.CreateProxy`. Used by `SetProxy` to find the hook tables for a given proxy.

#### ProxyInstance.ProxyIDs

**Signature:**
`Dictionary<object, Guid> ProxyIDs { get; internal set; }`

| Parameter | Type | Description |
|---|---|---|
| *(none)* | | Static property — maps a proxy object to its local `Guid` |

**Returns:** `Dictionary<object, Guid>`

**Notes:** Populated by `ProxyEx.CreateProxy`. `SetPropertyGetter` / `SetPropertySetter` / `SetMethod` use it to resolve the `ProxyInstance` from the `target` argument.

#### ProxyInstance.Invoke

**Signature:**
`object? Invoke(MethodInfo? targetMethod, object?[]? args)` — `protected override`, invoked by `DispatchProxy` on every proxied call.

| Parameter | Type | Description |
|---|---|---|
| `targetMethod` | `MethodInfo?` | The interface method being called |
| `args` | `object?[]?` | The call arguments |

**Returns:** `object?` — the `coverage` handler's result, or the reflection result, or the `end` chain value.

**Dispatch rules:**
- `targetMethod.Name` is `""` / `null` → return `null`.
- Name starts with `get_` → look up `GetterActions`; then `set_` → `SetterActions`; otherwise → `MethodActions`.
- For the matched triple, run: `R0 = start?.Invoke(args, null)`; then `R1 = coverage == null ? _targetType?.GetMethod(Name)?.Invoke(_target, args) : coverage.Invoke(args, R0)`; then `end?.Invoke(args, R1)`; return `R1`.

**Exceptions:** a hook or the reflection call may throw; the exception propagates to the proxy caller (no try/catch inside `Invoke`).

### Type: `Aop` (static)

Proxy-lifecycle infrastructure providing proxy-to-target reverse lookup.

#### Aop.Map

**Signature:**
`void Map(object proxy, object target)`

| Parameter | Type | Description |
|---|---|---|
| `proxy` | `object` | The AOP proxy |
| `target` | `object` | The original instance the proxy wraps |

**Returns:** `void`

**Exceptions:** none declared.

**Example:**
```text
// Source: generated Aop() extension (Writers/AopWriter.cs)
Aop.Map(p, x);   // p = created proxy, x = original instance
```

**Notes:** Stores the pair in a static `ConditionalWeakTable<object, object>`; called by the generated `Aop()` extension. The weak table means the mapping does not keep the target alive beyond its natural lifetime.

#### Aop.GetTarget\<TTarget\>

**Signature:**
`TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class`

| Parameter | Type | Description |
|---|---|---|
| `proxy` | `IAspectOriented` | The AOP proxy to reverse-map |

**Returns:** `TTarget?` — the original target instance, or `null` if the proxy was never mapped.

**Exceptions:** none.

**Example:**
```text
// Source: inferred from runtime (Aop.cs); consistent with demo wiring
var original = Aop.GetTarget<TeamViewModel>(team);
```

**Notes:** Reverse lookup on the `ConditionalWeakTable` — amortized `O(1)`.

### Type: `AopCache` (static)

Generic weak-reference cache for AOP proxies.

#### AopCache.Resolve\<TClass, TInterface\>

**Signature:**
`TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory) where TInterface : class, IAspectOriented where TClass : class`

| Parameter | Type | Description |
|---|---|---|
| `instance` | `TClass` | The target instance keying the cache |
| `factory` | `Func<TClass, TInterface>` | Creates the proxy when the instance has no cached proxy yet |

**Returns:** `TInterface` — the cached proxy if one exists, otherwise the proxy returned by `factory` (which is then stored).

**Exceptions:** none declared.

**Example:**
```text
// Source: generated Aop() extension (Writers/AopWriter.cs)
return AopCache.Resolve<TeamViewModel, TeamViewModel_Demo_Aop>(
    instance,
    static x => { var p = ProxyEx.CreateProxy<TeamViewModel_Demo_Aop>(x); Aop.Map(p, x); return p; });
```

**Notes:**
- Each `(TClass, TInterface)` pair gets its own `ConditionalWeakTable<TClass, TInterface>` via CLR generic specialization (`Entry<TClass, TInterface>`) — no per-class generated cache code is needed.
- The proxy is created once per target and is garbage-collected together with the target (weak keys).
