# AOP runtime — `AspectOrientedAttribute` & `IAspectOriented`

## Type: `AspectOrientedAttribute`

Declared in `Src/Core/VeloxDev.Core/AspectOriented/AspectOrientedAttribute.cs`:

```csharp
[AttributeUsage(AttributeTargets.Method | AttributeTargets.Property | AttributeTargets.Field,
    AllowMultiple = false, Inherited = false)]
public class AspectOrientedAttribute : Attribute
{
}
```

### Constructor: `AspectOrientedAttribute`

**Signature:** `AspectOrientedAttribute()`

No parameters, no state.

**Exceptions:** none.

### Semantics

- **Targets:** methods, properties, and fields only.
- **Detection is textual:** `AnalizeHelper.IsAopClass` matches the attribute's simple name `AspectOriented`, and `AopSurface` compares `att.ToString() == "AspectOriented"` per member. Write `[AspectOriented]` unqualified.
- **Class must be `partial`:** the discovery filter only accepts partial class declarations (`Analizer.Filters.IsCandidateClass`). A non-partial class is skipped without a diagnostic.
- **One marked member makes the whole class a target.** All marked members across all partial declarations are collected (`AnalizeHelper.Members`).
- **Exposure rules:** methods must be `public`; properties need a public accessor; fields surface only when a property-generating attribute (`[VeloxProperty]`, `[Observable]`) is present as well. See [Generated API](../../01_generated-api/index.md).

Demo marking, `Examples/AOP/WPF/Demo/TeamViewModel.cs`:

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

The two fields surface as the `Name` and `Members` properties; `Reset` surfaces as a method.

## Type: `IAspectOriented`

Declared in `Src/Core/VeloxDev.Core/Interfaces/AspectOriented/IAspectOriented.cs`:

```csharp
public interface IAspectOriented
{
}
```

An empty marker. Its roles:

- **Base contract** of every generated AOP interface.
- **Constraint** on `ProxyEx.SetProxy<T>` and `AopCache.Resolve<TClass, TInterface>`.
- **Parameter type** of `Aop.GetTarget<TTarget>` (whose own constraint is `TTarget : class`).

The generated interface also inherits `IAopHookTarget`, which has a member; that is why the user's own class does **not** implement either interface — the proxy class does. See [Generated proxy](../03_proxy-class/index.md).
