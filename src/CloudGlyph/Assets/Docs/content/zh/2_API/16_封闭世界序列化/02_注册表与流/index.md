# 注册表与流

生成器填充的编译期注册表、读写器契约，以及生成代码驱动的令牌游标。命名空间 `VeloxDev.Serialization`。

## VeloxDev.Serialization

### 类：VeloxJsonRegistry

封闭世界背后的编译期事实：每个类型对应的写入器与读取器、每个类型的线格式名称，以及如何构造嵌套容器。

**签名：** `public static class VeloxJsonRegistry`

| 成员 | 签名 | 说明 |
|---|---|---|
| `RegisterContainerFactory` | `static void RegisterContainerFactory(Type type, Func<object> factory)` | 注册如何构造文档作为值持有的嵌套容器（`Dictionary<K,V>`、`List<T>`）。 |
| `ContainerFactoryFor` | `static Func<object>? ContainerFactoryFor(Type type)` | 工厂，或 `null`。 |
| `RegisterWriter` | `static void RegisterWriter(Type type, IVeloxJsonWriter writer, bool declaresType)` | 注册类型写入器。`declaresType` 为 false 时已有条目优先。 |
| `RegisterReader` | `static void RegisterReader(Type type, IVeloxJsonReader reader, bool declaresType)` | 注册类型读取器，优先级同上。 |
| `RegisterName` | `static void RegisterName(Type type, string name)` | 注册线格式名称（`Namespace.Type, AssemblyName`，泛型同样写法）。 |
| `NameOf` | `static string? NameOf(Type type)` | 线格式名称，或 `null`。 |
| `TypeOf` | `static Type? TypeOf(string name)` | 文档名称对应的类型，或 `null`。 |
| `WriterFor` | `static IVeloxJsonWriter? WriterFor(Type type)` | 写入器，或 `null`。 |
| `ReaderFor` | `static IVeloxJsonReader? ReaderFor(Type type)` | 读取器，或 `null`。 |

注册发生在生成的 `[ModuleInitializer]` 方法中，因此表在 `Main` 之前就已完整。表以不可变快照发布，所以查找无需加锁。

### 接口：IVeloxJsonWriter

每个可序列化类型一个生成实现。

**签名：** `public interface IVeloxJsonWriter`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Write` | `void Write(VeloxJsonWriter writer, object value, Type? declaredType)` | 写入实例成员。运行期类型与 `declaredType` 不同时写入类型名。 |
| `WriteAsync` | `Task WriteAsync(VeloxJsonWriter writer, object value, Type? declaredType)` | 可等待形式。 |

### 接口：IVeloxJsonReader

**签名：** `public interface IVeloxJsonReader`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Create` | `object Create()` | 创建待读入的空实例。 |
| `Read` | `void Read(VeloxJsonReader reader, object target)` | 把成员读入 `target`，消费到右花括号。 |
| `ReadAsync` | `Task ReadAsync(VeloxJsonReader reader, object target)` | 可等待形式。 |

### 枚举：VeloxJsonFormat

**签名：** `public enum VeloxJsonFormat`

| 成员 | 含义 |
|---|---|
| `Compact` | 无空白。 |
| `Indented` | 每行一个成员，缩进两个空格。 |

### 类：VeloxJsonWriter

归档格式写入器：精确缩进、分隔符、数字拼法与 `$id` / `$type` / `$ref` 记账。单次使用，非线程安全。

**签名：** `public sealed partial class VeloxJsonWriter`

**构造函数：** `public VeloxJsonWriter(TextWriter writer, bool indented = true)`

| 成员 | 签名 | 说明 |
|---|---|---|
| `GetOrAddReference` | `int GetOrAddReference(object instance)` | 已写对象的 id，或新分配的 id。 |
| `WriteStartObject` | `bool WriteStartObject(object instance, Type? declaredType)` | 开始对象；若改为输出引用则返回 false。 |
| `WriteStartObjectWithoutReference` | `void WriteStartObjectWithoutReference()` | 开始无 `$id` / `$type` 的对象。 |
| `WriteEndObject` | `void WriteEndObject()` | 结束对象。 |
| `WriteStartArray` | `void WriteStartArray()` | 开始数组。 |
| `WriteNextElement` | `void WriteNextElement()` | 写入元素前的分隔符；空数组不调用。 |
| `WriteEndArray` | `void WriteEndArray()` | 结束数组。 |
| `WriteMemberName` | `void WriteMemberName(string name)` | 写属性名；值紧随其后。 |
| `WriteString` | `void WriteString(string? value)` | 写字符串；`null` 写字面量。 |
| `WriteNull` | `void WriteNull()` | 写 JSON `null`。 |
| `WriteBoolean` | `void WriteBoolean(bool value)` | 写 `true` / `false`。 |
| `WriteInt32` / `WriteInt64` | `void WriteInt32(int value)`、`void WriteInt64(long value)` | 整数。 |
| `WriteDouble` | `void WriteDouble(double value)` | 最短往返；整数值补 `.0`；非有限值写成字符串。 |
| `WriteSingle` | `void WriteSingle(float value)` | 与 double 相同的拼写。 |
| `WriteDecimal` | `void WriteDecimal(decimal value)` | 十进制数。 |
| `WriteGuid` | `void WriteGuid(Guid value)` | 连字符小写。 |
| `WriteRawValue` | `void WriteRawValue(string json)` | 已自带 JSON 拼写的值。 |

