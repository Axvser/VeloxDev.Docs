# 工作流系统 — 命名空间：`VeloxDev.MVVM.Serialization`

三个序列化器加一个流式选项构建器，全在 `VeloxDev.Core.Extension` 里。Core 自身没有序列化器，所以编译图与检查点的文档住在这里，而不是住进它们所写的类型旁边。

源码：`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`、`CompiledGraphEx.cs`、`CheckpointEx.cs`。

---

## `ComponentModelEx` —— 整树 JSON

基于 Newtonsoft。基础设置：`TypeNameHandling.Auto`、`PreserveReferencesHandling.Objects`、`ReferenceLoopHandling.Ignore`、`NullValueHandling.Include`、`DefaultValueHandling.Include`、`WritablePropertiesOnlyResolver`、`DictionaryKeyConverter`。

| 方法 | 签名 |
|---|---|
| `Serialize` | `Serialize<T>(this T workflow)` / `Serialize<T>(this T workflow, SerializationOptions)`，其中 `T : INotifyPropertyChanged` |
| `Deserialize` | `Deserialize<T>(this string json)`（另有 options 重载） |
| `TryDeserialize` | `TryDeserialize<T>(this string json, out T? workflow)`（另有 options 重载） |
| 异步 | `SerializeAsync`、`DeserializeAsync` |
| 流式 | `SerializeToUtf8Bytes`、`DeserializeFromUtf8Bytes`、`SerializeToTextWriterAsync`、`DeserializeFromTextReaderAsync`、`SerializeToStreamAsync`、`DeserializeFromStreamAsync` |
| 选项 | `SerializationOptions.Create().WithIndented()/WithCompact()/WithTypeNameHandling(...)/WithNullValueHandling(...)/WithDefaultValueHandling(...)/WithExcludedPropertyTypes(...)` |

**示例** —— demo 树的存取：`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` 的 `Save` 命令（`var json = this.Serialize();`），以及 `Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml.cs`（`json.Deserialize<TreeViewModel>()` + `Layout.UpdateCommand.Execute(null)`）。

---

## `SerializationOptions`

**签名：** `public sealed class SerializationOptions`

