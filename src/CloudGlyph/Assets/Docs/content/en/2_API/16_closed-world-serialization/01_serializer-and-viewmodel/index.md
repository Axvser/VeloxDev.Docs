# Serializer and View Models

The static serializer and the extension methods that add `INotifyPropertyChanged` conveniences. Namespace `VeloxDev.Serialization`.

## VeloxDev.Serialization

### Class: VeloxJsonSerializer

The closed-world serializer. Split across a synchronous file and an async companion; both are the same static partial type.

**Signature:** `public static partial class VeloxJsonSerializer`

**Synchronous writing**

| Member | Signature | Description |
|---|---|---|
| `Serialize` | `static string Serialize(object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` | Writes a value as a document string. |
| `WriteTo` | `static void WriteTo(TextWriter output, object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` | Writes into a text writer. |
| `WriteTo` | `static void WriteTo(Stream output, object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` | Writes UTF-8 into a stream; the stream is left open. |
| `WriteValue` | `static void WriteValue(VeloxJsonWriter writer, object? value, Type? declaredType)` | Writes one value; a container becomes an array or object, anything else uses its registered writer. |
| `WriteMap` | `static void WriteMap(VeloxJsonWriter writer, IDictionary map, Type declaredType, Type valueType, bool interfaceKeys)` | Writes a map; interface-keyed maps use the keys' reference ids as property names. |
| `IsExcluded` | `static bool IsExcluded(Type declaredType)` | Whether the current write excludes a member of that declared type. |

**Synchronous reading**

| Member | Signature | Description |
|---|---|---|
| `Deserialize<T>` | `static T? Deserialize<T>(string json) where T : class` | Reads a document string; `null` when the document is the JSON literal. |
| `Deserialize` | `static object? Deserialize(string json, Type type)` | Reads into a run-time type. |
| `Deserialize<T>` | `static T? Deserialize<T>(TextReader reader) where T : class` | Streams from a reader. |
| `Deserialize` | `static object? Deserialize(TextReader reader, Type type)` | Streams into a run-time type. |
| `Deserialize<T>` | `static T? Deserialize<T>(Stream stream) where T : class` | Streams UTF-8, honouring a byte order mark. |
| `Deserialize` | `static object? Deserialize(Stream stream, Type type)` | Streams into a run-time type. |
| `ReadUnknown` | `static object? ReadUnknown(VeloxJsonReader reader)` | Reads a value whose declared type is `object`, by token shape. |
| `ReadValue` | `static object? ReadValue(VeloxJsonReader reader, Type declaredType, object? existing)` | Reads one value, reusing `existing` when it matches. |
| `ReadArray` | `static void ReadArray(VeloxJsonReader reader, IList target, Type elementType)` | Clears and fills a list. |
| `ReadMap` | `static void ReadMap(VeloxJsonReader reader, IDictionary target, Type keyType, Type valueType, bool interfaceKeys)` | Clears and fills a map. |

**Asynchronous**

| Member | Signature |
|---|---|
| `WriteToAsync` | `static Task WriteToAsync(Stream output, object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` |
| `WriteToAsync` | `static Task WriteToAsync(TextWriter output, object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` |
| `WriteValueAsync` | `static Task WriteValueAsync(VeloxJsonWriter writer, object? value, Type? declaredType)` |
| `WriteMapAsync` | `static Task WriteMapAsync(VeloxJsonWriter writer, IDictionary map, Type declaredType, Type valueType, bool interfaceKeys)` |
| `DeserializeAsync<T>` | `static Task<T?> DeserializeAsync<T>(TextReader reader) where T : class` |
| `DeserializeAsync` | `static Task<object?> DeserializeAsync(TextReader reader, Type type)` |
| `DeserializeAsync<T>` | `static Task<T?> DeserializeAsync<T>(Stream stream) where T : class` |
| `DeserializeAsync` | `static Task<object?> DeserializeAsync(Stream stream, Type type)` |
| `ReadValueAsync` | `static Task<object?> ReadValueAsync(VeloxJsonReader reader, Type declaredType, object? existing)` |
| `ReadUnknownAsync` | `static Task<object?> ReadUnknownAsync(VeloxJsonReader reader)` |
| `ReadArrayAsync` | `static Task ReadArrayAsync(VeloxJsonReader reader, IList target, Type elementType)` |
| `ReadMapAsync` | `static Task ReadMapAsync(VeloxJsonReader reader, IDictionary target, Type keyType, Type valueType, bool interfaceKeys)` |

**Exceptions:** `ArgumentNullException` for a null value / writer / reader / type; `InvalidOperationException` when a value's type has no registered writer or a document names a type with no reader.

### Class: ViewModelSerializer

Extensions for `INotifyPropertyChanged`, which the MVVM generator adds to a view model.

**Signature:** `public static class ViewModelSerializer`

**Synchronous**

