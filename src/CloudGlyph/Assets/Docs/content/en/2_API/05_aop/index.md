# AOP — API Reference

Aspect-oriented interception for `.NET 5+` targets. `AspectOrientedAttribute` marks members of a `partial` class; the source generators emit a mirror interface, a sealed proxy class, and a cached `Aop()` extension. Runtime hooks are installed per member with `ProxyEx.SetProxy` and run as a `start` / `coverage` / `end` pipeline.

## Public surface

**Runtime — namespace `VeloxDev.AspectOriented` (`#if NET`)**

| Type | Kind | Role |
|---|---|---|
| `AspectOrientedAttribute` | attribute | Marks the members to mirror |
| `IAspectOriented` | interface | Empty marker implemented by every generated interface |
| `ProxyMembers` | enum | `Getter`, `Setter`, `Method` — selects the accessor/key |
| `ProxyHandler` | delegate | `object? (object?[]? parameters, object? previous)` |
| `AspectHooks` | sealed class | One `(start, coverage, end)` set |
| `IAopHookTarget` | interface | `SetHooks(string memberKey, AspectHooks? hooks)` — implemented by the generated proxy |
| `ProxyEx` | static class | `SetProxy` — installs a hook set |
| `Aop` | static class | `Map` / `GetTarget` — proxy-to-target reverse map |
| `AopCache` | static class | `Resolve` — one proxy per target instance |

**Generated — namespace `VeloxDev.AopInterfaces`, plus an extension in `VeloxDev.AspectOriented`**

| Artifact | Name |
|---|---|
| Interface | `{Class}_{NamespaceSegment}_Aop : IAspectOriented, IAopHookTarget` |
| Proxy | `internal sealed class {Interface}Proxy : {Interface}` |
| Extension | `{Class}_{NamespaceSegment}_AopExtensions.Aop(this Class)` |

## Sections

- [AOP runtime — namespace `VeloxDev.AspectOriented`](00_aspect-oriented/index.md) — the marking attribute, hook contracts, registration, the emitted proxy, and the lifecycle cache.
- [Generated API](01_generated-api/index.md) — naming, member rules, emitted artifacts, and limits.

## Evidence

- **Tests:** `Src/Core/VeloxDev.Core.Test/AspectOriented/` — `AopFixture.cs`, `AopProxyTests.cs` (13 tests, all passing).
- **Demos:** `Examples/AOP/WPF/Demo`, `Examples/AOP/Avalonia/Demo`.
- **Runtime:** `Src/Core/VeloxDev.Core/AspectOriented/*.cs`, `Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`.
- **Generator:** `Src/Generators/VeloxDev.Core.Generator/AopSurface.cs`, `AopProxy.cs`, `Base/AopNames.cs`, `Writers/AopWriter.cs`.

All members below are verified against those files; the tests pin stage order, replacement, caching, error behavior, and collectability.
