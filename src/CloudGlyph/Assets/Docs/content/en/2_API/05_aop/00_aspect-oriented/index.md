# AOP runtime — namespace `VeloxDev.AspectOriented` (`#if NET`)

Every file listed here is wrapped in `#if NET`, so the types exist in the `net5.0` and `net8.0` assets of `VeloxDev.Core`, not in `netstandard2.0`, `netframework4.6.1`, or `netcoreapp3.0`.

The runtime is deliberately small because the interception itself is generated code, not a runtime factory. The generated proxy class implements the generated interface, and each member either calls the target directly (no hooks) or runs the hook pipeline. The runtime types supply the contracts (`AspectHooks`, `ProxyHandler`, `IAopHookTarget`), the registration helper (`ProxyEx`), and the lifecycle maps (`Aop`, `AopCache`).

## Sub-pages

| Page | Contents |
|---|---|
| [AspectOrientedAttribute & IAspectOriented](00_attribute-and-marker/index.md) | The declaration surface and the marker contract |
| [ProxyMembers, ProxyHandler, AspectHooks, IAopHookTarget](01_proxy-members-handler/index.md) | The hook contracts and the interception key |
| [ProxyEx](02_proxyex/index.md) | `SetProxy` — the only public registration method |
| [Generated proxy](03_proxy-class/index.md) | What the emitted class does on every call, and the exceptions it can throw |
| [Aop & AopCache](04_proxy-lifecycle/index.md) | Reverse mapping and per-instance caching |

The user-facing entry point `Aop(this T)` is generated, not part of this namespace; see [Generated API](../01_generated-api/index.md).
