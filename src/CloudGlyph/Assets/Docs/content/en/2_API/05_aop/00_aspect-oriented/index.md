# AOP runtime — namespace `VeloxDev.AspectOriented` (`#if NET`)

Every runtime source file is compiled under `#if NET`, so the types below exist only in the `net5.0` target of `VeloxDev.Core` — its sole `NET` target. A project referencing that asset on .NET 5.0 or later can use the feature; both demos build against it (`net9.0` for the Avalonia demo, `net9.0-windows` for the WPF demo).

The runtime sits on top of `System.Reflection.DispatchProxy` and forms one interception core shared by every generated proxy:

- `AspectOrientedAttribute` marks the members of a `partial` class that should be reachable through a proxy, and `IAspectOriented` is the marker contract every generated AOP interface inherits.
- `ProxyMembers` selects which hook table a registration targets, and `ProxyHandler` is the signature shared by the `start`, `coverage` and `end` hooks.
- `ProxyEx.CreateProxy` (normally reached through the generated `Aop()`) creates a `DispatchProxy` backed by a `ProxyInstance`; `ProxyEx.SetProxy` attaches a `(start, coverage, end)` hook triple to one member.
- `Aop` keeps the weak proxy-to-target map used by reverse lookup, and `AopCache` caches one proxy per target instance.

## Sub-pages

- [AspectOrientedAttribute & IAspectOriented](00_attribute-and-marker/index.md) — the declaration surface.
- [ProxyMembers & ProxyHandler](01_proxy-members-handler/index.md) — how a hook target is selected, and the hook signature.
- [ProxyEx](02_proxyex/index.md) — proxy creation and hook registration.
- [ProxyInstance](03_proxyinstance/index.md) — the shared `DispatchProxy` and its dispatch rules.
- [Aop & AopCache](04_proxy-lifecycle/index.md) — proxy-to-target reverse lookup and the per-instance proxy cache.

The user-facing entry point `Aop(this T)` is generated, not part of this namespace; see [Generated API](../01_generated-api/index.md).
