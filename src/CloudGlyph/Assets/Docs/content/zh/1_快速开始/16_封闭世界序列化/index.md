# 封闭世界序列化

把视图模型序列化成 JSON 再读回，全程不使用反射。只有生成器为其编译了读写器的类型才能出现在文档里；闭包之外的类型会明确抛错，而不是退回反射。

## 1. 前置条件

- **`VeloxDev.Core` 支持的目标框架**：`netstandard2.0;netframework4.6.1;net5.0;netcoreapp3.0;net8.0`。本示例使用 `net8.0`。
- **`VeloxDev.Core`** 与 **`VeloxDev.Core.Generator`**。生成器遍历整个编译，为归档闭包中的每个类型发出读写器，并通过模块初始化器注册进 `VeloxJsonRegistry`。
- .NET SDK 8.0 或更高。无需任何服务。

## 2. 安装/引入依赖

```text
dotnet new console -n SerializationQuickStart
cd SerializationQuickStart
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 两个包还原成功。首次构建后编译出的读写器及其注册（在 `Main` 之前运行）就已就位；设置 `<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>` 可把 `<程序集>_VeloxJson.g.cs` 写到 `obj/` 下。

## 3. 基础配置/注册

类型通过三种方式之一加入闭包：它是工作流组件（tree/node/slot/link 视图模型）；它带有 `[VeloxProperty]` 字段；或显式标了 `[Archivable]`。满足前两条的视图模型不需要额外特性。

```csharp
using System.Collections.ObjectModel;
using VeloxDev.MVVM;

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "";
    [VeloxProperty] private int _priority;
    [VeloxProperty] private ObservableCollection<string> _tags = new();
}
```

**预期结果：** 生成的 JSON 成员是 `Title`、`Priority`、`Tags`，按此声明顺序。成员顺序是逐字节契约：改动它会作废已经保存的文档。

## 4. 核心用法（逐步构建）

### 4.1 序列化与反序列化视图模型

`ViewModelSerializer` 扩展方法要求 `INotifyPropertyChanged`，MVVM 生成器会为类补上该接口。`Serialize()` 输出缩进格式；`Deserialize<T>()` 失败时抛错，`TryDeserialize<T>()` 失败时返回 `false`。

```csharp
var note = new NoteViewModel { Title = "Ship", Priority = 2 };
note.Tags.Add("docs");

var json = note.Serialize();                    // 缩进
var compact = note.Serialize(
    SerializationOptions.Create().WithCompact());

var restored = json.Deserialize<NoteViewModel>();
if (json.TryDeserialize<NoteViewModel>(out var safe))
{
    // safe 是同一张图；失败时为 null
}
```

**预期结果：** `json` 是一个 JSON 对象，成员为 `Title`、`Priority`、`Tags`；`restored.Title` 为 `"Ship"`，`restored.Priority` 为 2，`restored.Tags` 含 `"docs"`。标签集合是清空后重填，不是追加。

### 4.2 用 `[Archivable]` 纳入普通类型

不是视图模型的文档类型——检查点、报告、DTO——可自行声明。它不需要 `[VeloxProperty]`，也不必是 `partial`；public 且带 public setter 的属性默认进入文档。

```csharp
using VeloxDev.Serialization;

[Archivable]
public sealed class Checkpoint
{
    [Archive(ArchiveOptions.ReName, "id")]
    public string? NodeId { get; set; }

    public int Attempt { get; set; }
}

