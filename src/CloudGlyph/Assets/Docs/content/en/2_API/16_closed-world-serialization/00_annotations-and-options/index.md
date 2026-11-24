# Annotations and Options

The attributes that decide membership and member shape, and the per-call formatting options. Namespace `VeloxDev.Serialization`.

## VeloxDev.Serialization

### Class: ArchivableAttribute

Marks a type as part of the archive format and optionally names further roots.

**Signature:** `public sealed class ArchivableAttribute : Attribute`

| Member | Signature | Description |
|---|---|---|
| Constructor | `ArchivableAttribute(params Type[] additionalRoots)` | Marks the type; each extra type joins as a root. |
| `AdditionalRoots` | `IReadOnlyList<Type> { get; }` | The further types this declaration puts into the format. |

**Attribute usage:** `AttributeTargets.Class | AttributeTargets.Struct`, `Inherited = false`.

A view model that is a component or carries `[VeloxProperty]` needs no `[Archivable]`. Use it for a plain document type — a checkpoint, a report, a DTO. The named types must be declared in the same assembly; naming one twice costs nothing.

### Class: ArchiveAttribute

Changes how one member takes part in the document.

**Signature:** `public sealed class ArchiveAttribute : Attribute`

| Member | Signature | Description |
|---|---|---|
| Constructor | `ArchiveAttribute(ArchiveOptions options, object? argument = null)` | `argument` is the string for `ReName`; `null` otherwise. |
| `Options` | `ArchiveOptions { get; }` | What to change. |
| `Argument` | `object? { get; }` | The value `Options` needs. |

**Attribute usage:** `AttributeTargets.Property | AttributeTargets.Field`, `Inherited = false`.

### Enum: ArchiveOptions

**Signature:** `[Flags] public enum ArchiveOptions`

| Member | Value | Effect |
|---|---|---|
| `None` | 0 | Default rules. |
| `KeepProperty` | 1 | Include a computed property (no public setter). It is written but cannot be read back. |
| `KeepField` | 2 | Include a field that has no property beside it. |
| `IgnoreField` | 4 | Leave out a member the default rules would take. |
| `ReName` | 8 | Write the member under `ArchiveAttribute.Argument` instead of its own name. |
| `EnumName` | 16 | Write this enum member as its name rather than its underlying number. Applies to an enum and a nullable enum. |

The default member rule is: a public property with a public setter, in declaration order. Everything else is left out unless one of these options names it.

### Class: SerializationOptions

Per-call overrides, built fluently and passed to the `Serialize` / `Deserialize` / `TryDeserialize` overloads.

**Signature:** `public sealed class SerializationOptions`

| Member | Signature | Description |
|---|---|---|
| `Create` | `static SerializationOptions Create()` | A blank builder. |
| `WithIndented` | `SerializationOptions WithIndented()` | Human-readable output. |
| `WithCompact` | `SerializationOptions WithCompact()` | No extra whitespace. |
| `WithExcludedPropertyTypes` | `SerializationOptions WithExcludedPropertyTypes(params Type[] types)` | Omits every property whose **declared** type is an exact match for one of `types`, everywhere in the graph. |

`WithExcludedPropertyTypes` exists for compiled-graph snapshots: a node's `Parent` is declared `ITreeComponent`, so excluding that declared type keeps the whole tree out of the document without excluding a slot's forward-needed parent (whose declared type differs). The filter is ambient for the duration of one write, not a parameter threaded through generated code.

## Example

```csharp
using VeloxDev.Serialization;

[Archivable]
public sealed class Checkpoint
{
    [Archive(ArchiveOptions.ReName, "id")]
    public string? NodeId { get; set; }

    public int Attempt { get; set; }

    [Archive(ArchiveOptions.IgnoreField)]
    public string CacheKey { get; set; } = "";
}

var json = VeloxJsonSerializer.Serialize(new Checkpoint { NodeId = "node-1", Attempt = 3 });
// The first member is written as "id"; the second as "Attempt".
```

`Archive` is applied per member; `Archivable` decides only whether the type is in. A member the generator cannot reach is reported rather than silently dropped.
