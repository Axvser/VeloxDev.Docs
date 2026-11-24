# Closed-World Serialization

`VeloxDev.Serialization` writes and reads the archive JSON without reflection. The generator walks the compilation and emits one reader/writer per type in the archive closure, registered through module initializers. A type outside that closure has no writer, and writing it throws instead of falling back to reflection.

## Type groups

| Group | Types | Page |
|---|---|---|
| Annotations and options | `ArchivableAttribute`, `ArchiveAttribute`, `ArchiveOptions`, `SerializationOptions` | [Annotations and options](00_annotations-and-options/index.md) |
| Serializer entry points | `VeloxJsonSerializer`, `ViewModelSerializer` | [Serializer and view models](01_serializer-and-viewmodel/index.md) |
| Registry and token streams | `VeloxJsonRegistry`, `IVeloxJsonWriter`, `IVeloxJsonReader`, `VeloxJsonWriter`, `VeloxJsonReader`, `VeloxJsonFormat` | [Registry and streams](02_registry-and-streams/index.md) |
| In-memory JSON tree | `VeloxJsonValue`, `VeloxJsonScalar`, `VeloxJsonArray`, `VeloxJsonObject` | [JSON tree](03_json-tree/index.md) |

## What joins the closure

- A workflow component (tree, node, slot or link view model).
- A type carrying a `[VeloxProperty]` field.
- A type explicitly marked `[Archivable]`.

The generator then follows member types, collection element types, dictionary key/value types, derived classes and interface implementations declared in the same compilation, and (for an open generic root) the types its constraints admit. A type nothing reaches, and that is not a root itself, does not enter; a type from another assembly enters only as a closed generic this assembly has seen.

## Document contract

| Aspect | Rule |
|---|---|
| Member order | Declaration order. Changing it invalidates existing documents. |
| Default members | Public property with a public setter. |
| Names | `{Type, AssemblyName}` for `$type`; member names are the C# names unless `[Archive(ArchiveOptions.ReName, "…")]` moves one. |
| References | `$id` on first write, `$ref` on repetition; cycles are preserved. |
| Enums | Written as their underlying integer unless `[Archive(ArchiveOptions.EnumName)]`. |
| Null | The JSON `null` literal. |

## Guarantees

- No reflection fallback. A type with no registered writer throws `InvalidOperationException`; a document naming a type with no reader throws the same.
- Callbacks are the BCL's `[OnSerializing]`, `[OnSerialized]`, `[OnDeserializing]`, `[OnDeserialized]`; the generated code calls them directly, so they must be `internal` or wider. Deserialization callbacks run after all members of the type are read.
- The output is byte-for-byte the archive format the framework produced before this module existed.

See [Closed-World Serialization quick start](../../1_QuickStart/16_closed-world-serialization/index.md) for a complete console program.
