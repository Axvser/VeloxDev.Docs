# Serialization — Archive a View Model, Rebuild It

`VeloxDev.Serialization` writes an object graph to JSON and reads it back — no reflection, no attributes to register, and no serializer instance to configure. It is a module of its own: it archives **any** view model, and the workflow tree is one of its callers.

## 1. Prerequisites

| Need | Why |
|---|---|
| A .NET project targeting `net8.0` (or any TFM `VeloxDev.Core` ships: `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0`) | `VeloxDev.Core` multi-targets; pick whichever your app already uses |
| The .NET SDK that builds it | Any SDK that can build the TFM you chose |

No service, no file, and no network access is involved.

## 2. Install

```powershell
dotnet new console -n ArchiveDemo
cd ArchiveDemo
dotnet add package VeloxDev.Core
```

**Expected result:** restore succeeds, and the project can `using VeloxDev.Serialization;`. The source generator (`VeloxDev.Core.Generator`) arrives as a package analyzer, so it runs in this project without a second reference.

## 3. Annotate a type

Serialization is **closed-world**: a type round-trips only if the generator emitted a reader and a writer for it. There are four ways in (`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:588-614`):

| Route | For |
|---|---|
| Implement one of the four workflow component interfaces | workflow trees, nodes, slots, links |
| Carry a `[WorkflowBuilder.*]` attribute | a component written from a template |
| Have a `[VeloxProperty]` **field** | your own view models — this page's route |
| Carry `[Archivable]` | a plain document that is not a view model |

```csharp
using VeloxDev.MVVM;                    // [VeloxProperty]

public sealed partial class Inventory
{
    [VeloxProperty] private string name = "";
    [VeloxProperty] private int count;
}
```

The class must be `partial`: the generator promotes each field into an observable property, and it also makes the type implement `INotifyPropertyChanged`.

**Expected result:** the project still builds, and `Inventory` now has public `Name` and `Count` properties.

## 4. Serialize and rebuild

```csharp
using VeloxDev.Serialization;           // Serialize<T> / Deserialize<T>

var before = new Inventory();
before.Name = "bolts";
before.Count = 42;

string json = before.Serialize();        // whole object graph → JSON
Inventory after = json.Deserialize<Inventory>();
```

**Expected result:** `after.Name == "bolts"` and `after.Count == 42` — the rebuilt instance came back through the parameterless constructor and then had its members written.

`TryDeserialize<T>(out var copy)` is the non-throwing form: it returns `false` on null, blank or malformed text instead of throwing.

### Which entry point you get

There are two, and the route you took in §3 decides which one:

| Entry | Constraint | Use it for |
|---|---|---|
| `ViewModelSerializer.Serialize<T>` / `.Deserialize<T>` | `where T : INotifyPropertyChanged` | the `[VeloxProperty]` route — view models |
| `VeloxJsonSerializer.Serialize(object, …)` / `.Deserialize<T>` | `where T : class` | the `[Archivable]` route — plain documents. This is what `CheckpointEx` calls |

### When a round trip goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `MissingWriter` / `MissingReader` | The type never entered the closed world. | Add `[Archivable]`, or reach it from a type that has it. |
| The member is absent from the document | It has no public setter. | `[Archive(ArchiveOptions.KeepProperty)]` writes it — but it still will not read back. |
| An enum comes back as a number | Enums are written as their underlying integer by default. | `[Archive(ArchiveOptions.EnumName)]` on that one member writes the value's name. |
| `InvalidOperationException` on read | The document is missing a `required` member. | Write the member, or drop `required`. |

The format is **not** interchangeable with `System.Text.Json` or Newtonsoft: the type discriminator, the collection shapes and the member set all differ, and a foreign type tag does not resolve — the reader falls back to the declared type.

## 5. Verification

The behaviour above is pinned by the module's own suites:

```bash
dotnet test Src/Core/VeloxDev.Core.Test --filter "FullyQualifiedName~Serialization"
dotnet test Src/Core/VeloxDev.Core.Extension.Test --filter "FullyQualifiedName~Serialization"
```

`ShapeRoundTripTests` and `ElementScalarRoundTripTests` hold the two sync/async chains to the same spelling, `SerializationGoldenTests` compares whole documents byte-for-byte, and `RegistryOwnershipTests` holds the declaring-assembly-wins rule.

## 6. Complete Code

```csharp
using System;
using VeloxDev.MVVM;
using VeloxDev.Serialization;

namespace ArchiveDemo
{
    public sealed partial class Inventory
    {
        [VeloxProperty] private string name = "";
        [VeloxProperty] private int count;
    }

    public static class Program
    {
        public static void Main()
        {
            var before = new Inventory();
            before.Name = "bolts";
            before.Count = 42;

            string json = before.Serialize();
            Console.WriteLine(json);

            Inventory after = json.Deserialize<Inventory>();
            bool same = after.Name == before.Name && after.Count == before.Count;
            Console.WriteLine($"round-trip ok: {same}");
        }
    }
}
```

## 7. Run Declaration

- ⚠️ **Not actually run — statically verified only.** Every identifier is checked against the tree: `[VeloxProperty]` (`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`), `Serialize<T>` / `Deserialize<T>` (`Src/Core/VeloxDev.Core/Serialization/ViewModelSerializer.cs:109,151`), and the generator's promotion rule (`Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs:381`, `:998`). No program from this page was executed, so the exact JSON text is **not** asserted — only the round-trip equality is.
