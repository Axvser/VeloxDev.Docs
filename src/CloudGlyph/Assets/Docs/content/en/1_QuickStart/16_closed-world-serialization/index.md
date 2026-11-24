# Closed-World Serialization

Serialize a view model to JSON and read it back without reflection. Only types the generator compiled a reader/writer for can appear in a document; anything outside that closure fails loudly instead of falling back to reflection.

## 1. Prerequisites

- **Supported targets of `VeloxDev.Core`**: `netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`. The sample uses `net8.0`.
- **`VeloxDev.Core`** and **`VeloxDev.Core.Generator`**. The generator walks the compilation and emits one reader/writer per type in the archive closure plus module-initializer registration into `VeloxJsonRegistry`.
- .NET SDK 8.0 or later. No services are required.

## 2. Install / Add Dependency

```text
dotnet new console -n SerializationQuickStart
cd SerializationQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**Expected result:** both packages restore. After the first build the compiled writers, readers and their registration (which runs before `Main`) are in place; set `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` to write the `<Assembly>_VeloxJson.g.cs` file under `obj/`.

## 3. Basic Setup / Registration

A type joins the closure in one of two ways: it is a workflow component (a tree/node/slot/link view model), or it carries a `[VeloxProperty]` field, or it is explicitly marked `[Archivable]`. A view model that satisfies the first two needs no extra attribute.

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "";
    [VeloxProperty] private int _priority;
    [VeloxProperty] private ObservableCollection<string> _tags = new();
}
```

**Expected result:** in the generated JSON the members are `Title`, `Priority` and `Tags`, in that declaration order. A member's order is a byte-level contract: changing it invalidates documents already saved.

## 4. Core Usage (Step by Step)

### 4.1 Serialize and deserialize a view model

The `ViewModelSerializer` extensions require `INotifyPropertyChanged`, which the MVVM generator adds to the class. `Serialize()` is indented; `Deserialize<T>()` throws on failure, while `TryDeserialize<T>()` returns `false`.

```csharp
var note = new NoteViewModel { Title = "Ship", Priority = 2 };
note.Tags.Add("docs");

var json = note.Serialize();                    // indented
var compact = note.Serialize(
    SerializationOptions.Create().WithCompact());

var restored = json.Deserialize<NoteViewModel>();
if (json.TryDeserialize<NoteViewModel>(out var safe))
{
    // safe is the same graph, or null on failure
}
```

**Expected result:** `json` is a JSON object whose members are `Title`, `Priority`, `Tags`; `restored.Title` is `"Ship"`, `restored.Priority` is 2 and `restored.Tags` contains `"docs"`. The tag collection is cleared and refilled, not appended to.

### 4.2 Include a plain type with `[Archivable]`

A document type that is not a view model — a checkpoint, a report, a DTO — declares itself. It does not need `[VeloxProperty]` and does not need to be `partial`; public properties with public setters enter by default.

```csharp
using VeloxDev.Serialization;

[Archivable]
public sealed class Checkpoint
{
    [Archive(ArchiveOptions.ReName, "id")]
    public string? NodeId { get; set; }

    public int Attempt { get; set; }
}

var json = VeloxJsonSerializer.Serialize(new Checkpoint { NodeId = "node-1", Attempt = 3 });
var back = VeloxJsonSerializer.Deserialize<Checkpoint>(json);
```

**Expected result:** the document names the first member `"id"` (not `"NodeId"`) and the second `"Attempt"`; `back.NodeId` is `"node-1"` and `back.Attempt` is 3. `Archivable` can also name further root types declared in the same assembly: `[Archivable(typeof(Rule), typeof(RuleSet))]`.

### 4.3 Choose which members enter

The default rule is: a public property with a public setter, in declaration order. `[Archive]` changes one member at a time:

| Option | Effect |
| --- | --- |
| `KeepProperty` | include a computed property (no public setter); it is written but cannot be read back |
| `KeepField` | include a field that has no property beside it |
| `IgnoreField` | leave out a member the default rules would take |
| `ReName` | write the member under `Argument` instead of its own name |
| `EnumName` | write this enum member as its name, not its underlying number |