一个流式构建器，它**修改自身并返回 `this`**，所以下面这个排除项会作用在你传进去的那个实例上。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Create()` | `static SerializationOptions Create()` | 一个全新的构建器。 |
| `WithIndented()` | `SerializationOptions` | `Formatting.Indented`。 |
| `WithCompact()` | `SerializationOptions` | `Formatting.None`。 |
| `WithTypeNameHandling(TypeNameHandling)` | `SerializationOptions` | Newtonsoft 的 `TypeNameHandling`。 |
| `WithNullValueHandling(NullValueHandling)` | `SerializationOptions` | Newtonsoft 的 `NullValueHandling`。 |
| `WithDefaultValueHandling(DefaultValueHandling)` | `SerializationOptions` | Newtonsoft 的 `DefaultValueHandling`。 |
| `WithExcludedPropertyTypes(params Type[])` | `SerializationOptions` | 丢弃声明类型是这些之一的属性 —— `CompiledGraphEx` 用来阻止写入器顺着引用走出图。 |

---

## `CompiledGraphEx` —— 编译图自成一份文档

**签名：** `public static class CompiledGraphEx`

| 成员 | 签名 | 说明 |
|---|---|---|
| `SerializeCompiledGraph` | `string SerializeCompiledGraph(this CompiledGraph graph, bool includeTree = false, SerializationOptions? options = null)` | 返回文档。`graph` 为 `null` 时抛 `ArgumentNullException`。 |
| `DeserializeCompiledGraph` | `CompiledGraph? DeserializeCompiledGraph(this string json)` | 读入上面写出的文档。 |

编译图就是普通的 VeloxDev ViewModel —— 分段在可观察集合里持有节点，自身形状里没有槽位也没有连线 —— 所以它与树用的是同一套机制。它额外需要的只是一个关于**文档伸到多远**的决定，因为节点是活的画布实例，它的可写成员朝外指：`Parent` 抵达树，槽位的 `Targets`/`Sources` 抵达每个与之相连的节点。因此不做决定地序列化，代价是整棵树加上整个连通分量。

| 模式 | `includeTree` | 保留 | 代价 |
|---|---|---|---|
| **快照**（默认） | `false` | 分段结构加上每个节点自身的状态 —— 深拷贝、归档或列表视图想要的东西。丢弃 `IWorkflowTreeViewModel` 与 `ObservableCollection<IWorkflowSlotViewModel>` 属性。 | 不可重新上墙：还原的节点没有 `Parent`，所以没有东西为缩放重新坍缩它们的几何，也没有东西在它们移动时把树标脏。 |
| **带上树** | `true` | 全部，于是还原的图可以放回画布。 | 代价是整棵树加上整个连通分量的大小 —— 而且节点的 `Parent` 是**第二棵**、新构造的树：节点回来时接的是那个副本，不是你手上这棵。 |

与模式无关，还原的节点都拿到**全新的 `RuntimeId`**（它不是可写成员）并且**不携带编译身份**（`ICompileTimeAware.CompileContext` 也不可写）。分支键是会被修补的那个例外：枚举键经任何往返都会变回数字，所以编译器把类型记在旁边，加载时还原 —— 见 `CompileKeyNormalizer`。

**说明：** 读入时**刻意不**施加排除：这个过滤器是为了阻止*写入器*顺着引用走出图，而读取器不会跟随任何东西 —— 文档里没有的成员就保持构造函数留给它的样子。

---

## `CheckpointEx` —— 运行位置作为 JSON

**签名：** `public static class CheckpointEx`

| 成员 | 签名 | 说明 |
|---|---|---|
| `SerializeCheckpoint` | `string SerializeCheckpoint(this ExecutionCheckpoint checkpoint)` | JSON 文本，**缩进** —— 它是人可能最终会打开的文件。`checkpoint` 为 `null` 时抛 `ArgumentNullException`。 |
| `DeserializeCheckpoint` | `ExecutionCheckpoint? DeserializeCheckpoint(this string json)` | 检查点；文本为空或不是检查点时为 `null`（解析失败被吞掉）。 |

它走的是库其它部分在用的那套设置 —— `ComponentModelEx` 背后那套 —— 而不是自己私有一份，所以检查点与它所属的图写法一致，载荷也保持形状：字典回来还是字典，而不是 `JObject`。

**说明：**

- **数字不保留类型，而且这是实测而非假设。** 载荷是 `object`，而 JSON 只有一种整数类型：进去的 `int` 回来是 `long`，`float` 回来是 `double`。`TypeNameHandling.All` 也救不了 —— 无论怎么设，基元都写成裸 JSON 值。引擎自己的字段（`ExecutionCheckpoint.Attempt`、键、形状）是精确的；一个用 `int` 匹配载荷的节点在恢复之后匹配不上。`InMemoryCheckpointStore` 没有这个缺口。
- **检查点是普通文档，不是 ViewModel**，这就是它不走 `ComponentModelEx.Serialize` 的原因 —— 那个面被约束在 `INotifyPropertyChanged` 上。

---

## `FileCheckpointStore`

**签名：** `public sealed class FileCheckpointStore : IExecutionCheckpointStore`

一个由单个文件支撑的检查点存储，于是运行的位置能活过取得它的那个进程。

| 成员 | 签名 | 说明 |
|---|---|---|
| 构造函数 | `FileCheckpointStore(string path)` | `path` 为 `null` 或空白时抛 `ArgumentNullException`。 |
| `Path` | `string` | 本存储读写的那份文件。 |
| `SaveAsync` | `Task SaveAsync(ExecutionCheckpoint checkpoint, CancellationToken ct)` | 替换文件内容；首次保存时若目录不存在会创建它。 |
| `LoadAsync` | `Task<ExecutionCheckpoint?> LoadAsync(CancellationToken ct)` | 文件不存在或无法解析时为 `null`。 |

**说明：**

- **一个存储、一份文件、一轮运行。** 每次保存都替换文件内容。
- 引擎可能同时有两条扇出分支在保存（它们是交错而不是跑在独立线程上，但一个 `await` 就足以重叠），所以写入在 `SemaphoreSlim` 后面串行化 —— 否则两个写入器可以自由交错字节。序列化发生在门的**外面**，只让 IO 等待。
- 写入是同步的（`File.WriteAllText`）：本工程只有 `netstandard2.0` 一个目标，那里没有 `WriteAllTextAsync`。

**示例（Demo）：**

```csharp
// Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs
Checkpoints = new FileCheckpointStore(CheckpointPath);
primary.CheckpointSource = ct => Checkpoints.LoadAsync(ct);
// 再由控制器交给引擎：
await new RuntimeEngine().RunAsync(graph, context, _runCts.Token, place);
```

**测试证据：** `VeloxDev.Core.Extension.Test/Serialization/ExecutionCheckpointSerializationTests.cs` —— `FileCheckpointStore_KeepsThePlace_AcrossInstances`、`FileCheckpointStore_SaveReplacesWhatWasThere`。