异步配套增加 `CompleteAsync`，以及每种形状与标量写入器的 `*Async` 版本（`WriteStartObjectAsync`、`WriteEndObjectAsync`、`WriteStartArrayAsync`、`WriteNextElementAsync`、`WriteEndArrayAsync`、`WriteMemberNameAsync`、`WriteStringAsync`、`WriteNullAsync`、`WriteBooleanAsync`、`WriteInt32Async`、`WriteInt64Async`、`WriteDoubleAsync`、`WriteSingleAsync`、`WriteDecimalAsync`、`WriteGuidAsync`、`WriteRawValueAsync`、`WriteStartObjectWithoutReferenceAsync`）。

### 类：VeloxJsonReader

生成读取器所用的对象协议游标。顺序无关：成员按名称分派。单次使用，非线程安全。

**签名：** `public sealed partial class VeloxJsonReader`

**构造函数**

| 签名 |
|---|
| `VeloxJsonReader(string json)` |
| `VeloxJsonReader(TextReader reader, int bufferSize = 8192)` |
| `VeloxJsonReader(Stream stream, int bufferSize = 8192)`——UTF-8，识别字节序标记，保持流打开 |

| 成员 | 签名 | 说明 |
|---|---|---|
| `AtEnd` | `bool AtEnd { get; }` | 文档是否已消费完。 |
| `BeginObject` | `bool BeginObject(out int referenceId, out string? typeName)` | 开始对象；文档为 `$ref` 时返回 false。 |
| `NextMember` | `bool NextMember(out string name)` | 读下一个成员名。 |
| `NextMember` | `bool NextMember()` | 前进但不物化名称；配合 `MemberNameEquals`。 |
| `MemberNameEquals` | `bool MemberNameEquals(string name)` | 就地比较刚读到的成员名。 |
| `FinishObject` | `void FinishObject()` | 消费右花括号。 |
| `BeginArray` | `void BeginArray()` | 开始数组。 |
| `NextElement` | `bool NextElement()` | 移到下一个元素。 |
| `FinishArray` | `void FinishArray()` | 消费右方括号。 |
| `RegisterReference` | `void RegisterReference(int referenceId, object instance)` | 在读成员前让对象可按 id 解析。 |
| `ResolveReference` | `object? ResolveReference(int referenceId)` | id 对应的对象。 |
| `NextIsString` / `NextIsArray` / `NextIsObject` / `NextIsNull` | `bool` | 令牌前瞻。 |
| `ReadNullIfPresent` | `bool ReadNullIfPresent()` | 当前为 `null` 字面量时消费它。 |
| `ReadEnum` | `object? ReadEnum(Type enumType)` | 读取写为名称的枚举，或 `null`。 |
| `ReadString` | `string? ReadString()` | 读字符串；JSON `null` 读作 `null`。 |
| `ReadText` | `string ReadText()` | 读值的文本，带引号或裸写。 |
| `ReadBoolean` | `bool ReadBoolean()` | 读布尔；否则抛 `FormatException`。 |
| `ReadInt32` / `ReadInt64` | `int` / `long` | 整数。 |
| `ReadDouble` | `double ReadDouble()` | 含 `"NaN"`、`"Infinity"`、`"-Infinity"` 拼写。 |
| `ReadSingle` | `float ReadSingle()` | 单精度。 |
| `ReadDecimal` | `decimal ReadDecimal()` | 十进制数。 |
| `ReadGuid` | `Guid ReadGuid()` | 从连字符文本形式。 |
| `SkipValue` | `void SkipValue()` | 跳过任意形状、任意深度的单个值。 |

异步配套镜像该表面：`AtEndAsync`、`BeginObjectAsync`、`NextMemberAsync`、`ReadMemberNameAsync`、`FinishObjectAsync`、`BeginArrayAsync`、`NextElementAsync`、`FinishArrayAsync`、`NextIsNullAsync`、`ReadNullIfPresentAsync`、`NextIsStringAsync`、`NextIsArrayAsync`、`NextIsObjectAsync`、`ReadEnumAsync`、`ReadStringAsync`、`ReadTextAsync`、`ReadBooleanAsync`、`ReadInt32Async`、`ReadInt64Async`、`ReadDoubleAsync`、`ReadSingleAsync`、`ReadDecimalAsync`、`ReadGuidAsync`、`SkipValueAsync`。

## 示例

```csharp
using System.IO;
using VeloxDev.Serialization;

var writer = new StringWriter();
VeloxJsonSerializer.WriteTo(writer, note);      // NoteViewModel 的生成写入器
string document = writer.ToString();

using var stream = new MemoryStream();
VeloxJsonSerializer.WriteTo(stream, note);      // UTF-8，无 BOM，流保持打开

var reader = new VeloxJsonReader(document);
NoteViewModel? back = VeloxJsonSerializer.Deserialize<NoteViewModel>(document);
```

应用代码很少直接触及读写器；生成的读写器与 `VeloxJsonSerializer` 覆盖常规路径。此层用于自定义输出或令牌级检查。
