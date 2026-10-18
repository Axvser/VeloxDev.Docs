# 序列化 — 归档一个视图模型，再把它重建出来

`VeloxDev.Serialization` 把生成过的对象图写成 JSON，再读回来。全程没有反射、没有运行期注册：只有当源生成器为某个类型编出了读写器，它才会被写出去。工作流树只是调用方之一；这套引擎能为任何标注过的视图模型归档。

## 1. 前置条件

| 需要 | 原因 |
|---|---|
| .NET SDK 8.0 或更高 | 生成器基于 Roslyn 4.8 构建，也就是 .NET 8 SDK 自带的编译器 |
| `VeloxDev.Core` 声明的目标框架之一：`netstandard2.0`、`netframework4.6.1`、`net5.0`、`netcoreapp3.0`、`net8.0` | `VeloxDev.Core` 10.0.0 多目标这些框架；选应用已经在用的那一档 |
| NuGet 访问 | 还原 `VeloxDev.Core` 与 `VeloxDev.Core.Generator` |

运行期不涉及任何服务、文件或网络访问。

## 2. 安装

```powershell
dotnet new console -n ArchiveDemo
cd ArchiveDemo
dotnet add package VeloxDev.Core --version 10.0.0
dotnet add package VeloxDev.Core.Generator --version 10.0.0
```

**预期结果：** 还原以 0 退出，项目里可以 `using VeloxDev.Serialization;`。`VeloxDev.Core` 提供运行期与 `[VeloxProperty]`；`VeloxDev.Core.Generator` 是编出读写器对的分析器。当你用 `ProjectReference` 引用 Core 时，必须把生成器引用显式写上 —— 分析器资产不会随项目引用传递。

## 3. 标注一个类型

序列化是**闭世界**的：只有当生成器为某个类型编出了读写器，它才能往返。进入闭世界有四条路（`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:588-614`）：

| 进入方式 | 适用于 |
|---|---|
| 实现四个工作流组件接口之一 | 工作流树、节点、槽、连线 |
| 带一个 `[WorkflowBuilder.*]` 特性 | 由模板生成出来的组件 |
| 有一个 `[VeloxProperty]` **字段** | 你自己的 ViewModel —— 本页走这条路 |
| 贴 `[Archivable]` | 不是 ViewModel 的普通文档 |

```csharp
using VeloxDev.MVVM;                    // [VeloxProperty]

public sealed partial class Inventory
{
    [VeloxProperty] private string name = "";
    [VeloxProperty] private int count;
}
```

类必须是 `partial`：生成器会把每个字段提升成可观察属性，同时让该类型实现 `INotifyPropertyChanged`。

**预期结果：** 项目仍能构建，`Inventory` 上出现了 public 的 `Name` 与 `Count` 属性。

## 4. 序列化并重建

```csharp
using VeloxDev.Serialization;           // Serialize<T> / Deserialize<T>

var before = new Inventory();
before.Name = "bolts";
before.Count = 42;

string json = before.Serialize();        // 整个对象图 → JSON
Inventory after = json.Deserialize<Inventory>();
```

**预期结果：** `after.Name == "bolts"` 且 `after.Count == 42` —— 重建出来的实例先走了无参构造函数，随后成员被写入。

`TryDeserialize<T>(out var copy)` 是不抛异常的版本：文本为 null、空白或畸形时返回 `false`。

### 你拿到的是哪个入口

有两个入口，§3 选的那条路决定用哪一个：

| 入口 | 约束 | 适用 |
|---|---|---|
| `ViewModelSerializer.Serialize<T>` / `.Deserialize<T>` | `where T : INotifyPropertyChanged` | `[VeloxProperty]` 那条路 —— 视图模型 |
| `VeloxJsonSerializer.Serialize(object, …)` / `.Deserialize<T>` | `where T : class` | `[Archivable]` 那条路 —— 普通文档。`CheckpointEx` 调用的就是它 |

### 往返失败时

| 症状 | 原因 | 处理 |
|---|---|---|
| `InvalidOperationException`，说某类型 "has no registered JSON writer" 或 "reader" | 该类型从未进入闭世界 | 贴 `[Archivable]`，或让它从已进入闭世界的类型可达 |
| 成员没有出现在文档里 | 它没有 public setter | `[Archive(ArchiveOptions.KeepProperty)]` 能写出去 —— 但仍然读不回来 |
| 枚举回来变成了数字 | 枚举默认按底层整数写出 | 在该成员上贴 `[Archive(ArchiveOptions.EnumName)]`，写出值名 |
| 读取时抛 `InvalidOperationException` | 文档缺少 `required` 或 `[JsonRequired]` 成员 | 写出该成员，或去掉必填约束 |
| `object` 成员回来变成字典、`long` 或 `string` | 声明没有点名的 CLR 类型无法恢复 | 在成员上声明具体类型 |

这个格式**不能**和 `System.Text.Json` 或 Newtonsoft 互通：类型判别符、集合形状和成员集都不同；外来的类型标签解析不出来 —— 读侧会退回声明类型。

## 5. 验证

```powershell
dotnet run
```

**预期结果：** 先打印出 JSON 文档，随后打印 `round-trip ok: True`：

```text
{
  "$id": "1",
  "Name": "bolts",
  "Count": 42
}
round-trip ok: True
```

引擎自己的测试套件是上述行为的权威（在仓库根目录运行）：

```bash
dotnet test Src/Core/VeloxDev.Core.Test --filter "FullyQualifiedName~Serialization"
dotnet test Src/Core/VeloxDev.Core.Extension.Test --filter "FullyQualifiedName~Serialization"
```

`ShapeRoundTripTests` 与 `ElementScalarRoundTripTests` 把同步、异步两条链路钉到同一种拼写，`SerializationGoldenTests` 逐字节比较整份文档，`RegistryOwnershipTests` 钉住「声明方优先」规则。

## 6. 完整代码

把 `Program.cs` 的内容替换为：

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

- ✅ **已于 2026-10-18 实际构建并运行**，使用的是本仓库本地构建的 `VeloxDev.Core` 10.0.0（`net8.0`）与 `VeloxDev.Core.Generator`（Debug）程序集。NuGet 安装命令本身没有重跑；代码与生成器路径相同。记录输出：

```text
{
  "$id": "1",
  "Name": "bolts",
  "Count": 42
}
round-trip ok: True
```

所有标识符也已对着代码树核过：`[VeloxProperty]`（`Src/Core/VeloxDev.Core/MVVM/VeloxPropertyAttribute.cs`）、`Serialize<T>` / `Deserialize<T>`（`Src/Core/VeloxDev.Core/Serialization/ViewModelSerializer.cs:109,151`）、生成器的提升规则（`Src/Generators/VeloxDev.Core.Generator/Writers/MVVMWriter.cs:381`、`:998`）。
