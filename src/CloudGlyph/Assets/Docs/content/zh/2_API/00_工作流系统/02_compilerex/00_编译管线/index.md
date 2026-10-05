# 工作流系统 — 编译管线

`VeloxDev.Core.WorkflowSystem.CompilerEx` 的编译半边：入口点、它产出的不可变产物，以及节点为参与编译而实现的契约。

源码：`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/` —— `CompilerViewModel.cs`、`CompilerViewModel.Reverse.cs`、`CompileRole.cs`、`Contracts/`、`Model/`。

---

## 编译入口

### `CompilerViewModel`

`public sealed partial class`。挂在某个节点（通常是控制器）上，好让 UI 绑定编译结果 —— `Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` 声明了 `public CompilerViewModel Compiler { get; } = new();`。

##### 属性

| 名称 | 类型 | 说明 |
|---|---|---|
| `Graphs` | `ObservableCollection<CompiledGraph>` | 最近一次编译产物（`[VeloxProperty]`），供 UI 绑定。每次 `CompileAsync` 开头清空。 |

##### 方法

#### `CompilerViewModel.CompileAsync<T>`

**签名：**

```csharp
Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(
    T component, CompileRole role, CancellationToken ct = default) where T : IWorkflowViewModel;
```

| 参数 | 类型 | 说明 |
|---|---|---|
| `component` | `T : IWorkflowViewModel` | 从哪个节点编译。必须是 `IWorkflowNodeViewModel` —— `Root` 下它是起点，`Terminal` 下它是结果节点。 |
| `role` | `CompileRole` | `Root`（正向）或 `Terminal`（反向祖先锥）。 |
| `ct` | `CancellationToken` | 可选取消。默认 `default`。 |

**返回：** `IReadOnlyList<CompiledGraph>` —— 本次请求一张编译图。它同时会写进 `Graphs`。

**异常：**

| 异常 | 条件 |
|---|---|
| `ArgumentException` | `component` 不是 `IWorkflowNodeViewModel`。 |
| `ArgumentOutOfRangeException` | `role` 不是已定义的 `CompileRole`。 |
| `InvalidOperationException` | `CompileRole.Terminal` 的锥无法表达：多个独立生产者没有汇入同一个公共汇合点，或某路由有超过一条分支抵达终点。 |

**示例：**

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

// Demo：Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs（Compile 命令）
await Compiler.CompileAsync(this, CompileRole.Root);
```

**说明：** `Terminal` 在 `CompilerViewModel.Reverse.cs` 里实现：沿槽位 `Sources` 做反向 BFS（每条边由发送方的 `AccessAsync` 以 `ICompileContext` 校验），随后自动推导锥的入口前沿，只编译锥内部分。锥上的路由保留真实的 `BranchSegment` 语义，只编译在锥内的那条分支（`RestrictRouteToCone`）。

---

## 编译产物

### `CompileRole`

**签名：** `public enum CompileRole { Root, Terminal }`

| 成员 | 值 | 含义 |
|---|---|---|
| `Root` | 0 | 该节点是起点：沿 `Targets` 正向分解从它可达的子图。 |
| `Terminal` | 1 | 该节点是结果终点：编译它的祖先锥，只算到该节点为止。 |

### `CompiledGraph`

`public sealed partial class`。被视作一张图的、有序的编译分段集合。可嵌套 —— `BranchSegment` / `ParallelSegment` 各自持有子 `CompiledGraph`。产出后即不可变：它**描述**可能的执行，实际走哪条路由运行期状态决定。

| 名称 | 类型 | 说明 |
|---|---|---|
| `Entries` | `ObservableCollection<CompileSegment>` | 顶层分段，按驱动顺序排列。 |

### `CompileSegment`

`public abstract partial class`。三种具体分段的公共基类。

| 名称 | 类型 | 说明 |
|---|---|---|
| `Id` | `Guid` | 分段 UID（UI 树节点标识），默认 `Guid.NewGuid()`。 |
| `Depth` | `int` | 嵌套深度，供 UI 缩进，默认 `0`。 |

| 分段 | 成员 | 为谁产出 |
|---|---|---|
| `ChainSegment`（`sealed partial`） | `ObservableCollection<IWorkflowNodeViewModel> Nodes` | 单入单出的线性节点串。 |
| `BranchSegment`（`sealed partial`） | `IWorkflowNodeViewModel? Router`、`ObservableCollection<BranchOption> Options`、`bool IsDynamic`、`object? CompileKey`、`string? CompileKeyTypeName` | 实现了 `ICompileTimeRouter` 的节点。 |
| `ParallelSegment`（`sealed partial`） | `ObservableCollection<CompiledGraph> Branches` | 扇出组：一个路由键喂给多个目标，或多个生产者汇入同一节点。 |

### `BranchOption`

`public sealed partial class`。`BranchSegment` 的一条分支。

| 名称 | 类型 | 说明 |
|---|---|---|
| `Key` | `object?` | 本选项应答的路由键。 |
| `Label` | `string?` | 显示标签（键的字符串形式；键为 null 时为 `"?"`）。 |
| `Graph` | `CompiledGraph?` | 本选项的下游子图；终结选项为 `null`。 |
| `IsTerminal` | `bool` | 没有下游节点：运行期选中它即整轮结束（汇合尾部不再传播）。 |
| `KeyTypeName` | `string?` | 键的程序集限定类型名，**仅当键是枚举时**由编译器记录 —— 见下方 `CompileKeyNormalizer`。 |

### `CompileKeyNormalizer` *（internal）*

`internal static class`。不属于公开面；写在这里是因为它解释了一个否则会被当成 bug 的序列化行为。

分支键以 `object` 保存，因为 `ICompileTimeRouter` 可以用任何东西做键，而一个数字从 JSON 回来会变成 `long`：`object` 成员里的枚举会还原成它的底层数字，因为枚举是按裸整数写出去的、不带类型标签（由 `ComponentModelExTests.AnEnumInAnObjectMember_ComesBackAsItsNumber` 钉住）。**静态**分支靠运气躲过这一劫（两边都退化成 `long`，比较仍然相等），但**动态**分支会在运行期重新解析出真枚举，于是匹配不到任何选项 —— 运行会像那条分支没有下游一样结束。

所以编译器在键旁边记下它的类型（`CompileKeyNormalizer.TypeNameOf`），`BranchSegment` / `BranchOption` 在加载时通过一个 `[OnDeserialized]` 回调调用 `CompileKeyNormalizer.Normalize` 还原它 —— 用回调而不是属性 setter，因为加载时 setter 会在文档中位置更靠后的类型名成员尚未读到之前就触发。匹配不到任何成员的数字会变成*未定义*的枚举值而不是报错，这正是实跑遇到「没有选项认领的键」时的行为。

---

## 编译期契约

| 类型 | 签名 / 成员 |
|---|---|
| `ICompileContext : IAccessContext` | `int Order { get; set; }` —— 编译期固定执行序号，`-1` = 绝对停止；`int ChainIndex { get; set; }` —— 线性分段内的序号；`int Offset { get; set; }` —— 子图入口偏移；`IReadOnlyList<IWorkflowNodeViewModel>? InputNodes { get; set; }` —— 汇合点的输入来源。 |
| `CompileContext : ICompileContext` | `public sealed partial class`。`IsCompilePhase => true`、`Data => null`。`Sender` / `Receiver` 在节点自己持有的那份身份实例上为 `null`，只由编译器为 `AccessAsync` 校验构造的逐边实例填充。`Order` / `ChainIndex` / `Offset` 是 `[VeloxProperty]`，默认值 `-1` / `-1` / `0`。 |
| `ICompileTimeAware` | `void AttachCompileTimeContext(ICompileContext context)`；`ICompileContext? CompileContext { get; }` —— 编译结束时注入编译身份。 |
| `ICompileTimeRouter` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()` —— 分支表（一个键可扇出到多个目标）；`Task<object?> ResolveRouteKey(object? payload)` —— 当前载荷对应的路由键（运行期是 `IRuntimeContext`，编译期是 `null`）。 |
| `RouterCompileMode` | `public enum RouterCompileMode { Static, Dynamic }`。`Static`：`GetRouteTable()` 只返回当前选中的分支，顺序在编译期固定。`Dynamic`：所有分支都存活，运行期重新解析键。 |

