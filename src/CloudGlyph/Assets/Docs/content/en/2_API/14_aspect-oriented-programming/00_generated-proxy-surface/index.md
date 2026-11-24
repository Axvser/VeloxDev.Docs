# Generated Proxy Surface

The attribute, the marker interfaces, the proxy cache, and the members the generator emits. All runtime types here are compiled under `#if NET`.

## VeloxDev.AspectOriented

### Class: AspectOrientedAttribute

Marks a member for weaving.

**Signature:** `public class AspectOrientedAttribute : Attribute`

**Attribute usage:** `AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field`, `AllowMultiple = false`, `Inherited = false`.

A public property or method needs only this attribute. A field needs a property generator attribute as well (`[VeloxProperty]`), and the generated property becomes the intercepted member.

### Interface: IAspectOriented

Marker for a type the generator can weave. The generated mirror interface implements it; the original class does not.

**Signature:** `public interface IAspectOriented`

### Class: AopCache

One weak proxy cache per `(TClass, TInterface)` pair, specialized by the CLR rather than by generated code.

**Signature:** `public static class AopCache`

| Member | Signature | Description |
|---|---|---|
| `Resolve<TClass, TInterface>` | `static TInterface Resolve<TClass, TInterface>(TClass instance, Func<TClass, TInterface> factory) where TInterface : class, IAspectOriented where TClass : class` | Returns the cached proxy for `instance`, creating it with `factory` on first use. |

`TInterface` carries a `DynamicallyAccessedMembers(PublicParameterlessConstructor)` annotation solely to satisfy `ConditionalWeakTable`'s trimmer requirement; the method never calls `GetOrCreateValue`.

### Class: Aop

The proxy-to-target reverse map.

**Signature:** `public static class Aop`

| Member | Signature | Description |
|---|---|---|
| `Map` | `static void Map(object proxy, object target)` | Registers the proxy-to-target mapping. Called by the generated `Aop()` extension. |
| `GetTarget<TTarget>` | `static TTarget? GetTarget<TTarget>(IAspectOriented proxy) where TTarget : class` | Returns the original object, or `null`. |

## Generated members

For a partial class `CounterViewModel` in namespace `App.ViewModels`, the generator emits:

| Member | Name | Visibility | Notes |
|---|---|---|---|
| Mirror interface | `CounterViewModel_App_ViewModels_Aop` in `VeloxDev.AopInterfaces` | `public interface` | Implements `IAspectOriented` and `IAopHookTarget`; mirrors every woven member. |
| Proxy | `CounterViewModel_App_ViewModels_AopProxy` | `internal sealed class` | Implements the mirror interface. The name is `{Interface}Proxy`; not for direct use. |
| Extension class | `CounterViewModel_App_ViewModels_AopExtensions` in `VeloxDev.AspectOriented` | `public static class` | Declares `Aop()`. |
| Extension method | `public static {Interface} Aop(this {Class} instance)` | `public static` | Resolves through `AopCache.Resolve`, constructs the proxy once, and calls `Aop.Map`. |

The namespace segment replaces `.` with `_`; a class in the global namespace uses `Global`. The generated files are `{Class}_{Namespace}_AOP.g.cs`, `{Class}_{Namespace}_AopExt.g.cs`, `{Interface}.g.cs` and `{Interface}Proxy.g.cs`.

**Member keys.** A property is split into `get_{Name}` and `set_{Name}`; a method uses its own name. The proxy's `IAopHookTarget.SetHooks` accepts only these keys and an unknown key throws.

## Example

```csharp
using System;
using VeloxDev.AspectOriented;

var counter = new CounterViewModel();
var proxy = counter.Aop();          // VeloxDev.AopInterfaces.CounterViewModel_Global_Aop

Console.WriteLine(proxy.Value);     // reads through the proxy
proxy.Value = 7;                    // writes through the proxy

CounterViewModel? original = Aop.GetTarget<CounterViewModel>(proxy);
Console.WriteLine(ReferenceEquals(counter, original));   // True
```

The interface type is generated at build time, so name it explicitly or keep `var`. See [Hooks and installation](../01_hooks-and-installation/index.md) for installing behavior.

## Notes

- A call on `counter` directly bypasses every hook; only the proxy runs them.
- The proxy is cached per target instance. Two `Aop()` calls on the same object return the same proxy.
- The generated proxy is ordinary C# in the consumer's assembly. The previous runtime `DispatchProxy` implementation required `Reflection.Emit` and `RequiresDynamicCode`; this design has neither.
