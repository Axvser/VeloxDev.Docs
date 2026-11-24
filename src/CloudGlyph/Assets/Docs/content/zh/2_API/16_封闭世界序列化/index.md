# 封闭世界序列化

`VeloxDev.Serialization` 在不使用反射的情况下写入和读取归档 JSON。生成器遍历编译并为一个归档闭包中的每个类型产出一个读写器，通过模块初始化器注册。闭包外的类型没有写入器，写入它会抛异常而不是回退到反射。

## 类型分组

| 分组 | 类型 | 页面 |
|---|---|---|
| 注解与选项 | `ArchivableAttribute`、`ArchiveAttribute`、`ArchiveOptions`、`SerializationOptions` | [注解与选项](00_注解与选项/index.md) |
| 序列化器入口 | `VeloxJsonSerializer`、`ViewModelSerializer` | [序列化器与视图模型](01_序列化器与视图模型/index.md) |
| 注册表与令牌流 | `VeloxJsonRegistry`、`IVeloxJsonWriter`、`IVeloxJsonReader`、`VeloxJsonWriter`、`VeloxJsonReader`、`VeloxJsonFormat` | [注册表与流](02_注册表与流/index.md) |
| 内存 JSON 树 | `VeloxJsonValue`、`VeloxJsonScalar`、`VeloxJsonArray`、`VeloxJsonObject` | [JSON 树](03_JSON树/index.md) |

## 什么会加入闭包

- 工作流组件（树、节点、插槽或连线视图模型）。
- 带 `[VeloxProperty]` 字段的类型。
- 显式标记 `[Archivable]` 的类型。

生成器随后追踪成员类型、集合元素类型、字典键/值类型、同一编译中的派生类型与接口实现，以及（对开放泛型根）其约束允许的类型。没有任何根可达、且自身不是根的类型不会进入；其他程序集的类型只以本程序集见过的封闭泛型形式进入。

## 文档契约

| 方面 | 规则 |
|---|---|
| 成员顺序 | 声明顺序。改变它会作废已有文档。 |
| 默认成员 | 带公开 setter 的公开属性。 |
| 名称 | `$type` 为 `{Type, AssemblyName}`；成员名默认为 C# 名称，除非 `[Archive(ArchiveOptions.ReName, "…")]` 改变。 |
| 引用 | 首次写入加 `$id`，重复时用 `$ref`；循环得以保留。 |
| 枚举 | 默认写底层整数，除非 `[Archive(ArchiveOptions.EnumName)]`。 |
| 空值 | JSON `null` 字面量。 |

## 保证

- 无反射回退。没有注册写入器的类型抛 `InvalidOperationException`；文档命名了没有读取器的类型同样抛出。
- 回调是 BCL 的 `[OnSerializing]`、`[OnSerialized]`、`[OnDeserializing]`、`[OnDeserialized]`；生成代码直接调用，因此它们必须是 `internal` 或更宽。反序列化回调在该类型所有成员读完后运行。
- 输出与本模块存在之前框架产出的归档格式逐字节一致。

完整控制台程序见[封闭世界序列化快速开始](../../1_快速开始/16_封闭世界序列化/index.md)。