| Member | Signature | Description |
|---|---|---|
| `Serialize<T>` | `static string Serialize<T>(this T workflow) where T : INotifyPropertyChanged` | Indented by default. |
| `Serialize<T>` | `static string Serialize<T>(this T workflow, SerializationOptions options) where T : INotifyPropertyChanged` | With options. |
| `TryDeserialize<T>` | `static bool TryDeserialize<T>(this string json, out T? workflow) where T : INotifyPropertyChanged` | Returns `false` for null, empty or malformed input. |
| `TryDeserialize<T>` | `static bool TryDeserialize<T>(this string json, SerializationOptions options, out T? workflow) where T : INotifyPropertyChanged` | With options. |
| `Deserialize<T>` | `static T Deserialize<T>(this string json) where T : INotifyPropertyChanged` | Throws on failure. |
| `Deserialize<T>` | `static T Deserialize<T>(this string json, SerializationOptions options) where T : INotifyPropertyChanged` | With options. |
| `DeserializeToType` | `static object? DeserializeToType(this VeloxJsonValue value, Type targetType)` | Reads a JSON tree into a type. |
| `SerializeToTextWriter<T>` | `static void SerializeToTextWriter<T>(this T workflow, TextWriter writer, SerializationOptions? options = null) where T : INotifyPropertyChanged` | Streams into a writer. |
| `SerializeToStream<T>` | `static void SerializeToStream<T>(this T workflow, Stream stream, SerializationOptions? options = null) where T : INotifyPropertyChanged` | Streams UTF-8 into a stream. |
| `DeserializeFromTextReader<T>` | `static T? DeserializeFromTextReader<T>(this TextReader reader) where T : INotifyPropertyChanged` | Streams from a reader. |
| `DeserializeFromStream<T>` | `static T? DeserializeFromStream<T>(this Stream stream) where T : INotifyPropertyChanged` | Streams from a stream. |
| `SerializeToUtf8Bytes<T>` | `static byte[] SerializeToUtf8Bytes<T>(this T workflow, SerializationOptions? options = null) where T : INotifyPropertyChanged` | UTF-8 bytes. |
| `DeserializeFromUtf8Bytes<T>` | `static T DeserializeFromUtf8Bytes<T>(this byte[] utf8Json, SerializationOptions? options = null) where T : INotifyPropertyChanged` | From UTF-8 bytes. |

**Asynchronous**

| Member | Signature |
|---|---|
| `SerializeAsync<T>` | `static Task<string> SerializeAsync<T>(this T workflow, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `SerializeAsync<T>` | `static Task<string> SerializeAsync<T>(this T workflow, SerializationOptions options, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `DeserializeAsync<T>` | `static Task<T> DeserializeAsync<T>(this string json, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `DeserializeAsync<T>` | `static Task<T> DeserializeAsync<T>(this string json, SerializationOptions options, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `SerializeToUtf8BytesAsync<T>` | `static Task<byte[]> SerializeToUtf8BytesAsync<T>(this T workflow, SerializationOptions? options = null, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `DeserializeFromUtf8BytesAsync<T>` | `static Task<T> DeserializeFromUtf8BytesAsync<T>(this byte[] utf8Json, SerializationOptions? options = null, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `SerializeToTextWriterAsync<T>` | `static Task SerializeToTextWriterAsync<T>(this T workflow, TextWriter writer, SerializationOptions? options = null, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `DeserializeFromTextReaderAsync<T>` | `static Task<T> DeserializeFromTextReaderAsync<T>(this TextReader reader, SerializationOptions? options = null, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `SerializeToStreamAsync<T>` | `static Task SerializeToStreamAsync<T>(this T workflow, Stream stream, SerializationOptions? options = null, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |
| `DeserializeFromStreamAsync<T>` | `static Task<T> DeserializeFromStreamAsync<T>(this Stream stream, SerializationOptions? options = null, CancellationToken cancellationToken = default) where T : INotifyPropertyChanged` |

The streaming overloads avoid building a whole document string; peak memory is the buffer plus the graph.

## Example

```csharp
using System;
using VeloxDev.Serialization;

var note = new NoteViewModel { Title = "Ship", Priority = 2 };
note.Tags.Add("docs");

string json = note.Serialize();
string compact = note.Serialize(SerializationOptions.Create().WithCompact());

NoteViewModel restored = json.Deserialize<NoteViewModel>();
if (json.TryDeserialize<NoteViewModel>(out var safe))
{
    Console.WriteLine(safe?.Title);
}

byte[] utf8 = note.SerializeToUtf8Bytes();
NoteViewModel same = utf8.DeserializeFromUtf8Bytes<NoteViewModel>();
```

A collection property is cleared and refilled on read, not appended to; the collection instance itself is reused so its subscriptions survive. See [Closed-World Serialization quick start](../../../1_QuickStart/16_closed-world-serialization/index.md) for the complete program.
