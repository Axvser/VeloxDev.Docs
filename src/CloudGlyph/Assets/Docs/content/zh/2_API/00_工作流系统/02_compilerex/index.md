# Workflow System — 命名空间：`VeloxDev.Core.WorkflowSystem.CompilerEx`

编译与运行时引擎：**编译期**把从发起节点可达（或目标节点的祖先锥）的纯无环子图分解成一张编译图（`CompiledGraph`，多图语义），并在编译完成后给每个节点注入编译身份（`ICompileContext`）；**运行期**由 `RuntimeEngine` 沿编译图逐段驱动节点——引擎拥有下游派发，节点自身不广播。

> 两种执行路径（编译驱动 / 非编译广播）共享同一入口 `ReceiveAsync` 的数据流差异见 [执行机制](../05_执行机制/index.md)。运行时节点通过收到的 context 类型区分路径。

---

## 1. 编译入口、角色与产物模型

### `CompileRole`

枚举，声明传给 `CompilerViewModel.CompileAsync` 的节点扮演的角色。

| 成员 | 说明 |
|---|---|
| `Root` | 把节点视为**起点**：沿其输出边（`Targets`）向下游分解可达子图（控制器 / 入口） |
| `Terminal` | 把节点视为**结果终端**：沿 `Sources` 反向收集其祖先锥，自动推导锥的入口边界，只编译“算出该节点结果”所需的最小前驱子图（无需显式起点） |

*源码：`WorkflowSystem/CompilerEx/Compile/CompileRole.cs`。*

### `CompilerViewModel`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Graphs` | `ObservableCollection<CompiledGraph> Graphs { get; }` | 编译产物集合；`CompileAsync` 每次先清空再写入一张图（controller 暴露它以便 UI 启用“运行”） |
| `CompileAsync` | `Task<IReadOnlyList<CompiledGraph>> CompileAsync<T>(T component, CompileRole role, CancellationToken ct = default)` | `T : IWorkflowViewModel`；单一编译入口，返回 `IReadOnlyList<CompiledGraph>`（当前实现恒含一张图）并写入 `Graphs` |

`CompileAsync` 分解规则（对 `Root` 与 `Terminal` 锥内相同）：

- 线性段（单输入 / 单输出连续节点）→ `ChainSegment`；
- 实现 `ICompileTimeRouter` 的节点 → `BranchSegment`（静态模式按当前键剪枝，动态模式保留全部分支）；
- 一条路由键指向多个下游 / 普通节点的多目标扇出 → `ParallelSegment`（扇出 / 汇合）；无下游 → `IsTerminal` 终端分支；
- 所有分支出口共同指向的节点是汇合点，作为父图下一段链的起点（全局 `Order` 带偏移，不归零）；
- 编译后给每个 `ICompileTimeAware` 节点注入 `CompileContext`；
- 链续接时每条输出边都经 `AccessAsync`（编译期 `ICompileContext`，`IsCompilePhase = true`、`Data = null`）静态检测，被拒边按“未连接”剪除。

**异常：** 若 `component` 不是 `IWorkflowNodeViewModel` → `ArgumentException`；`role` 越界 → `ArgumentOutOfRangeException`；`Terminal` 反向锥不可表达（独立前驱不汇聚到唯一汇合点，或多条路由分支同时抵达目标）→ `InvalidOperationException`。

*源码：`WorkflowSystem/CompilerEx/Compile/CompilerViewModel.cs`、`CompilerViewModel.Reverse.cs`。*

### 编译产物模型（`Compile/Model/*`）

#### `CompiledGraph`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Entries` | `ObservableCollection<CompileSegment> Entries { get; }` | 一段有序的编译段集合；图可嵌套（`BranchSegment` / `ParallelSegment` 各持有子 `CompiledGraph`）。编译产物只描述可能执行路径的集合，实际路径由运行期决定 |

#### `CompileSegment`（抽象）

编译段基类，携带 UI/结构共享状态。具体段：`ChainSegment`、`BranchSegment`、`ParallelSegment`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Id` | `Guid` | 段 UID（UI 树节点标识） |
| `Depth` | `int` | 嵌套深度（UI 缩进） |

#### `ChainSegment : CompileSegment`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Nodes` | `ObservableCollection<IWorkflowNodeViewModel>` | 一段线性节点序列（拓扑序） |

