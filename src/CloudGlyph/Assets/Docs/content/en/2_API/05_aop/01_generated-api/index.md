# AOP — Generated API

Two incremental generators in `Src/Generators/VeloxDev.Core.Generator` produce everything the caller touches:

| Generator | Source | Emits |
|---|---|---|
| `VeloxDev.Generators.AopSurface` | `AopSurface.cs` | the mirror interface and the proxy class (two files) |
| `VeloxDev.Generators.AopProxy` | `AopProxy.cs` → `Writers/AopWriter.cs` | the `Aop()` extension |

Nothing is injected into the user's class. `AopWriter.GenerateBaseTypes` and `GenerateBaseInterfaces` return empty arrays, and `GenerateBody` returns an empty string — the old partial-class glue no longer exists.

## Discovery

`Analizer.Filters.Targets` uses `ForAttributeWithMetadataName("VeloxDev.AspectOriented.AspectOrientedAttribute", ...)`, and `IsCandidateClass` accepts only **partial** class declarations. `AnalizeHelper.IsAopClass` then re-checks the members across every partial declaration by the attribute's simple name. Consequences:

- the class must be `partial`;
- write `[AspectOriented]`, not a qualified or aliased form;
- a type split across partial files is generated once, with members collected from all parts.

## Naming

`Base/AopNames.cs` is the single naming algorithm:

```csharp
internal const string InterfaceNamespace = "VeloxDev.AopInterfaces";

internal static string InterfaceFor(INamedTypeSymbol symbol)
    => $"{symbol.Name}_{Segment(symbol)}_Aop";

internal static string ProxyFor(INamedTypeSymbol symbol)
    => InterfaceFor(symbol) + "Proxy";

internal static string Segment(INamedTypeSymbol symbol)
    => symbol.ContainingNamespace is null || symbol.ContainingNamespace.IsGlobalNamespace
        ? "Global"
        : symbol.ContainingNamespace.ToDisplayString().Replace('.', '_');
```

Examples: `Demo.TeamViewModel` → `TeamViewModel_Demo_Aop`; `Demo.ViewModels.TeamViewModel` → `TeamViewModel_Demo_ViewModels_Aop`; a global-namespace class → `{Class}_Global_Aop`.

## Generated interface

File hint `{Interface}.g.cs`, namespace `VeloxDev.AopInterfaces`. For `AopFixture` (namespace `VeloxDev.Core.Test.AspectOriented`), the emitted declaration is:

```csharp
public interface AopFixture_VeloxDev_Core_Test_AspectOriented_Aop : global::VeloxDev.AspectOriented.IAspectOriented, global::VeloxDev.AspectOriented.IAopHookTarget
{
    public string Title { get; set; }

    public int Add(int a, int b);
    public void Ping();
    public string Echo(string value);
}
```

Member rules, from `AopSurface.GenerateSource`:

| Source member | Condition | Interface member |
|---|---|---|
| Field | `[AspectOriented]` plus an attribute whose text contains `Observable` or `Property` | `get`/`set` property, named by dropping a leading `_` and upper-casing the next character (`_name` → `Name`) |
| Property | `public` and `[AspectOriented]`; getter mirrored when a public getter exists or no getter is declared; setter only if a public setter exists | the same property |
| Method | `public` and `[AspectOriented]` | the same method with fully qualified parameter and return types |

A property's getter and setter are independent members and get independent hook sets.

## Generated proxy

File hint `{Interface}Proxy.g.cs`, namespace `VeloxDev.AopInterfaces`:

```csharp
internal sealed class AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy : AopFixture_VeloxDev_Core_Test_AspectOriented_Aop
{
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Add;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Ping;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_Echo;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_get_Title;
    private global::VeloxDev.AspectOriented.AspectHooks? _hooks_set_Title;

    private readonly global::VeloxDev.Core.Test.AspectOriented.AopFixture _target;

    internal AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy(global::VeloxDev.Core.Test.AspectOriented.AopFixture target) => _target = target;
    // members and SetHooks ...
}
```

It is `internal` and `sealed`; callers only see the interface type returned by `Aop()`. Its behavior and exception surface are documented on [Generated proxy](../00_aspect-oriented/03_proxy-class/index.md).

## Generated extension

File hint `{Class}_{NamespaceSegment}_AopExt.g.cs`, namespace `VeloxDev.AspectOriented`, class `{Class}_{NamespaceSegment}_AopExtensions`. Actual emitted output for `AopFixture`:

```csharp
namespace VeloxDev.AspectOriented;

public static class AopFixture_VeloxDev_Core_Test_AspectOriented_AopExtensions
{
    public static global::VeloxDev.AopInterfaces.AopFixture_VeloxDev_Core_Test_AspectOriented_Aop Aop(this global::VeloxDev.Core.Test.AspectOriented.AopFixture instance)
        => global::VeloxDev.AspectOriented.AopCache.Resolve<
            global::VeloxDev.Core.Test.AspectOriented.AopFixture,
            global::VeloxDev.AopInterfaces.AopFixture_VeloxDev_Core_Test_AspectOriented_Aop>(
            instance,
            static x =>
            {
                var p = new global::VeloxDev.AopInterfaces.AopFixture_VeloxDev_Core_Test_AspectOriented_AopProxy(x);
                global::VeloxDev.AspectOriented.Aop.Map(p, x);
                return p;
            });
}
```

| Parameter | Type | Description |
|---|---|---|
| `instance` | the model class | Target instance |

**Returns:** the generated interface — one cached proxy per instance via `AopCache.Resolve`.

**Generated output paths:** by default Roslyn only returns these sources to the compiler. Set `EmitCompilerGeneratedFiles=true` to inspect them under `obj/<Configuration>/<TFM>/generated/VeloxDev.Core.Generator/VeloxDev.Generators.{AopSurface,AopProxy}/`. The snippets above are the emitted files from `Src/Core/VeloxDev.Core.Test` (`obj/Debug/net10.0/generated/...`).

## Limits (source-verified)

| Shape | Result | Cause |
|---|---|---|
| Non-partial class | Nothing generated, no diagnostic | `IsCandidateClass` requires `partial` |
| Overloaded methods | Generated code does not compile | one hook field and one `switch` case per bare name |
| Generic method | Generated interface loses the type-parameter list | `MethodDeclaration(...)` is created without `WithTypeParameterList` |
| `ref` / `out` / `in` parameter | Generated call omits the modifier | the proxy calls `_target.M(arg1, ...)` with plain identifiers |
| Non-public method, or non-public accessor | Not mirrored | `public` filters in `AopSurface` |

Keep intercepted members instance members with unique names and plain by-value parameters.