var json = VeloxJsonSerializer.Serialize(new Checkpoint { NodeId = "node-1", Attempt = 3 });
var back = VeloxJsonSerializer.Deserialize<Checkpoint>(json);
```

**预期结果：** 文档把第一个成员写成 `"id"`（不是 `"NodeId"`），第二个写成 `"Attempt"`；`back.NodeId` 为 `"node-1"`，`back.Attempt` 为 3。`Archivable` 也可点名同一程序集内声明的更多根类型：`[Archivable(typeof(Rule), typeof(RuleSet))]`。

### 4.3 选择进入文档的成员

默认规则是：public 且有 public setter 的属性，按声明顺序。`[Archive]` 逐个成员改变这一点：

| 选项 | 作用 |
| --- | --- |
| `KeepProperty` | 纳入计算属性（无 public setter）；它会被写出，但无法读回 |
| `KeepField` | 纳入没有对应属性的字段 |
| `IgnoreField` | 排除默认规则本会纳入的成员 |
| `ReName` | 用 `Argument` 而不是成员原名写出 |
| `EnumName` | 把这个枚举成员写成名字，而不是底层数字 |

**预期结果：** 计算属性不加 `KeepProperty` 就不会进入文档；改名的成员能往返，因为读侧应用同一映射。

### 4.4 闭包含有什么、不含什么

当编译能触达某类型时，生成器把它纳入，再顺着它的成员类型、集合元素类型、字典键/值类型展开；对带根标记的开放泛型，还纳入其约束允许的类型。同一程序集内声明的派生类与接口实现会自动纳入。别的程序集里的类型只有在本程序集见过其封闭泛型实例时才能参与；否则会在生成期报错，而不是被静默丢掉。

没有反射兜底。写入没有注册读写器的类型会抛 `InvalidOperationException`；读取 `$type` 没有读器的文档同样抛错。

```csharp
try
{
    VeloxJsonSerializer.Serialize(new { Id = 1 });
}
catch (InvalidOperationException error)
{
    Console.WriteLine(error.Message);
}
```

**预期结果：** 匿名类型在闭包之外，消息会点名该类型并说明没有注册写入器。

### 4.5 流式重载

同一序列化器还提供 `SerializeToTextWriter`、`SerializeToStream`、`SerializeToUtf8Bytes`、`DeserializeFromTextReader`、`DeserializeFromStream` 与 `DeserializeFromUtf8Bytes`，每个都有异步版本。它们不构建整份文档字符串；峰值内存是读写器缓冲加上对象图。

```csharp
byte[] utf8 = note.SerializeToUtf8Bytes();
NoteViewModel same = utf8.DeserializeFromUtf8Bytes<NoteViewModel>();
```

**预期结果：** `same` 与从字符串形式读出的图一致。

## 5. 验证

运行完整程序。第一份文档包含 `Title`、`Priority`、`Tags`；还原行打印 `restored: Ship / 2 / 2 tags`；检查点文档包含 `"id"` 与 `"Attempt"` 并能读回；匿名类型打印缺失写入器的消息。

## 6. 完整代码

```csharp
using System;
using System.Collections.ObjectModel;
using VeloxDev.MVVM;
using VeloxDev.Serialization;

var note = new NoteViewModel { Title = "Ship the wiki", Priority = 2 };
note.Tags.Add("docs");
note.Tags.Add("wiki");

var json = note.Serialize();
Console.WriteLine(json);

var restored = json.Deserialize<NoteViewModel>();
Console.WriteLine($"restored: {restored.Title} / {restored.Priority} / {restored.Tags.Count} tags");

var compact = note.Serialize(SerializationOptions.Create().WithCompact());
Console.WriteLine($"compact length: {compact.Length}");

var checkpoint = new Checkpoint { NodeId = "node-1", Attempt = 3 };
var checkpointJson = VeloxJsonSerializer.Serialize(checkpoint);
Console.WriteLine(checkpointJson);

var back = VeloxJsonSerializer.Deserialize<Checkpoint>(checkpointJson);
Console.WriteLine($"checkpoint: {back?.NodeId} / {back?.Attempt}");

try
{
    VeloxJsonSerializer.Serialize(new { Id = 1 });
}
catch (InvalidOperationException error)
{
    Console.WriteLine($"outside the closure: {error.Message}");
}

public partial class NoteViewModel
{
    [VeloxProperty] private string _title = "";
    [VeloxProperty] private int _priority;
    [VeloxProperty] private ObservableCollection<string> _tags = new();
}

[Archivable]
public sealed class Checkpoint
{
    [Archive(ArchiveOptions.ReName, "id")]
    public string? NodeId { get; set; }

    public int Attempt { get; set; }
}
```

入口点已在 `Src/Core/VeloxDev.Core/Serialization/VeloxJsonSerializer.cs` 与 `ViewModelSerializer.cs` 核验；端到端往返参照 `Src/Test/Unit/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowSerializationTests.cs`。

## 7. 运行声明

- ⚠️ 未实际运行——仅于 2026-11-25 静态核验。已对照序列化器、注册表、注解与选项源码，`VeloxJson` 生成器（`Src/Generators/VeloxDev.Core.Generator/VeloxJson.cs`、`Base/VeloxJsonModel.cs`、`Writers/VeloxJsonCodeWriter.cs`）以及序列化测试核验。本环境未执行 NuGet 还原或运行。
