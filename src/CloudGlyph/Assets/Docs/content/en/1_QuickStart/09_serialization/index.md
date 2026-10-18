# Serialization — Archive a View Model, Rebuild It

`VeloxDev.Serialization` writes a generated object graph to JSON and reads it back. There is no reflection and no runtime registration: a type is written only if the source generator emitted a reader and a writer for it. The workflow tree is one caller; the engine archives any annotated view model.

## 1. Prerequisites

| Need | Why |
|---|---|
| .NET SDK 8.0 or later | The generator is built against Roslyn 4.8, the compiler that ships with the .NET 8 SDK |
| A target framework `VeloxDev.Core` declares: `netstandard2.0`, `netframework4.6.1`, `net5.0`, `netcoreapp3.0`, or `net8.0` | `VeloxDev.Core` 10.0.0 multi-targets these; pick the one your app already uses |
| NuGet access | Restores `VeloxDev.Core` and `VeloxDev.Core.Generator` |

No service, file, or network access is involved at run time.

## 2. Install

```powershell
dotnet new console -n ArchiveDemo
cd ArchiveDemo
dotnet add package VeloxDev.Core --version 10.0.0
dotnet add package VeloxDev.Core.Generator --version 10.0.0
```

**Expected result:** restore exits 0, and the project can `using VeloxDev.Serialization;`. `VeloxDev.Core` carries the runtime and `[VeloxProperty]`; `VeloxDev.Core.Generator` is the analyzer that emits the reader/writer pair. Keep the generator reference explicit when you use a `ProjectReference` to Core — analyzer assets do not flow through project references.

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
| `InvalidOperationException` saying a type "has no registered JSON writer" or "reader" | The type never entered the closed world | Add `[Archivable]`, or reach it from a type that has it |
| The member is absent from the document | It has no public setter | `[Archive(ArchiveOptions.KeepProperty)]` writes it — but it still will not read back |
| An enum comes back as a number | Enums are written as their underlying integer by default | `[Archive(ArchiveOptions.EnumName)]` on that one member writes the value's name |
| `InvalidOperationException` on read | The document is missing a `required` or `[JsonRequired]` member | Write the member, or drop the requirement |
| An `object` member comes back as a dictionary, `long`, or `string` | The format cannot recover a CLR type the declaration does not name | Declare the concrete type on the member |

The format is **not** interchangeable with `System.Text.Json` or Newtonsoft: the type discriminator, the collection shapes and the member set all differ, and a foreign type tag does not resolve — the reader falls back to the declared type.

## 5. Verification

```powershell
dotnet run
```

**Expected result:** the JSON document is printed, followed by `round-trip ok: True`:

```text
{
  "$id": "1",
  "Name": "bolts",
  "Count": 42
}
round-trip ok: True
```

The engine's own suites are the authority for the behaviours above (run from the repository root):

```bash
dotnet test Src/Core/VeloxDev.Core.Test --filter "FullyQualifiedName~Serialization"
dotnet test Src/Core/VeloxDev.Core.Extension.Test --filter "FullyQualifiedName~Serialization"
```

`ShapeRoundTripTests` and `ElementScalarRoundTripTests` hold the sync and async chains to the same spelling, `SerializationGoldenTests` compares whole documents byte-for-byte, and `RegistryOwnershipTests` holds the declaring-assembly-wins rule.

## 6. Complete Code

Replace the contents of `Program.cs` with:

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

- ✅ **Actually built and ran on 2026-10-18** against the locally built `VeloxDev.Core` 10.0.0 (`net8.0`) and `VeloxDev.Core.Generator` (Debug) assemblies from this repository. The NuGet install commands themselves were not re-run; the code and generator path are the same. Recorded output:

```text
{
  "$id": "1",
  "Name": "bolts",
  "Count": 42
}
round-trip ok: True
```

Every identifier is also checked against the tree: `[VeloxProperty]` (`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`), `Serialize<T>` / `Deserialize<T>` (`Src/Core/VeloxDev.Core/Serialization/ViewModelSerializer.cs:109,151`), and the generator's promotion rule (`Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs:381`, `:998`).
