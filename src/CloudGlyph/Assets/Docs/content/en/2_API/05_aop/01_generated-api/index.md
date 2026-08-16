# AOP — Generated API (source generator)

Produced at compile time by `AopInterface` / `AopProxy` (`Src/Generators/VeloxDev.Core.Generator`). The concrete names depend on the class identifier and its containing namespace.

### Type: `VeloxDev.AopInterfaces.{ClassName}_{Namespace}_Aop`

**Signature:** `public interface {ClassName}_{Namespace}_Aop : IAspectOriented` — e.g. `TeamViewModel_Demo_Aop` for `Demo.TeamViewModel`.

**Members:** one public member declaration for each interceptable `[AspectOriented]` member of the class:
- fields marked `[VeloxProperty]` / `[Observable]` → a get/set property;
- public `[AspectOriented]` properties → a get/set property (getter/setter kept only where the original accessor is public);
- public `[AspectOriented]` methods → a method with the fully-qualified parameter/return types.

**Notes:** The interface is what `DispatchProxy.Create<T, ProxyInstance>()` proxies, so the runtime can intercept `get_*` / `set_*` / plain-method names.

### Extension: `Aop(this T instance)`

**Signature:** `public static {ClassName}_{Namespace}_Aop Aop(this T instance)` in namespace `VeloxDev.AspectOriented` — e.g. `public static TeamViewModel_Demo_Aop Aop(this TeamViewModel instance)`.

| Parameter | Type | Description |
|---|---|---|
| `instance` | `T` | The target instance |

**Returns:** `{ClassName}_{Namespace}_Aop` — the cached (or newly created) proxy.

**Example:**
```text
// Source: Examples/AOP/WPF/Demo/MainWindow.xaml.cs
var team = _teamData.Aop();        // cached proxy
_ = _teamData.Aop().Name;          // getter intercepted
_teamData.Aop().Reset();           // method intercepted
```

**Notes:**
- Resolves the proxy through `AopCache.Resolve<T, I>` (one per pair, weak table).
- The factory passed to `Resolve` calls `ProxyEx.CreateProxy<I>(x)` and `Aop.Map(p, x)`.
- The generated class is named `{ClassName}_{Namespace}_AopExtensions` (e.g. `TeamViewModel_Demo_AopExtensions`); it is `public static`.
