# 编译产物模型

`CompiledGraph` 是段的序集合；段可嵌套。图还在绑定表中拥有每个节点的编译身份，因此运行期从不要求节点自己携带编译器状态。

命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`。

## CompiledGraph

**签名：** `sealed partial class CompiledGraph`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Entries` | `ObservableCollection<CompileSegment>` | 有序顶层段。 |
| `TryGetCompileInfo(INodeComponent node, out NodeCompileInfo? info)` | `bool` | 从本图读取节点的编译身份。 |

`TryGetCompileInfo` 对未编译进图的节点、被剪掉的节点，以及从文档还原的图（绑定是运行期数据、不序列化）返回 `false`。绑定字典本身是 internal；该方法是公开读取入口。

## CompileSegment

**签名：** `abstract partial class CompileSegment`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Id` | `Guid` | 供 UI 树使用的段标识。 |
| `Depth` | `int` | 用于缩进的嵌套深度。 |

## ChainSegment

**签名：** `sealed partial class ChainSegment : CompileSegment`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Nodes` | `ObservableCollection<INodeComponent>` | 按驱动顺序排列的线性段。 |

## BranchSegment

**签名：** `sealed partial class BranchSegment : CompileSegment`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Router` | `INodeComponent?` | 路由器节点。 |
| `Options` | `ObservableCollection<BranchOption>` | 每个路由键一个选项。 |
| `IsDynamic` | `bool` | 键在运行期解析时为 `true`。 |
| `CompileKey` | `object?` | 编译期锁定的静态键；动态分支为 null。 |
| `CompileKeyTypeName` | `string?` | 键为枚举时的程序集限定类型名；否则为 null。 |

`CompileKeyTypeName` 的存在是因为 `object` 成员中的枚举往返后会变成底层数字。`BranchSegment` 与 `BranchOption` 在加载时还原枚举，使运行期重新解析为真实枚举的动态键仍能匹配选项。

## ParallelSegment

**签名：** `sealed partial class ParallelSegment : CompileSegment`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Branches` | `ObservableCollection<CompiledGraph>` | 每个扇出分支一个子图。 |

分支以交错的异步操作并发执行（见[运行时引擎](../../05_工作流运行时/00_运行时引擎/index.md)），但段形状与顺序无关。

## BranchOption

**签名：** `sealed partial class BranchOption`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Key` | `object?` | 路由键。 |
| `Label` | `string?` | 显示标签；默认为键的文本。 |
| `Graph` | `CompiledGraph?` | 下游子图；终止选项为 null。 |
| `IsTerminal` | `bool` | 选择该选项会结束整轮运行。 |
| `KeyTypeName` | `string?` | 键为枚举时的类型名；用于加载时还原。 |

## NodeCompileInfo

**签名：** `sealed class NodeCompileInfo` —— 构造函数是 internal，实例由编译器创建。

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `Order` | `int` | 全局驱动顺序；`-1` 为绝对停止态。 |
| `ChainIndex` | `int` | 线性段内索引。 |
| `Offset` | `int` | 节点所属子图的入口偏移。 |
| `InputNodes` | `IReadOnlyList<INodeComponent>?` | 汇合点聚合的上游源；链式与单输入节点为 null。 |

## CompiledOutline 与 CompiledOutlineRow

**签名：** `static class CompiledOutline` 与 `readonly record struct CompiledOutlineRow(int Depth, string Kind, string Label, IReadOnlyList<INodeComponent> Nodes)`

| 成员 | 类型 | 说明 |
| --- | --- | --- |
| `CompiledOutline.Of(CompiledGraph graph)` | `IReadOnlyList<CompiledOutlineRow>` | 深度优先、最外层优先展平；null 图返回空。 |
| `CompiledOutlineRow.Depth` | `int` | 嵌套深度，图自身入口为 `0`。 |
| `CompiledOutlineRow.Kind` | `string` | `Execute`、`Branch`、`Parallel`、`Option` 或 `Terminal`。 |
| `CompiledOutlineRow.Label` | `string` | 以 `→` 连接的节点类型，或路由器与选项数。 |
| `CompiledOutlineRow.Nodes` | `IReadOnlyList<INodeComponent>` | 该行命名的节点；选项行与并行行为空。 |

`CompiledOutline` 是同一结构的扁平、可虚拟化视图；图本身已是可绑定的嵌套视图模型，因此扁平大纲是可选项。

## 示例

```csharp
var graph = (await new CompilerViewModel().CompileAsync(source, CompileRole.Root))[0];

foreach (var row in CompiledOutline.Of(graph))
    Console.WriteLine($"{new string(' ', row.Depth * 2)}{row.Kind}: {row.Label}");

if (graph.TryGetCompileInfo(source, out var info))
    Console.WriteLine(info!.Order);     // 0

var branch = graph.Entries.OfType<BranchSegment>().FirstOrDefault();
Console.WriteLine(branch?.Options.Count);
```
