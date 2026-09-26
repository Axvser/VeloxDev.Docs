# Workflow System — Namespace: `VeloxDev.MVVM.Serialization`

`ComponentModelEx`: **the modern TFMs (net8.0 / net10.0) are System.Text.Json based**, while the `netstandard2.0` asset still uses Newtonsoft; both write the same archive shape. Base settings: the type discriminator is the **assembly-qualified name** (byte-identical to existing archives, whitelisted from the compile-time component catalog), references preserved, writable properties only, interface-keyed dictionaries stored by reference id, and `NaN` written as the named literal.

> One known difference on the writing side: a collection is written as `{"$id","$values":[]}` where older archives hold a plain array. Readers accept both.

| Method | Signature |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)` where `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)` (+ options overload) |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)` (+ options overload) |
| Async | `SerializeAsync`, `DeserializeAsync` |
| Streaming | `SerializeToUtf8Bytes`, `DeserializeFromUtf8Bytes`, `SerializeToTextWriterAsync`, `DeserializeFromTextReaderAsync`, `SerializeToStreamAsync`, `DeserializeFromStreamAsync` |
| Options | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)`. The three enums belong to this library now (same names as Newtonsoft's, fewer values), so `using Newtonsoft.Json` is no longer needed. |

**Example** — save/load in the demo tree: `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`, `Save` command, line 252 (`var json = this.Serialize();`), and `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`, lines 65-67 (`json.Deserialize<TreeViewModel>()` + `Layout.UpdateCommand.Execute(null)`).

*Source: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`.*
