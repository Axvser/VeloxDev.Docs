# 序列化 — 归档一个视图模型，再把它建回来

`VeloxDev.Serialization` 把对象图写成 JSON、再读回来 —— 没有反射、没有要注册的特性、也没有要配置的序列化器实例。它是一个**独立的模块**：为**任意**视图模型归档，工作流树只是它的调用方之一。

## 1. 前置条件

| 需要 | 为什么 |
|---|---|
| 一个目标框架为 `net8.0` 的 .NET 项目（或 `VeloxDev.Core` 支持的任一次档：`netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0`） | `VeloxDev.Core` 多目标；挑你的应用已经在用的那一档 |
| 能构建该档的 .NET SDK | 任何能构建所选 TFM 的 SDK |

不涉及任何服务、文件或网络访问。

## 2. 安装

```powershell
dotnet new console -n ArchiveDemo
cd ArchiveDemo
dotnet add package VeloxDev.Core
```

**预期结果：** 还原成功，且项目可以 `using VeloxDev.Serialization;`。源生成器（`VeloxDev.Core.Generator`）作为包分析器随包到达，所以它在本项目里自动生效，不需要第二次引用。

## 3. 标注一个类型

序列化是**闭世界**的：只有当生成器为某个类型编出了读写器，它才能往返。进入闭世界有四条路（`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:588-614`）：

| 进入方式 | 适用于 |
|---|---|
| 实现四个工作流组件接口之一 | 工作流树、节点、槽位、连线 |
| 带一个 `[WorkflowBuilder.*]` 特性 | 由模板生成出来的组件 |
| 有一个 `[VeloxProperty]` **字段** | 你自己的 ViewModel —— 本页走这条路 |
| 贴 `[Archivable]` | 不是 ViewModel 的普通文档类型 |

```csharp
using VeloxDev.MVVM;                    // [VeloxProperty]

public sealed partial class Inventory
{
    [VeloxProperty] private string name = "";
    [VeloxProperty] private int count;
}
```

类必须是 `partial`：生成器会把每个字段提升成一个可观察属性，同时让该类型实现 `INotifyPropertyChanged`。

**预期结果：** 项目仍能构建，且 `Inventory` 现在有了公开的 `Name` 与 `Count` 属性。

## 4. 序列化与重建

```csharp
using VeloxDev.Serialization;           // Serialize<T> / Deserialize<T>

var before = new Inventory();
before.Name = "bolts";
before.Count = 42;

string json = before.Serialize();        // 整张对象图 → JSON
Inventory after = json.Deserialize<Inventory>();
```

**预期结果：** `after.Name == "bolts"`、`after.Count == 42` —— 重建的实例先经无参构造，然后成员被写入。

`TryDeserialize<T>(out var copy)` 是不抛异常的版本：null、空白或畸形文本时返回 `false`。

### 你拿到的是哪个入口

有两个，§3 里你走的那条路决定用哪个：

| 入口 | 约束 | 用于 |
|---|---|---|
| `ViewModelSerializer.Serialize<T>` / `.Deserialize<T>` | `where T : INotifyPropertyChanged` | `[VeloxProperty]` 那条路 —— ViewModel |
| `VeloxJsonSerializer.Serialize(object, …)` / `.Deserialize<T>` | `where T : class` | `[Archivable]` 那条路 —— 普通文档。`CheckpointEx` 调的就是它 |

### 往返出错的四种形态

| 症状 | 原因 | 修法 |
|---|---|---|
| `MissingWriter` / `MissingReader` | 该类型从未进入闭世界。 | 贴 `[Archivable]`，或从已有入口的类型走到它。 |
| 成员在文档里不存在 | 它没有 public setter。 | `[Archive(ArchiveOptions.KeepProperty)]` 能写出去 —— 但**仍然读不回来**。 |
| 枚举读回来成了数字 | 枚举默认按底层整数写。 | 在**那一个成员**上贴 `[Archive(ArchiveOptions.EnumName)]`，改写成员名。 |
| 读取时抛 `InvalidOperationException` | 文档缺了一个 `required` 成员。 | 把该成员写进去，或去掉 `required`。 |

该格式与 `System.Text.Json`、Newtonsoft **不互通**：类型判别符、集合形状、成员集来源三处都不同，外来的类型标签查不到 —— 读侧会退回声明类型。

## 5. 验证

上述行为由模块自己的测试套件钉住：

```bash
dotnet test Src/Core/VeloxDev.Core.Test --filter "FullyQualifiedName~Serialization"
dotnet test Src/Core/VeloxDev.Core.Extension.Test --filter "FullyQualifiedName~Serialization"
```

`ShapeRoundTripTests` 与 `ElementScalarRoundTripTests` 把同步/异步两条链拴成同一套拼写，`SerializationGoldenTests` 逐字节比对整份文档，`RegistryOwnershipTests` 守住「声明方优先」那条规则。

## 6. 完整代码

```csharp
using System;
using VeloxDev.MVVM;
using VeloxDev.Serialization;

namespace ArchiveDemo
{
    public sealed partial class Inventory
    {
        [VeloxProperty] private string name = "";
        [VeloxProperty] private int count;
    }

    public static class Program
    {
        public static void Main()
        {
            var before = new Inventory();
            before.Name = "bolts";
            before.Count = 42;

            string json = before.Serialize();
            Console.WriteLine(json);

            Inventory after = json.Deserialize<Inventory>();
            bool same = after.Name == before.Name && after.Count == before.Count;
            Console.WriteLine($"round-trip ok: {same}");
        }
    }
}
```

## 7. 运行声明

- ⚠️ **未实际运行 —— 仅静态核验。** 每个标识符都回树里核过：`[VeloxProperty]`（`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`）、`Serialize<T>` / `Deserialize<T>`（`Src/Core/VeloxDev.Core/Serialization/ViewModelSerializer.cs:109,151`），以及生成器的提升规则（`Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs:381`、`:998`）。本页的程序**没有**被执行过，所以 JSON 的确切文本**不作断言** —— 只断言往返相等。
