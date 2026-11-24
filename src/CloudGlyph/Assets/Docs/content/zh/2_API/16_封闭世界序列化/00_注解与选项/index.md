# 注解与选项

决定成员归属与成员形状的特性，以及逐调用格式化选项。命名空间 `VeloxDev.Serialization`。

## VeloxDev.Serialization

### 类：ArchivableAttribute

把类型标记为归档格式的一部分，并可选地命名更多根。

**签名：** `public sealed class ArchivableAttribute : Attribute`

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `ArchivableAttribute(params Type[] additionalRoots)` | 标记类型；每个额外类型作为根加入。 |
| `AdditionalRoots` | `IReadOnlyList<Type> { get; }` | 此声明加入格式的更多类型。 |

**特性用法：** `AttributeTargets.Class | AttributeTargets.Struct`，`Inherited = false`。

作为组件或带 `[VeloxProperty]` 的视图模型无需 `[Archivable]`。它用于普通文档类型——检查点、报告、DTO。命名的类型必须在同一程序集声明；重复命名同一类型没有代价。

### 类：ArchiveAttribute

改变一个成员参与文档的方式。

**签名：** `public sealed class ArchiveAttribute : Attribute`

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `ArchiveAttribute(ArchiveOptions options, object? argument = null)` | `argument` 是 `ReName` 的字符串；其他情况为 `null`。 |
| `Options` | `ArchiveOptions { get; }` | 要改变什么。 |
| `Argument` | `object? { get; }` | `Options` 需要的值。 |

**特性用法：** `AttributeTargets.Property | AttributeTargets.Field`，`Inherited = false`。

### 枚举：ArchiveOptions

**签名：** `[Flags] public enum ArchiveOptions`

| 成员 | 值 | 效果 |
|---|---|---|
| `None` | 0 | 默认规则。 |
| `KeepProperty` | 1 | 包含计算属性（无公开 setter）。它会写入但无法读回。 |
| `KeepField` | 2 | 包含没有对应属性的字段。 |
| `IgnoreField` | 4 | 排除默认规则会取的成员。 |
| `ReName` | 8 | 用 `ArchiveAttribute.Argument` 而非自身名称写入。 |
| `EnumName` | 16 | 把该枚举成员写为名称而非底层数字。适用于枚举与可空枚举。 |

默认成员规则是：带公开 setter 的公开属性，按声明顺序。其余成员除非由某个选项命名，否则被排除。

### 类：SerializationOptions

逐调用覆盖，流式构建后传给 `Serialize` / `Deserialize` / `TryDeserialize` 重载。

**签名：** `public sealed class SerializationOptions`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Create` | `static SerializationOptions Create()` | 空构建器。 |
| `WithIndented` | `SerializationOptions WithIndented()` | 人类可读输出。 |
| `WithCompact` | `SerializationOptions WithCompact()` | 无多余空白。 |
| `WithExcludedPropertyTypes` | `SerializationOptions WithExcludedPropertyTypes(params Type[] types)` | 在整个图中省略**声明类型**与 `types` 精确匹配的每个属性。 |

`WithExcludedPropertyTypes` 用于编译图快照：节点的 `Parent` 声明为 `ITreeComponent`，排除该声明类型可在不排除插槽前向所需父节点（其声明类型不同）的情况下，把整棵树排除在文档之外。过滤器在一次写入期间是环境值，而不是穿过生成代码的参数。

## 示例

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
// 第一个成员写为 "id"，第二个写为 "Attempt"。
```

`Archive` 逐成员应用；`Archivable` 只决定类型是否在闭包内。生成器无法访问的成员会被报告，而不是静默丢弃。
