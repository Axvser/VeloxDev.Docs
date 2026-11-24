# Aspect-Oriented Programming

`VeloxDev.AspectOriented` provides before / replace / after hooks around a property getter, a property setter or a method. The generator emits a mirror interface and a compile-time proxy; no runtime code generation is involved. The runtime half is compiled only when the `NET` symbol is defined, so the consumer must target **.NET 5.0 or later** (`netstandard2.0` and `netframework4.6.1` do not carry the namespace).

## Type groups

| Group | Types | Page |
|---|---|---|
| Generated proxy surface | `AspectOrientedAttribute`, `IAspectOriented`, the generated interface / proxy / `Aop()` extension, `AopCache`, `Aop` | [Generated proxy surface](00_generated-proxy-surface/index.md) |
| Hooks and installation | `ProxyHandler`, `AspectHooks`, `IAopHookTarget`, `ProxyMembers`, `ProxyEx` | [Hooks and installation](01_hooks-and-installation/index.md) |

## How a call flows

1. `[AspectOriented]` on a public property or method (or on a `[VeloxProperty]` field) makes the generator emit a mirror interface and a proxy that implements it.
2. `counter.Aop()` returns the cached proxy. Calls on the proxy run the installed hooks; calls on the original object bypass them.
3. `proxy.SetProxy(memberKind, memberName, start, coverage, end)` installs one member's three stages. Installing again replaces all three.
4. For a getter the handler's `parameters` is `null`; for a setter its single element is the value being written; for a method they are the method's own arguments.

See [Aspect-Oriented Programming quick start](../../1_QuickStart/14_aspect-oriented-programming/index.md) for a complete console program.

## Limits

- An overloaded method cannot be hooked: the interception key is the bare method name.
- A public property is required; a non-public property or method is not woven.
- A `[VeloxProperty]` field is supported only alongside `[AspectOriented]`, and the intercepted member is the generated property (`_name` becomes `Name`).
