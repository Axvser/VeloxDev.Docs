# 封闭世界序列化

`VeloxJsonSerializer` 通过一个在封闭类型集上编译出的注册表读写归档格式。值由运行时类型注册的 writer 写入，由文档 `$type` 命名的 reader 读取。没有反射兜底。

分析分为两个操作：

- [写入路径](00_写入路径/index.md) — `Serialize`、`WriteValue`、标量/容器分派与注册表查找。
- [读取路径](01_读取路径/index.md) — `Deserialize`、`ReadValue`、引用登记与生成的 reader。

```csharp
var json = workflow.Serialize();
var restored = json.Deserialize<MyViewModel>();
```

命名空间：`VeloxDev.Serialization`。
