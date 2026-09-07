# AOP — API Reference

Feature: dynamic, aspect-oriented proxies for `.NET` targets. `AspectOrientedAttribute` marks members of a `partial` class; the Roslyn source generators emit an AOP proxy interface plus an `Aop(this T)` extension; the runtime namespace `VeloxDev.AspectOriented` builds `DispatchProxy` proxies and lets you attach `start` / `coverage` / `end` hooks per member, observing or replacing the original logic without modifying the model source.

**Public surface at a glance**

- Runtime — namespace `VeloxDev.AspectOriented` (`#if NET`): `AspectOrientedAttribute`, `IAspectOriented`, enum `ProxyMembers`, delegate `ProxyHandler`, static `ProxyEx`, `ProxyInstance : DispatchProxy`, static `Aop`, static `AopCache`.
- Generated — interface `VeloxDev.AopInterfaces.{Class}_{Ns}_Aop` and the `{Class}_{Ns}_AopExtensions.Aop(this T)` entry point.

**Evidence**

- Demo: `Examples/AOP/WPF/Demo`, `Examples/AOP/Avalonia/Demo`.
- Runtime source: `Src/Core/VeloxDev.Core/AspectOriented/*.cs` and `Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`.
- Generator source: `Src/Generators/VeloxDev.Core.Generator/AopInterface.cs`, `AopProxy.cs`, `Writers/AopWriter.cs`.
- **Test note:** no AOP-specific suite exists under `VeloxDev.Core.Test` at refresh time (the feature inventory's `Demo + Test` row is stale on the Test half). The surface below is verified against the demos and the runtime / generator sources.

## API — sections

- [AOP runtime — namespace `VeloxDev.AspectOriented`](00_aspect-oriented/index.md) — the marking attribute, marker interface, hook contracts, proxy factory / instance and lifecycle cache.
- [Generated API (source generator)](01_generated-api/index.md) — the compile-time emitted AOP interface, the partial-class glue and the `Aop(this T)` extension.