`BranchSegment` 上的 `CompileKey` 就是编译期 `ResolveRouteKey(null)` 的返回值：非 null 即 **Static**（`IsDynamic == false`），运行期用锁定的键；`null` 即 **Dynamic**（`IsDynamic == true`），运行期调用 `ResolveRouteKey(context)`。静态剪枝下，每个「可达但未被选中」的节点都被盖上 `Order = -1`，绝不进入任何分段。

实现该契约的 demo 路由见 `策略模式`。

---

## 扁平大纲

### `CompiledOutline` / `CompiledOutlineRow`

```csharp
public readonly record struct CompiledOutlineRow(
    int Depth, string Kind, string Label, IReadOnlyList<IWorkflowNodeViewModel> Nodes);

public static class CompiledOutline
{
    public static IReadOnlyList<CompiledOutlineRow> Of(CompiledGraph graph);
}
```

编译图本身就是 ViewModel —— 分段放在可观察集合里 —— 所以嵌套列表可以直接绑它。`CompiledOutline.Of` 是为另一种形态准备的：一个扁平、可虚拟化的列表，一次把整棵结构摆出来；代价是算一次（编译后的图是冻的，所以没有任何东西需要跟着它同步）。

| 行字段 | 含义 |
|---|---|
| `Depth` | 嵌套深度；图自身的条目为 `0` —— 列表视图按它缩进。 |
| `Kind` | `"Execute"`（`ChainSegment`）、`"Branch"`（`BranchSegment`）、`"Parallel"`（`ParallelSegment`），外加分支选项的 `"Option"` / `"Terminal"`。 |
| `Label` | 紧凑描述：链的节点以 `→` 相连，或路由器及其键。 |
| `Nodes` | 本行点名的节点，按顺序。不点名任何节点时为空。 |

**示例（Demo / 已实测）：** 对一条编译后的 `Ticker → Bias → Printer` 链，`CompiledOutline.Of` 恰好产出一行：

```text
Execute | TickerNode → BiasNode → PrinterNode
```

**说明：** 这套词汇（`Execute` / `Branch` / `Parallel`）与 Agent 对编译图的投影用的是同一套，两处不会漂移成两套术语。demo 把 `CompiledOutline.Of` 绑到树上（`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`），Avalonia 宿主按 `Depth` 缩进（`Examples/Workflow/Avalonia/Demo/Views/Workflow/DepthIndentConverter.cs`）。
