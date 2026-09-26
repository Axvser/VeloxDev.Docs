# Workflow System — 命名空间：`VeloxDev.MVVM.Serialization`

`ComponentModelEx`：**现代 TFM（net8.0 / net10.0）基于 System.Text.Json**，`netstandard2.0` 资产仍基于 Newtonsoft，两者产出同一形状的存档。基础设置：多态判别符取**程序集限定名**（与旧档逐字相同，白名单来自编译期组件目录）、引用保留、只写可写属性、接口键字典按引用 id 存取、`NaN` 写字面量。

> 写出侧与旧档有一处已知差异：集合被包成 `{"$id","$values":[]}` 而旧档是裸数组，读侧两种都认。

| 方法 | 签名 |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)`，其中 `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)`（+ options 重载） |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)`（+ options 重载） |
| 异步 | `SerializeAsync`、`DeserializeAsync` |
| 流式 | `SerializeToUtf8Bytes`、`DeserializeFromUtf8Bytes`、`SerializeToTextWriterAsync`、`DeserializeFromTextReaderAsync`、`SerializeToStreamAsync`、`DeserializeFromStreamAsync` |
| 选项 | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)`。三个枚举是这个库自己的（与 Newtonsoft 同名但取值收窄），不再需要 `using Newtonsoft.Json`。 |

**示例** —— 演示树中的保存 / 加载：`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` 的 `Save` 命令（约第 252 行 `var json = this.Serialize();`）；`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs` 的 `SelectWorkflow`（约第 65 行 `json.Deserialize<TreeViewModel>()`，随后 `result.Layout.UpdateCommand.Execute(null)`）。

*源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`。*