#### `BranchSegment : CompileSegment`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Router` | `IWorkflowNodeViewModel?` | 路由节点本身 |
| `Options` | `ObservableCollection<BranchOption>` | 各分支选项 |
| `IsDynamic` | `bool` | true = 运行期经 `ResolveRouteKey` 重解析键；false = 编译期已锁定键 |
| `CompileKey` | `object?` | 编译期锁定的路由键（静态模式；动态模式为 null） |

#### `BranchOption`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Key` | `object?` | 分支键 |
| `Label` | `string?` | 显示标签 |
| `Graph` | `CompiledGraph?` | 下游子图（null = 终端分支） |
| `IsTerminal` | `bool` | 注册了键但无下游——运行期选中即结束整轮运行 |

#### `ParallelSegment : CompileSegment`

| 成员 | 签名 | 说明 |
|---|---|---|
| `Branches` | `ObservableCollection<CompiledGraph>` | 扇出子图。各分支**顺序执行**——顺序承载“等待所有上游”的汇合语义（共享 `IRuntimeContext` 黑板非线程安全，故无真正并行） |

*源码：`WorkflowSystem/CompilerEx/Compile/Model/CompiledGraph.cs`、`CompileSegment.cs`、`ChainSegment.cs`、`BranchSegment.cs`、`ParallelSegment.cs`、`BranchOption.cs`。*

---

## 2. 编译期契约（路由 / 注入 / 身份）

### `ICompileTimeRouter`

节点声明的“上游数据 → 广播目标”路由契约：

| 成员 | 签名 | 说明 |
|---|---|---|
| `GetRouteTable` | `Task<IReadOnlyDictionary<object, IReadOnlyList<IWorkflowNodeViewModel>>> GetRouteTable()` | 编译期分支表：键 → 下游节点列表；一个分支可扇出到多目标。编译器据其生成 `BranchSegment` |
| `ResolveRouteKey` | `Task<object?> ResolveRouteKey(object? payload)` | 给定当前数据负载（**运行期为 `IRuntimeContext` 实例，编译期为 null**）返回路由键。编译期不可判 → 返回 null → 该分支动态保留 |

### `RouterCompileMode`

路由节点的编译模式，决定 `GetRouteTable` 编译期返回的分支字典：

| 成员 | 说明 |
|---|---|
| `Static` | 编译期只返回当前选中分支；编译产物 = 单一路径，`CompileKey` 锁定，未选中分支的下游节点被注入 `Order = -1`（绝对停止） |
| `Dynamic` | 编译期返回全部分支；编译产物保留分支结构，运行期经 `ResolveRouteKey` 决定走哪支 |

### `ICompileTimeAware`

编译期注入接口：编译完成后接收自己的编译身份。

| 成员 | 签名 | 说明 |
|---|---|---|
| `AttachCompileTimeContext` | `void AttachCompileTimeContext(ICompileContext context)` | 编译完成时由编译器调用 |
| `CompileContext` | `ICompileContext? CompileContext { get; }` | 注入的身份（`Order = -1` 表示绝对停止）；运行期据其跳转执行状态码 |

### `ICompileContext : IAccessContext`

