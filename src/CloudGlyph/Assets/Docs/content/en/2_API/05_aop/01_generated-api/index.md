# AOP — Generated API (source generator)

Emitted at compile time for every `partial` class that has at least one member carrying `[AspectOriented]` (detection in `Base/AnalizeHelper.IsAopClass` and `Writers/AopWriter.ReadAopConfig`). Three artifacts come from the generators in `Src/Generators/VeloxDev.Core.Generator`:

| Artifact | Emitted by | File hint |
|---|---|---|
| AOP proxy interface | `AopInterface` | `{Class}_{Ns}_Aop.g.cs` |
| Partial-class glue | `AopProxy` → `AopWriter.Write` | `{Class}_{Ns}_AOP.g.cs` |
| `Aop(this T)` extension | `AopProxy` → `AopWriter.WriteExtension` | `{Class}_{Ns}_AopExt.g.cs` |

`Ns` is the class's containing namespace with `.` replaced by `_` (for a file-scoped `Demo.TeamViewModel`, `Ns = Demo`).

## Generated type: `VeloxDev.AopInterfaces.{Class}_{Ns}_Aop`

Naming rule from `AopInterface.cs`:

```csharp
string interfaceName = $"{classDeclaration.Identifier.Text}_{classSymbol.ContainingNamespace.ToDisplayString().Replace('.', '_')}_Aop";
```

`public`, inherits `global::VeloxDev.AspectOriented.IAspectOriented`. Examples: `Demo.TeamViewModel` → `TeamViewModel_Demo_Aop`; `Demo.ViewModels.TeamViewModel` → `TeamViewModel_Demo_ViewModels_Aop`.

**Generated members** (one public member per qualifying member of the class, in source order by kind):

- **Fields** that carry both `[AspectOriented]` and an attribute whose simple name contains `Observable` or `Property` (for example `[VeloxProperty]`, `[Observable]`) become a get/set property. The name drops a leading `_` and upper-cases the next character (`Base/AnalizeHelper.GetPropertyNameByFieldName`): `_name` → `Name`.
- **Public properties** annotated `[AspectOriented]` become a property: the getter is kept when there is no getter or the getter is public; the setter only when a public setter exists.
- **Public methods** annotated `[AspectOriented]` become a method; parameter and return types are rewritten to their fully-qualified symbol display (`void` stays `void`).

Readable rendering of what `AopInterface` emits for the WPF demo class `Demo.TeamViewModel` (the generator writes fully-qualified type names resolved by the semantic model):

```csharp
public interface TeamViewModel_Demo_Aop : global::VeloxDev.AspectOriented.IAspectOriented
{
    string Name { get; set; }
    ObservableCollection<MemberViewModel> Members { get; set; }
    void Reset();
    void AOP_OnMemberAdded(object? sender, NotifyCollectionChangedEventArgs e);
    void AOP_OnMemberRemoved(object? sender, NotifyCollectionChangedEventArgs e);
}
```

`Name` / `Members` come from the two `[VeloxProperty][AspectOriented]` fields of `TeamViewModel.cs`; `Reset`, `AOP_OnMemberAdded` and `AOP_OnMemberRemoved` from the `[AspectOriented]` public methods. This is the type passed to `DispatchProxy.Create<T, ProxyInstance>()`, which is why the runtime can intercept the `get_*` / `set_*` / method names (`AspectOrientedAttribute` is documented in [attribute-and-marker](../00_aspect-oriented/00_attribute-and-marker/index.md)).

## Generated partial class (file `{Class}_{Ns}_AOP.g.cs`)

`AopProxy` (namespace `VeloxDev.Generators`) collects every class reaching the filter and, when `AopWriter.CanWrite()` is true (an `[AspectOriented]` member exists), emits a source through the inherited `WriterBase.Write()`: the containing namespace and the class re-declared as `partial`, its base-type list preserved from the symbol plus the generated AOP interface (`AopWriter.GenerateBaseInterfaces`), with an empty body.

Real contract from `Writers/AopWriter.cs`:

```csharp
public override string[] GenerateBaseInterfaces() =>
[
    $"{NAMESPACE_VELOX_AOP}.{Syntax?.Identifier.Text}_{Symbol?.ContainingNamespace.ToDisplayString().Replace('.', '_')}_Aop"
];
```

where `NAMESPACE_VELOX_AOP = "global::VeloxDev.AopInterfaces"` (`Writers/WriterBase.cs`). Effect: the compiler sees the class implement its generated interface, so the members living in the user's own `partial` part satisfy the interface contract — the model never has to declare the interface itself.

## Generated extension: `Aop(this T)` in `{Class}_{Ns}_AopExtensions`

`AopWriter.WriteExtension()` emits file `{Class}_{Ns}_AopExt.g.cs` in namespace `VeloxDev.AspectOriented`. Concrete output for the WPF demo's `Demo.TeamViewModel`:

```csharp
namespace VeloxDev.AspectOriented;

public static class TeamViewModel_Demo_AopExtensions
{
    public static global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop Aop(
        this global::Demo.TeamViewModel instance)
        => global::VeloxDev.AspectOriented.AopCache.Resolve<
            global::Demo.TeamViewModel,
            global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop>(
            instance,
            static x =>
            {
                var p = global::VeloxDev.AspectOriented.ProxyEx.CreateProxy<global::VeloxDev.AopInterfaces.TeamViewModel_Demo_Aop>(x);
                global::VeloxDev.AspectOriented.Aop.Map(p, x);
                return p;
            });
}
```

| Parameter | Type | Description |
|---|---|---|
| `instance` | `T` (the model class) | The target instance to wrap |

**Returns:** `{Class}_{Ns}_Aop` — the cached proxy (one per instance, via `AopCache.Resolve`), typed as the generated interface.

**Notes:**

- Resolves through `AopCache.Resolve<TClass, TInterface>` (see [Aop & AopCache](../00_aspect-oriented/04_proxy-lifecycle/index.md)); the factory it runs calls `ProxyEx.CreateProxy<I>(x)` and `Aop.Map(p, x)`.
- Demo usage, `Examples/AOP/WPF/Demo/MainWindow.xaml.cs`:

```csharp
var team = _teamData.Aop();     // cached proxy
_ = _teamData.Aop().Name;       // getter intercepted (start hook fires)
_teamData.Aop().Reset();        // method intercepted (coverage replaces body)
```

Related pages: [AOP runtime overview](../00_aspect-oriented/index.md).
