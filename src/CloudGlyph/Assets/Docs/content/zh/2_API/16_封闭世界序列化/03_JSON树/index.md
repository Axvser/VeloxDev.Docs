# JSON 树

一种内存 JSON 值，用于构建工具结果与配置载荷，并以归档格式相同的拼写规则渲染。命名空间 `VeloxDev.Serialization`。

## VeloxDev.Serialization

### 类：VeloxJsonValue

抽象树节点。标量可从原语隐式转换。

**签名：** `public abstract class VeloxJsonValue`

| 成员 | 签名 | 说明 |
|---|---|---|
| `ToJson` | `string ToJson(VeloxJsonFormat format = VeloxJsonFormat.Compact)` | 把树渲染为文本。 |
| `ToString` | `override string ToString()` | `ToJson()`。 |
| `IsNull` | `virtual bool IsNull { get; }` | 是否为 JSON `null`。 |
| `Materialize` | `virtual object? Materialize()` | 把树转成 CLR 值：`string`、`bool`、`long` / `double`、`Dictionary<string, object?>`、`List<object?>` 或 `null`。 |
| `DeepEquals` | `virtual bool DeepEquals(VeloxJsonValue? other)` | 逐成员、逐元素相等；成员顺序不参与判断。 |
| `From` | `static VeloxJsonValue From(object? value)` | 从值构建树。归档序列化器认识的类型走其生成写入器，而非反射遍历。 |
| `Parse` | `static VeloxJsonValue Parse(string json)` | 把文本解析为树；非法 JSON 抛 `FormatException`。 |
| `Null` | `static VeloxJsonValue Null { get; }` | JSON `null` 字面量。 |

**隐式转换：** `string?`、`bool`、`int`、`long` 与 `double` 到 `VeloxJsonValue`。

### 类：VeloxJsonScalar

字符串、数字、布尔或 `null`，以将要写出的文本保存。

**签名：** `public sealed class VeloxJsonScalar : VeloxJsonValue`

| 成员 | 类型/签名 | 说明 |
|---|---|---|
| `Text` | `string? { get; }` | 将要写出的文本。 |
| `AsString` | `string? AsString()` | 文本。 |
| `AsInt32` | `int AsInt32()` | 数字；不是数字时为 `0`。 |
| `AsBoolean` | `bool AsBoolean()` | `text == "true"`。 |
| `IsNumber` | `bool { get; }` | 裸数字字面量；带引号的数字字符串仍是文本。 |
| `IsText` | `bool { get; }` | 是否来自带引号字符串。 |
| `DeepEquals` / `Materialize` | 重写 | 种类与文本都比较。 |

### 类：VeloxJsonArray

有序数组。

**签名：** `public sealed class VeloxJsonArray : VeloxJsonValue, IEnumerable<VeloxJsonValue>`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Count` | `int { get; }` | 元素数。 |
| `this[int]` | `VeloxJsonValue this[int index] { get; }` | 指定位置的元素。 |
| `Add` | `void Add(VeloxJsonValue value)` | 追加元素；`null` 变成 JSON 字面量。 |
| `Add` | `void Add(object? value)` | 追加由 `From` 构建的元素。 |
| `Clear` | `void Clear()` | 移除所有元素。 |
| `GetEnumerator` | `IEnumerator<VeloxJsonValue> GetEnumerator()` | 按顺序枚举。 |

### 类：VeloxJsonObject

保持插入顺序的对象。

**签名：** `public sealed class VeloxJsonObject : VeloxJsonValue, IEnumerable<KeyValuePair<string, VeloxJsonValue>>`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Count` | `int { get; }` | 成员数。 |
| `Names` | `IEnumerable<string> { get; }` | 按顺序的成员名。 |
| `this[string]` | `VeloxJsonValue? this[string name] { get; set; }` | 获取或设置成员。设置已存在成员就地替换；设为 `null` 移除。 |
| `Has` | `bool Has(string name)` | 是否有该成员。 |
| `Add` | `void Add(string name, VeloxJsonValue value)` | 添加或替换成员。 |
| `GetEnumerator` | `IEnumerator<KeyValuePair<string, VeloxJsonValue>> GetEnumerator()` | 按顺序枚举成员。 |
| `ToDictionary` | `Dictionary<string, object?> ToDictionary()` | 物化后的映射。 |

## 示例

```csharp
using VeloxDev.Serialization;

var result = new VeloxJsonObject();
result["ok"] = true;
result["count"] = 3;
result["items"] = new VeloxJsonArray { "alpha", "beta" };

string compact = result.ToJson(VeloxJsonFormat.Compact);
string indented = result.ToJson(VeloxJsonFormat.Indented);

VeloxJsonValue parsed = VeloxJsonValue.Parse(compact);
Console.WriteLine(parsed.DeepEquals(result));          // True
var map = (Dictionary<string, object?>)parsed.Materialize()!;
```

## 说明

- 从文档读到的标量以文本返回而非类型化值；用 `AsInt32` / `AsBoolean` 读取。
- `From` 处理标量、字典（含 `IReadOnlyDictionary<string, object?>`）、可枚举对象，以及归档序列化器有写入器的任意类型。其余抛 `InvalidOperationException`。
- `DeepEquals` 忽略成员顺序，状态快照用它区分一次载荷与下一次载荷。