编译身份上下文接口。由 `CompileContext` 实现，经 `ICompileTimeAware` 注入节点。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Order` | `int` | 全局编译期固定执行序号；**-1 = 绝对停止**（未选中分支 / 终止态） |
| `ChainIndex` | `int` | 在所属线性段内的索引（从 0 起） |
| `Offset` | `int` | 本子图的入口偏移（路由下游 > 0，全局序号不归零） |
| `InputNodes` | `IReadOnlyList<IWorkflowNodeViewModel>?` | 汇合点输入源节点（编译期从各分支出口登记）。`Count > 1` 时运行期把各上游产物聚合成 `GroupData` 注入 `Data`；链式 / 单输入节点为 null，保留裸 Data 链语义 |

`CompileContext`（默认实现）：`IsCompilePhase => true`、`Data => null`；`Sender` / `Receiver` 在**边实例**上由编译器按被校验边填入，节点自持的身份实例上为 null；`InputNodes`、`Order`、`ChainIndex`、`Offset` 均可读写。

*源码：`WorkflowSystem/CompilerEx/Compile/Contracts/{ICompileTimeRouter,RouterCompileMode,ICompileTimeAware,ICompileContext}.cs`、`Compile/Model/CompileContext.cs`。*

---

## 3. 运行期：引擎、会话上下文、汇合数据与重定向

### `RuntimeEngine`

编译图运行时引擎：沿 `CompiledGraph` 驱动节点执行，不依赖节点自行广播——“引擎取数据并驱动下一个节点”。

| 成员 | 签名 | 说明 |
|---|---|---|
| `RunAsync` | `Task RunAsync(CompiledGraph graph, IRuntimeContext context, CancellationToken ct)` | 驱动一张图的所有条目；`graph` 或 `context` 为 null 直接返回 |

引擎语义（对照 `RuntimeEngine.cs`）：

- `ChainSegment`：逐个驱动节点——重定向重跑时跳过 `Order < 目标` 的节点（可跨链）。
- `BranchSegment`：先驱动路由节点本身（除非是“仅重新路由”），再选键（静态用锁定 `CompileKey`，动态经 `ResolveRouteKey(context)` 重解析）→ 驱动选中子图；选中 `IsTerminal` 分支即整轮正常结束。
- `ParallelSegment`：每分支前恢复 `Data = 源负载`（避免前一分支输出泄漏进下一分支），再顺序驱动各分支子图；分支内命中终端分支则整轮结束。
- 每次驱动前注入：命中 `IRuntimeContext.Target` 置 `TargetReached = true`；给 `IRuntimeAware` 节点调用 `AttachRuntimeContext`；写入 `CurrentOrder`（= 编译固定序号）；`RegisterOutput` 登记产物并按 `InputNodes.Count > 1` 时以 `GroupData` 覆盖 `Data` 注入汇合点。
- 节点在 `ReceiveAsync` 中调用 `Error()/Warn()` 或抛异常 = 请求重定向：若节点实现 `IRedirectable`，引擎以其返回值（必须是前驱序号）**重跑整张图**（目标为 Router 时只重新路由、不重新计算）；否则流程结束、`Status = "Stopped"`、`EndedWithError = true`、`CurrentOrder = -1`。
- 每次 `RunAsync` 开头 `ResetOutputs()` 一次并清 `TargetReached`；重定向超过 50 次（`MaxRedirects`）抛 `InvalidOperationException`。

*源码：`WorkflowSystem/CompilerEx/Runtime/RuntimeEngine.cs`。*

### `IRuntimeContext : ITaskContext`

编译器运行时会话上下文（继承 `ITaskContext`，即同时是 `IAccessContext`/`IContext`）：`UID` / 日志 / 共享变量（黑板）/ 执行位置。编译驱动时引擎**把会话对象直接作为任务上下文**传入 `ReceiveAsync`。

| 成员 | 签名 | 说明 |
|---|---|---|
| `Uid` / `Sequence` | `Guid` / `int` | 会话唯一标识 / 下一条执行序号 |
| `Logs` | `ObservableCollection<string>` | 带序号前缀的日志 |
| `CurrentEntry` | `CompileSegment?` | 正在执行的编译段 |
| `NodeIndex` / `BranchKey` / `Attempt` | `int` / `object?` / `int` | 链内当前节点下标 / 当前分支键 / 尝试次数（每重定向 +1） |
| `IsRunning` / `Status` | `bool` / `string` | 运行中标记 / 状态串（Idle/Running/Completed/Stopped） |
| `CurrentOrder` | `int` | 当前执行状态码 = 编译期固定序号 |
| `Target` | `IWorkflowNodeViewModel?` | 可选目标节点（结果 / 终端运行设置）；引擎驱动到匹配节点时置 `TargetReached` |
| `TargetReached` | `bool` | 本轮是否真正驱动到 `Target`（false = 分支未走 / 条件未满足，不虚构结果） |
| `Data` | `new object? { get; set; }` | 链式结果（**遮蔽** `IContext.Data` 增加 setter）：每驱动完一个节点引擎把 `ReceiveAsync` 返回值写回，供下游读取 |
| `RedirectRequested` | `bool` | 本次驱动是否请求了重定向（`Error`/`Warn` 置位，引擎驱动前清） |
| `EndedWithError` | `bool` | 因“节点报错但不实现 `IRedirectable`”提前结束（状态 -1） |
| `PendingRedirectTarget` | `int?` | 引擎请求的重定向目标 `Order`（可跨链） |
| `ActiveRedirectTarget` | `int?` | 每 pass 开头引擎写入的“当前重跑目标 Order”（首 pass 为 null）；产物收集据其区分契约保留前缀与陈旧分支 |
| `Log` | `void Log(string entry)` | 普通日志行 |
| `Error` / `Warn` | `void Error(string message)` / `void Warn(string message)` | 错误 / 警告日志行，并标记“请求重定向” |
| `Set` / `TryGet` | `void Set(string key, object? value)` / `bool TryGet(string key, out object? value)` | 共享变量（黑板）写 / 读 |
| `RegisterOutput` | `void RegisterOutput(IWorkflowNodeViewModel node, object? value)` | 登记节点本次产物（带当前 pass 戳），供多输入汇合点聚合 |
| `ResetOutputs` | `void ResetOutputs()` | 清空产物登记表（每次 `RunAsync` 开头一次；重定向重跑不清，靠 pass 戳过滤陈旧产物） |
| `CollectGroupedInputs` | `IReadOnlyDictionary<IWorkflowNodeViewModel, object?> CollectGroupedInputs(IEnumerable<IWorkflowNodeViewModel> inputNodes)` | 把一组输入源的产物收集为只读字典：仅本 pass 产物 + 重定向目标前契约保留前缀；未登记的来源缺席（`TryGetValue` → false） |

### `RuntimeContext : IRuntimeContext`

`IRuntimeContext` 的默认实现（公开 VM，携带 UID；`[VeloxProperty]` 成员 + 共享变量字典 + 产物登记表；`IsCompilePhase => false`）。`Next()` 以 `Interlocked` 自增序号；`Error()`/`Warn()` 在写日志的同时置 `RedirectRequested`。

*源码：`WorkflowSystem/CompilerEx/Runtime/Contracts/IRuntimeContext.cs`、`Runtime/Model/RuntimeContext.cs`。*

### `IGroupData` / `GroupData`

多输入汇合数据契约（非泛型）。运行期驱动汇合点前，引擎把多路上游产物包装成只读字典注入 `context.Data`；节点在 `ReceiveAsync` 里以 `context.Data is IGroupData g` 读取，经 `TryGetValue` / 索引器 / `Keys` 消费（Key = 来源 `IWorkflowNodeViewModel` 引用身份，Value = 该节点本次产物）。未运行来源缺席，`TryGetValue` → false。

```csharp
public interface IGroupData : IReadOnlyDictionary<IWorkflowNodeViewModel, object?>
{
}

