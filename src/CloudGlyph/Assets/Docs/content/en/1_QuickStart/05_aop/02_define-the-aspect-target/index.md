# Define the Aspect Target

Declare a **`partial` class** and mark the members to intercept. The class must be `partial`: the generator only considers partial class declarations, and a non-partial class is skipped silently.

```csharp
using VeloxDev.AspectOriented;

namespace AopQuickStart;

public partial class Counter
{
    [AspectOriented]
    public int Total { get; set; }

    [AspectOriented]
    public int Add(int a, int b)
    {
        Total = a + b;
        return Total;
    }

    [AspectOriented]
    public void Reset()
    {
        Total = 0;
    }
}
```

## What gets mirrored

| Declared member | Mirrored when | Proxy member |
|---|---|---|
| Field | carries `[AspectOriented]` **and** an attribute whose simple name contains `Observable` or `Property` (`[VeloxProperty]`, `[Observable]`) | a `get`/`set` property named from the field (`_name` → `Name`) |
| Property | carries `[AspectOriented]`; getter mirrored when a public getter exists or no getter is declared; setter only when a public setter exists | the same property |
| Method | carries `[AspectOriented]` and is `public` | the same method, with fully qualified parameter and return types |

`[AspectOriented]` must be written with its simple name. The generator matches the text `AspectOriented` on the member (`Base/AnalizeHelper.cs`), so `[VeloxDev.AspectOriented.AspectOriented]` and aliased forms are not recognized.

## The generated surface

For `Counter` above the generators emit (all in the consumer assembly):

| Artifact | Type | File hint |
|---|---|---|
| Interface | `public interface VeloxDev.AopInterfaces.Counter_AopQuickStart_Aop : IAspectOriented, IAopHookTarget` | `Counter_AopQuickStart_Aop.g.cs` |
| Proxy | `internal sealed class Counter_AopQuickStart_AopProxy : Counter_AopQuickStart_Aop` | `Counter_AopQuickStart_AopProxy.g.cs` |
| Extension | `public static class Counter_AopQuickStart_AopExtensions` in `VeloxDev.AspectOriented` | `Counter_AopQuickStart_AopExt.g.cs` |

The name segment is the containing namespace with `.` replaced by `_`; a class in the global namespace uses `Global` (`Base/AopNames.cs`). Nothing is injected into `Counter` itself — the user's class does not implement the interface.

## Limits

The generator copies a method's name, parameters and return type, but not its type-parameter list, and the generated proxy passes arguments by value. Keep intercepted methods simple:

- unique names — the hook key is the bare method name, so **overloads are not supported**;
- no `ref` / `out` / `in` parameters;
- no generic method parameters.

## Expected result

`dotnet build` succeeds, and `counter.Aop()` resolves in IntelliSense to the generated extension returning `Counter_AopQuickStart_Aop`.
