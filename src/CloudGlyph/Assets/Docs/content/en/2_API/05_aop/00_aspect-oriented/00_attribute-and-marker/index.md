# AOP runtime — `AspectOrientedAttribute` & `IAspectOriented`

The declaration surface of the AOP feature: `AspectOrientedAttribute` marks which members of a `partial` class should be exposed through a dynamic proxy, and `IAspectOriented` is the empty marker contract that every generated AOP interface inherits.

## Type: `AspectOrientedAttribute`

`Src/Core/VeloxDev.Core/AspectOriented/AspectOrientedAttribute.cs`:

```csharp
namespace VeloxDev.AspectOriented
{
    [AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
        AllowMultiple = false, Inherited = false)]
    public class AspectOrientedAttribute : Attribute
    {
    }
}
```

### Constructor: `AspectOrientedAttribute`

**Signature:** `AspectOrientedAttribute()`

| Parameter | Type | Description |
|---|---|---|
| *(none)* | | Parameterless constructor (the attribute carries no state) |

**Returns:** `AspectOrientedAttribute`

**Exceptions:** none.

### Attribute semantics

- **Targets:** `Method`, `Property` or `Field` only; `AllowMultiple = false`, `Inherited = false`.
- **Detection:** the generators match the attribute by its simple name `AspectOriented` (`Base/AnalizeHelper.IsAopClass`, `Writers/AopWriter.ReadAopConfig`). As soon as one member of a class carries it, the whole containing `partial` class becomes an AOP target and the generators emit its AOP interface, a partial-class glue and the `Aop(this T)` extension (see [Generated API](../../01_generated-api/index.md)).
- **Exposure:** members that the generator surfaces on the proxy interface must be `public` (a `private` field is only surfaced when a `[VeloxProperty]` / `[Observable]` generator turns it into a public property).

Demo-verified marking, `Examples/AOP/WPF/Demo/TeamViewModel.cs`:

```csharp
public partial class TeamViewModel
{
    [VeloxProperty][AspectOriented] private string _name = string.Empty;
    [VeloxProperty][AspectOriented] private ObservableCollection<MemberViewModel> _members = [];

    [AspectOriented]
    public void Reset()
    {
        Name = string.Empty;
        Members.Clear();
    }
}
```

Here the two fields also carry `[VeloxProperty]` (MVVM), so they surface on the proxy interface as the `Name` and `Members` properties; the two `[AspectOriented]` public methods (`Reset`, plus `AOP_OnMemberAdded` / `AOP_OnMemberRemoved` later in the file) are exposed directly.

## Type: `IAspectOriented`

`Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`:

```csharp
namespace VeloxDev.AspectOriented
{
    public interface IAspectOriented
    {
    }
}
```

Empty marker interface with no members. Its roles:

- **Base contract** of every generated AOP interface — the generator writes the base type `global::VeloxDev.AspectOriented.IAspectOriented`.
- **Generic constraint** shared by `ProxyEx.CreateProxy<T>`, `ProxyEx.SetProxy<T>`, `Aop.GetTarget<TTarget>` and `AopCache.Resolve<TClass, TInterface>` (see [proxyex](../02_proxyex/index.md) and [proxy-lifecycle](../04_proxy-lifecycle/index.md)).

Related pages: [ProxyMembers & ProxyHandler](../01_proxy-members-handler/index.md), [ProxyEx](../02_proxyex/index.md), [ProxyInstance](../03_proxyinstance/index.md).