**Expected result:** a computed property stays out unless marked `KeepProperty`; a renamed member round-trips because the reader applies the same mapping.

### 4.4 What the closure does and does not contain

The generator includes a type when the compilation reaches it, then follows its member types, collection element types, dictionary key/value types and (for a root-marked open generic) the types its constraints admit. Derived classes and interface implementations declared in the same assembly are taken in automatically. A type declared in another assembly can only take part when it is a closed generic that assembly has seen; otherwise it is reported at generation time rather than silently dropped.

There is no reflection fallback. Writing a type with no registered writer throws `InvalidOperationException`; reading a document whose `$type` has no reader throws too.

```csharp
try
{
    VeloxJsonSerializer.Serialize(new { Id = 1 });
}
catch (InvalidOperationException error)
{
    Console.WriteLine(error.Message);
}
```

**Expected result:** the anonymous type is outside the closure and the message names the type and says it has no registered writer.

### 4.5 Streaming overloads

The same serializer has `SerializeToTextWriter`, `SerializeToStream`, `SerializeToUtf8Bytes`, `DeserializeFromTextReader`, `DeserializeFromStream` and `DeserializeFromUtf8Bytes`, each with an async counterpart. They avoid building a whole document string; peak memory is the reader/writer buffer plus the graph.

```csharp
byte[] utf8 = note.SerializeToUtf8Bytes();
NoteViewModel same = utf8.DeserializeFromUtf8Bytes<NoteViewModel>();
```

**Expected result:** `same` equals the graph read from the string form.

## 5. Verification

Run the complete program. The first document contains `Title`, `Priority`, `Tags`; the restored line prints `restored: Ship / 2 / 2 tags`; the checkpoint document contains `"id"` and `"Attempt"` and reads back; the anonymous type prints the missing-writer message.

## 6. Complete Code

```csharp
using System;
using System.Collections.ObjectModel;
using VeloxDev.MVVM;
using VeloxDev.Serialization;

var note = new NoteViewModel { Title = "Ship the wiki", Priority = 2 };
note.Tags.Add("docs");
note.Tags.Add("wiki");

var json = note.Serialize();
Console.WriteLine(json);

var restored = json.Deserialize<NoteViewModel>();
Console.WriteLine($"restored: {restored.Title} / {restored.Priority} / {restored.Tags.Count} tags");

var compact = note.Serialize(SerializationOptions.Create().WithCompact());
Console.WriteLine($"compact length: {compact.Length}");

var checkpoint = new Checkpoint { NodeId = "node-1", Attempt = 3 };
var checkpointJson = VeloxJsonSerializer.Serialize(checkpoint);
Console.WriteLine(checkpointJson);

var back = VeloxJsonSerializer.Deserialize<Checkpoint>(checkpointJson);
Console.WriteLine($"checkpoint: {back?.NodeId} / {back?.Attempt}");

try
{
    VeloxJsonSerializer.Serialize(new { Id = 1 });
}
catch (InvalidOperationException error)
{
    Console.WriteLine($"outside the closure: {error.Message}");
}

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "";
    [VeloxProperty] private int _priority;
    [VeloxProperty] private ObservableCollection<string> _tags = new();
}

[Archivable]
public sealed class Checkpoint
{
    [Archive(ArchiveOptions.ReName, "id")]
    public string? NodeId { get; set; }

    public int Attempt { get; set; }
}
```

Entry points verified in `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs` and `ViewModelSerializer.cs`; the end-to-end round trip follows `Src/Test/Unit/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowSerializationTests.cs`.

## 7. Run Declaration

- ⚠️ Not actually run — statically verified only on 2026-11-25. Verified against the serializer, registry, annotations and options sources, the `VeloxJson` generator (`Src/Generators/VeloxDev.Core.Generator/VeloxJson.cs`, `Base/VeloxJsonModel.cs`, `Writers/VeloxJsonCodeWriter.cs`) and the serialization tests. No NuGet restore or execution was performed in this environment.