public readonly struct GroupData : IGroupData
{
    // 包装只读字典；实现 IReadOnlyDictionary 全部成员，索引器对未登记来源抛 KeyNotFoundException
}
```

*源码：`WorkflowSystem/CompilerEx/Runtime/Model/GroupData.cs`。*

### `IRedirectable` / `IRuntimeAware`

| 接口 | 成员 | 说明 |
|---|---|---|
| `IRedirectable` | `Task<int?> ResolveRedirectAsync(IRuntimeContext context, CancellationToken ct)` | 可重定向节点：链内决定是否回退到更早编译态。引擎在驱动节点后调用；返回非 null 的 `CompileContext.Order` = 回退到该态并重执行（v1 链内重定向）；null = 继续。编译图本身无环，重定向纯属运行期契约 |
| `IRuntimeAware` | `void AttachRuntimeContext(IRuntimeContext context)` | 运行期注入：编译执行引擎在驱动前把当前会话交给节点，使其能记序号 / 写日志 / 读写共享变量 |

*源码：`WorkflowSystem/CompilerEx/Runtime/Contracts/{IRedirectable,IRuntimeAware}.cs`。*

---

### 运行示例（真实）

从控制器节点编译并驱动整条链——`Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs` 的 `Compile` / `Run` 命令：

```csharp
[VeloxCommand]
private async Task Compile(object? parameters, CancellationToken ct)
{
    await Compiler.CompileAsync(this, CompileRole.Root);   // 填 Compiler.Graphs
    OnPropertyChanged(nameof(HasCompiledGraphs));
}

[VeloxCommand]
private async Task Run(object? parameters, CancellationToken ct)
{
    var graph = Compiler.Graphs.FirstOrDefault();
    if (graph is null) return;

    var context = new RuntimeContext { IsRunning = true };   // UI 可绑定会话进度
    RuntimeContext = context;
    OnPropertyChanged(nameof(RuntimeContext));

    _runCts = CancellationTokenSource.CreateLinkedTokenSource(ct);
    try
    {
        await new RuntimeEngine().RunAsync(graph, context, _runCts.Token);
    }
    finally
    {
        _runCts.Dispose();
        _runCts = null;
    }
}
```

*源码：`Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`（`Compile`/`Run`/`Stop` 命令，第 30-68 行）。*
