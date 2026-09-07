# AOP runtime — `ProxyEx` (static)

`Src/Core/VeloxDev.Core/AspectOriented/ProxyEx.cs`. Static factory and hook-registration helper. It also declares the `ProxyMembers` enum (see [ProxyMembers & ProxyHandler](../01_proxy-members-handler/index.md)).

## ProxyEx.CreateProxy\<T\>

**Signature:** `T CreateProxy<T>(this T target) where T : IAspectOriented`

| Parameter | Type | Description |
|---|---|---|
| `target` | `T` | The instance to wrap. `T` is the generated AOP interface type, so the returned proxy can be typed as that interface |

**Returns:** `T` — a `DispatchProxy` implementing `T` whose interception is forwarded to a fresh `ProxyInstance`.

**Exceptions:**

| Exception | Condition |
|---|---|
| `InvalidOperationException` | `DispatchProxy.Create<T, ProxyInstance>()` returned `null` |

**Implementation notes:**

- Runs `DispatchProxy.Create<T, ProxyInstance>()`; the proxy's `ProxyInstance` constructor already generated a local `Guid` and registered it in `ProxyInstance.ProxyInstances`.
- Sets the internal `_target` (= `target`) and `_targetType` (= `typeof(T)`, the proxy interface) fields through dynamic dispatch, then registers `proxy → _localid` in `ProxyInstance.ProxyIDs`.
- This is exactly the factory body the generated `Aop()` extension passes to `AopCache.Resolve` (the lambda emitted by `Writers/AopWriter.WriteExtension` for the WPF demo's `Demo.TeamViewModel`):

```csharp
// Source: emitted by Src/Generators/VeloxDev.Core.Generator/Writers/AopWriter.cs (WriteExtension)
static x =>
{
    var p = global::VeloxDev.AspectOriented.ProxyEx.CreateProxy<global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop>(x);
    global::VeloxDev.AspectOriented.Aop.Map(p, x);
    return p;
}
```

**Notes:** normally you call the generated `Aop(this T)` extension rather than `CreateProxy` directly; see [Generated API](../../01_generated-api/index.md).

## ProxyEx.SetProxy\<T\>

**Signature:** `void SetProxy<T>(this T target, ProxyMembers memberType, string memberName, ProxyHandler? start, ProxyHandler? coverage, ProxyHandler? end) where T : class, IAspectOriented`

| Parameter | Type | Description |
|---|---|---|
| `target` | `T` | The proxy instance (returned by `Aop()` / `CreateProxy`). It must be registered in `ProxyInstance.ProxyIDs`, otherwise the call is a silent no-op |
| `memberType` | `ProxyMembers` | `Getter` / `Setter` / `Method` — selects the hook table |
| `memberName` | `string` | The member name without a `get_` / `set_` prefix (e.g. `nameof(TeamViewModel.Name)`, `nameof(TeamViewModel.Reset)`). Property names are dispatched under `get_` / `set_` keys, methods under the bare name |
| `start` | `ProxyHandler?` | Runs before the member body; `null` to skip |
| `coverage` | `ProxyHandler?` | Non-null replaces the member body; `null` falls back to reflecting the real target member |
| `end` | `ProxyHandler?` | Runs after the member body; `null` to skip |

**Returns:** `void`

**Exceptions:** none declared. If `target` is not a registered proxy, the call is a silent no-op (the underlying `SetPropertyGetter` / `SetPropertySetter` / `SetMethod` return `source` unchanged).

**Implementation notes:**

- Dispatches on `memberType` to the internal `SetPropertyGetter` / `SetPropertySetter` / `SetMethod`, which resolve `ProxyInstance.ProxyIDs[target]` then `ProxyInstance.ProxyInstances[id]` and store the whole `(start, coverage, end)` triple under the dispatched name key.
- Calling `SetProxy` again for the same member overwrites the stored triple (a `ContainsKey` branch updates the entry).

Demo-verified usage, `Examples/AOP/WPF/Demo/MainWindow.xaml.cs` (`ConfigureAOP`):

```csharp
var p = data.Aop();

// Before hook: fires before Name is read
p.SetProxy(ProxyMembers.Getter,
    nameof(TeamViewModel.Name),
    (_, _) => { MessageBox.Show($"a read operation happened at [{DateTime.Now}]"); return null; },
    null,
    null);

// Override original logic: cancels the default Reset() behavior
p.SetProxy(ProxyMembers.Method,
    nameof(TeamViewModel.Reset),
    null,
    (_, _) => { MessageBox.Show($"the default Reset() has been cancelled"); return null; },
    null);
```

Related pages: [ProxyInstance](../03_proxyinstance/index.md) stores and dispatches the registered triples; [Aop & AopCache](../04_proxy-lifecycle/index.md) explains `Aop()`'s caching.
