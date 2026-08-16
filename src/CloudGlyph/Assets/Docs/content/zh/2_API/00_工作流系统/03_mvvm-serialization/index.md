# Workflow System — 命名空间：`VeloxDev.MVVM.Serialization`

`ComponentModelEx`（基于 Newtonsoft）。基础设置：`TypeNameHandling.Auto`、`PreserveReferencesHandling.Objects`、`ReferenceLoopHandling.Ignore`、`NullValueHandling.Include`、`DefaultValueHandling.Include`、`WritablePropertiesOnlyResolver`、`DictionaryKeyConverter`。

| 方法 | 签名 |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)`，其中 `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)`（+ options 重载） |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)`（+ options 重载） |
| 异步 | `SerializeAsync`、`DeserializeAsync` |
| 流式 | `SerializeToUtf8Bytes`、`DeserializeFromUtf8Bytes`、`SerializeToTextWriterAsync`、`DeserializeFromTextReaderAsync`、`SerializeToStreamAsync`、`DeserializeFromStreamAsync` |
| 选项 | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)` |

**示例** —— 演示树中的保存 / 加载：`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`，第 185-193 行（`this.Serialize()`）；`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`，第 46-51 行（`json.Deserialize<TreeViewModel>()` + `Layout.UpdateCommand.Execute(null)`）。

*源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`。*
