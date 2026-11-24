# Registry and Streams

The compile-time registry the generator fills, the writer/reader contracts, and the token cursors the generated code drives. Namespace `VeloxDev.Serialization`.

## VeloxDev.Serialization

### Class: VeloxJsonRegistry

The compile-time facts behind the closed world: which writer and reader belong to each type, the wire name of each type, and how to construct nested containers.

**Signature:** `public static class VeloxJsonRegistry`

| Member | Signature | Description |
|---|---|---|
| `RegisterContainerFactory` | `static void RegisterContainerFactory(Type type, Func<object> factory)` | Registers how to construct a nested container (`Dictionary<K,V>`, `List<T>`) the document holds as a value. |
| `ContainerFactoryFor` | `static Func<object>? ContainerFactoryFor(Type type)` | The factory, or `null`. |
| `RegisterWriter` | `static void RegisterWriter(Type type, IVeloxJsonWriter writer, bool declaresType)` | Registers a type's writer. When `declaresType` is false, an existing entry wins. |
| `RegisterReader` | `static void RegisterReader(Type type, IVeloxJsonReader reader, bool declaresType)` | Registers a type's reader, same precedence. |
| `RegisterName` | `static void RegisterName(Type type, string name)` | Registers the wire name (`Namespace.Type, AssemblyName`, generics written the same way). |
| `NameOf` | `static string? NameOf(Type type)` | The wire name, or `null`. |
| `TypeOf` | `static Type? TypeOf(string name)` | The type a document name stands for, or `null`. |
| `WriterFor` | `static IVeloxJsonWriter? WriterFor(Type type)` | The writer, or `null`. |
| `ReaderFor` | `static IVeloxJsonReader? ReaderFor(Type type)` | The reader, or `null`. |

Registration happens in generated `[ModuleInitializer]` methods, so the tables are complete before `Main`. The tables are published as immutable snapshots, which is why lookups take no lock.

### Interface: IVeloxJsonWriter

One generated implementation per serializable type.

**Signature:** `public interface IVeloxJsonWriter`

| Member | Signature | Description |
|---|---|---|
| `Write` | `void Write(VeloxJsonWriter writer, object value, Type? declaredType)` | Writes the instance's members. A type name is written when the runtime type differs from `declaredType`. |
| `WriteAsync` | `Task WriteAsync(VeloxJsonWriter writer, object value, Type? declaredType)` | The awaited form. |

### Interface: IVeloxJsonReader

**Signature:** `public interface IVeloxJsonReader`

| Member | Signature | Description |
|---|---|---|
| `Create` | `object Create()` | Creates a blank instance to read into. |
| `Read` | `void Read(VeloxJsonReader reader, object target)` | Reads the members into `target`, consuming through the closing brace. |
| `ReadAsync` | `Task ReadAsync(VeloxJsonReader reader, object target)` | The awaited form. |

### Enum: VeloxJsonFormat

**Signature:** `public enum VeloxJsonFormat`

| Member | Meaning |
|---|---|
| `Compact` | No whitespace. |
| `Indented` | One member per line, indented by two spaces. |

### Class: VeloxJsonWriter

The archive-format writer: exact indentation, separators, number spellings and `$id` / `$type` / `$ref` bookkeeping. Single-use, not thread-safe.

**Signature:** `public sealed partial class VeloxJsonWriter`

**Constructor:** `public VeloxJsonWriter(TextWriter writer, bool indented = true)`

| Member | Signature | Description |
|---|---|---|
| `GetOrAddReference` | `int GetOrAddReference(object instance)` | The id of an already-written object, or a fresh one. |
| `WriteStartObject` | `bool WriteStartObject(object instance, Type? declaredType)` | Starts an object; returns false when a reference was emitted instead. |
| `WriteStartObjectWithoutReference` | `void WriteStartObjectWithoutReference()` | Starts an object with no `$id` or `$type`. |
| `WriteEndObject` | `void WriteEndObject()` | Ends an object. |
| `WriteStartArray` | `void WriteStartArray()` | Starts an array. |
| `WriteNextElement` | `void WriteNextElement()` | Writes the separator before an element; omit for an empty array. |
| `WriteEndArray` | `void WriteEndArray()` | Ends an array. |
| `WriteMemberName` | `void WriteMemberName(string name)` | Writes a property name; the value follows. |
| `WriteString` | `void WriteString(string? value)` | Writes a string; `null` writes the literal. |
| `WriteNull` | `void WriteNull()` | Writes the JSON `null`. |
| `WriteBoolean` | `void WriteBoolean(bool value)` | Writes `true` / `false`. |
| `WriteInt32` / `WriteInt64` | `void WriteInt32(int value)`, `void WriteInt64(long value)` | Integers. |
| `WriteDouble` | `void WriteDouble(double value)` | Shortest round-trippable; integral values get `.0`; non-finite values are strings. |
| `WriteSingle` | `void WriteSingle(float value)` | Same spelling as a double. |
| `WriteDecimal` | `void WriteDecimal(decimal value)` | Decimal. |
| `WriteGuid` | `void WriteGuid(Guid value)` | Hyphenated lower-case. |
| `WriteRawValue` | `void WriteRawValue(string json)` | A value that already carries its JSON spelling. |

