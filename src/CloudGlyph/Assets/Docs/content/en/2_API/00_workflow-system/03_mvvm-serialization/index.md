# Workflow System — Namespace: `VeloxDev.MVVM.Serialization`

`ComponentModelEx` (Newtonsoft based). Base settings: `TypeNameHandling.Auto`, `PreserveReferencesHandling.Objects`, `ReferenceLoopHandling.Ignore`, `NullValueHandling.Include`, `DefaultValueHandling.Include`, `WritablePropertiesOnlyResolver`, `DictionaryKeyConverter`.

| Method | Signature |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)` where `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)` (+ options overload) |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)` (+ options overload) |
| Async | `SerializeAsync`, `DeserializeAsync` |
| Streaming | `SerializeToUtf8Bytes`, `DeserializeFromUtf8Bytes`, `SerializeToTextWriterAsync`, `DeserializeFromTextReaderAsync`, `SerializeToStreamAsync`, `DeserializeFromStreamAsync` |
| Options | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)` |

**Example** — save/load in the demo tree: `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, lines 185-193 (`this.Serialize()`), and `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, lines 46-51 (`json.Deserialize<TreeViewModel>()` + `Layout.UpdateCommand.Execute(null)`).

*Source: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`.*
