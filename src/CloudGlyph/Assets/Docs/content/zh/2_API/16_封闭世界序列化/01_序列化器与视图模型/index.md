# 序列化器与视图模型

静态序列化器，以及为 `INotifyPropertyChanged` 增加便利方法的扩展。命名空间 `VeloxDev.Serialization`。

## VeloxDev.Serialization

### 类：VeloxJsonSerializer

封闭世界序列化器。分同步文件与异步配套文件；两者是同一个静态分部类型。

**签名：** `public static partial class VeloxJsonSerializer`

**同步写入**

| 成员 | 签名 | 说明 |
|---|---|---|
| `Serialize` | `static string Serialize(object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` | 把值写成文档字符串。 |
| `WriteTo` | `static void WriteTo(TextWriter output, object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` | 写入文本写入器。 |
| `WriteTo` | `static void WriteTo(Stream output, object value, bool indented = true, IReadOnlyCollection<Type>? excludedTypes = null)` | 以 UTF-8 写入流；流保持打开。 |
| `WriteValue` | `static void WriteValue(VeloxJsonWriter writer, object? value, Type? declaredType)` | 写一个值；容器写成数组或对象，其余用其注册写入器。 |
| `WriteMap` | `static void WriteMap(VeloxJsonWriter writer, IDictionary map, Type declaredType, Type valueType, bool interfaceKeys)` | 写映射；接口键映射用键的引用 id 作为属性名。 |
| `IsExcluded` | `static bool IsExcluded(Type declaredType)` | 当前写入是否排除该声明类型的成员。 |

**同步读取**

| 成员 | 签名 | 说明 |
|---|---|---|
| `Deserialize<T>` | `static T? Deserialize<T>(string json) where T : class` | 读取文档字符串；文档是 JSON 字面量时返回 `null`。 |
| `Deserialize` | `static object? Deserialize(string json, Type type)` | 读入运行期类型。 |
| `Deserialize<T>` | `static T? Deserialize<T>(TextReader reader) where T : class` | 从读取器流式读取。 |
| `Deserialize` | `static object? Deserialize(TextReader reader, Type type)` | 流式读入运行期类型。 |
| `Deserialize<T>` | `static T? Deserialize<T>(Stream stream) where T : class` | 流式读取 UTF-8，识别字节序标记。 |
| `Deserialize` | `static object? Deserialize(Stream stream, Type type)` | 流式读入运行期类型。 |
| `ReadUnknown` | `static object? ReadUnknown(VeloxJsonReader reader)` | 按令牌形状读取声明类型为 `object` 的值。 |
| `ReadValue` | `static object? ReadValue(VeloxJsonReader reader, Type declaredType, object? existing)` | 读一个值；`existing` 匹配时复用之。 |
| `ReadArray` | `static void ReadArray(VeloxJsonReader reader, IList target, Type elementType)` | 清空并填充列表。 |
| `ReadMap` | `static void ReadMap(VeloxJsonReader reader, IDictionary target, Type keyType, Type valueType, bool interfaceKeys)` | 清空并填充映射。 |

**异步**

| 成员 | 签名 |
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

**异常：** 值为 null、写入器/读取器/类型为 null 时抛 `ArgumentNullException`；值类型没有注册写入器或文档命名了没有读取器的类型时抛 `InvalidOperationException`。

### 类：ViewModelSerializer

面向 `INotifyPropertyChanged` 的扩展，MVVM 生成器会把它加到视图模型上。

**签名：** `public static class ViewModelSerializer`

**同步**

| 成员 | 签名 | 说明 |
|---|---|---|
| `Serialize<T>` | `static string Serialize<T>(this T workflow) where T : INotifyPropertyChanged` | 默认缩进。 |
| `Serialize<T>` | `static string Serialize<T>(this T workflow, SerializationOptions options) where T : INotifyPropertyChanged` | 带选项。 |
| `TryDeserialize<T>` | `static bool TryDeserialize<T>(this string json, out T? workflow) where T : INotifyPropertyChanged` | null、空或畸形输入返回 `false`。 |
| `TryDeserialize<T>` | `static bool TryDeserialize<T>(this string json, SerializationOptions options, out T? workflow) where T : INotifyPropertyChanged` | 带选项。 |
| `Deserialize<T>` | `static T Deserialize<T>(this string json) where T : INotifyPropertyChanged` | 失败时抛出。 |
| `Deserialize<T>` | `static T Deserialize<T>(this string json, SerializationOptions options) where T : INotifyPropertyChanged` | 带选项。 |
| `DeserializeToType` | `static object? DeserializeToType(this VeloxJsonValue value, Type targetType)` | 把 JSON 树读入类型。 |
| `SerializeToTextWriter<T>` | `static void SerializeToTextWriter<T>(this T workflow, TextWriter writer, SerializationOptions? options = null) where T : INotifyPropertyChanged` | 流式写入写入器。 |
| `SerializeToStream<T>` | `static void SerializeToStream<T>(this T workflow, Stream stream, SerializationOptions? options = null) where T : INotifyPropertyChanged` | 以 UTF-8 流式写入流。 |
| `DeserializeFromTextReader<T>` | `static T? DeserializeFromTextReader<T>(this TextReader reader) where T : INotifyPropertyChanged` | 从读取器流式读取。 |
| `DeserializeFromStream<T>` | `static T? DeserializeFromStream<T>(this Stream stream) where T : INotifyPropertyChanged` | 从流式读取。 |
| `SerializeToUtf8Bytes<T>` | `static byte[] SerializeToUtf8Bytes<T>(this T workflow, SerializationOptions? options = null) where T : INotifyPropertyChanged` | UTF-8 字节。 |
| `DeserializeFromUtf8Bytes<T>` | `static T DeserializeFromUtf8Bytes<T>(this byte[] utf8Json, SerializationOptions? options = null) where T : INotifyPropertyChanged` | 从 UTF-8 字节。 |

**异步**

| 成员 | 签名 |
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

流式重载避免构建整份文档字符串；峰值内存是缓冲区加上图。

## 示例

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

读取时集合属性被清空并重新填充，而非追加；集合实例本身复用，因此其订阅得以保留。完整程序见[封闭世界序列化快速开始](../../../1_快速开始/16_封闭世界序列化/index.md)。