The async companion adds `CompleteAsync` and an `*Async` twin for every shape and scalar writer (`WriteStartObjectAsync`, `WriteEndObjectAsync`, `WriteStartArrayAsync`, `WriteNextElementAsync`, `WriteEndArrayAsync`, `WriteMemberNameAsync`, `WriteStringAsync`, `WriteNullAsync`, `WriteBooleanAsync`, `WriteInt32Async`, `WriteInt64Async`, `WriteDoubleAsync`, `WriteSingleAsync`, `WriteDecimalAsync`, `WriteGuidAsync`, `WriteRawValueAsync`, `WriteStartObjectWithoutReferenceAsync`).

### Class: VeloxJsonReader

A cursor over one document with the object protocol the generated readers use. Order-independent: members dispatch by name. Single-use, not thread-safe.

**Signature:** `public sealed partial class VeloxJsonReader`

**Constructors**

| Signature |
|---|
| `VeloxJsonReader(string json)` |
| `VeloxJsonReader(TextReader reader, int bufferSize = 8192)` |
| `VeloxJsonReader(Stream stream, int bufferSize = 8192)` — UTF-8, honours a byte order mark, leaves the stream open |

| Member | Signature | Description |
|---|---|---|
| `AtEnd` | `bool AtEnd { get; }` | Whether the document is consumed. |
| `BeginObject` | `bool BeginObject(out int referenceId, out string? typeName)` | Starts an object; false when the document held a `$ref`. |
| `NextMember` | `bool NextMember(out string name)` | Reads the next member name. |
| `NextMember` | `bool NextMember()` | Advances without materialising the name; pair with `MemberNameEquals`. |
| `MemberNameEquals` | `bool MemberNameEquals(string name)` | Compares the just-read member name in place. |
| `FinishObject` | `void FinishObject()` | Consumes the closing brace. |
| `BeginArray` | `void BeginArray()` | Starts an array. |
| `NextElement` | `bool NextElement()` | Moves to the next element. |
| `FinishArray` | `void FinishArray()` | Consumes the closing bracket. |
| `RegisterReference` | `void RegisterReference(int referenceId, object instance)` | Makes an object resolvable before its members are read. |
| `ResolveReference` | `object? ResolveReference(int referenceId)` | The object an id stands for. |
| `NextIsString` / `NextIsArray` / `NextIsObject` / `NextIsNull` | `bool` | Token lookaheads. |
| `ReadNullIfPresent` | `bool ReadNullIfPresent()` | Consumes a `null` literal when present. |
| `ReadEnum` | `object? ReadEnum(Type enumType)` | Reads an enum written as its name, or `null`. |
| `ReadString` | `string? ReadString()` | Reads a string; a JSON `null` reads as `null`. |
| `ReadText` | `string ReadText()` | Reads a value's text, quoted or bare. |
| `ReadBoolean` | `bool ReadBoolean()` | Reads a boolean; throws `FormatException` otherwise. |
| `ReadInt32` / `ReadInt64` | `int` / `long` | Integers. |
| `ReadDouble` | `double ReadDouble()` | Includes the `"NaN"`, `"Infinity"`, `"-Infinity"` spellings. |
| `ReadSingle` | `float ReadSingle()` | Single precision. |
| `ReadDecimal` | `decimal ReadDecimal()` | Decimal. |
| `ReadGuid` | `Guid ReadGuid()` | From the hyphenated text form. |
| `SkipValue` | `void SkipValue()` | Skips one value of any shape, at any depth. |

The async companion mirrors this surface: `AtEndAsync`, `BeginObjectAsync`, `NextMemberAsync`, `ReadMemberNameAsync`, `FinishObjectAsync`, `BeginArrayAsync`, `NextElementAsync`, `FinishArrayAsync`, `NextIsNullAsync`, `ReadNullIfPresentAsync`, `NextIsStringAsync`, `NextIsArrayAsync`, `NextIsObjectAsync`, `ReadEnumAsync`, `ReadStringAsync`, `ReadTextAsync`, `ReadBooleanAsync`, `ReadInt32Async`, `ReadInt64Async`, `ReadDoubleAsync`, `ReadSingleAsync`, `ReadDecimalAsync`, `ReadGuidAsync`, `SkipValueAsync`.

## Example

```csharp
using System.IO;
using VeloxDev.Serialization;

var writer = new StringWriter();
VeloxJsonSerializer.WriteTo(writer, note);      // generated writer for NoteViewModel
string document = writer.ToString();

using var stream = new MemoryStream();
VeloxJsonSerializer.WriteTo(stream, note);      // UTF-8, no BOM, stream left open

var reader = new VeloxJsonReader(document);
NoteViewModel? back = VeloxJsonSerializer.Deserialize<NoteViewModel>(document);
```

Application code rarely touches the reader/writer directly; the generated readers/writers and `VeloxJsonSerializer` cover the normal path. Use this layer for custom emission or token-level inspection.
