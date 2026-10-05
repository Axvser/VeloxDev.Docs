# 工作流系统 — 序列化

归档引擎是 `VeloxDev.Serialization`，它随 **`VeloxDev.Core`** 一起发布 —— 前几页已经引用的就是那个包，所以**不必再装任何东西**。只有两种文档住在 `VeloxDev.Core.Extension` 里：编译后的图，和一次运行的检查点（见 `终端编译`）。

序列化是**闭世界**的：只有当源生成器为某个类型编出了读写器，它才能往返。这里没有反射、也没有兜底，所以生成器没见过的类型会**明确报错**，而不是读回一个空壳。

## 1. 生成器接受什么

进入闭世界有四条路，任一条即可（`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:588-614`）：

| 进入方式 | 适用于 |
|---|---|
| 实现四个组件接口之一 | `IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel` |
| 带一个 `[WorkflowBuilder.*]` 特性 | 生成出来的组件模板 |
| 有一个 `[VeloxProperty]` **字段** | 你自己的 ViewModel —— `QuickTree` 走的就是这条 |
| 贴 `[Archivable]` | 不是 ViewModel 的普通文档类型 |

```csharp
// ViewModel：[VeloxProperty] 字段会把属性提升出来，所以类必须是 partial。
// 出处：Src/Core/VeloxDev.Core.Extension.Test/Serialization/ViewModelSerializerContractTests.cs:23-26
internal sealed partial class ContractModel
{
    [VeloxProperty] private int count;
}

// 普通文档类型：只贴 [Archivable] 就够，不需要 partial。
// 出处：Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Model/ExecutionCheckpoints.cs:27-28
[Archivable]
public sealed class ExecutionCheckpoint
```

成员的收录规则是「**public 且带 public setter 的属性，按声明顺序**」；`[VeloxProperty]` 字段排在其后，继承来的成员最后。这个顺序是**逐字节的契约**，不是风格选择。

## 2. 保存与重建

```csharp
using VeloxDev.Serialization;

// 存之前先把正在跑的工作收干净 —— Demo 的 Save 就是这一步。
await tree.GetHelper().CloseAsync();

var json = tree.Serialize();
var copy = json.Deserialize<QuickTree>();

Console.WriteLine($"copy Nodes={copy.Nodes.Count} Links={copy.Links.Count} " +
                  $"origin={copy.Layout.OriginSize.Width}x{copy.Layout.OriginSize.Height}");
```

**预期结果：** `copy.Nodes.Count == 3`、`copy.Links.Count == 2`、`copy.Layout.OriginSize` 为 `2400x850`。节点上一次编译拿到的 `CompileContext` **不会**进文档 —— 它的 setter 不是 public —— 会在下次编译时重新注入。

`Serialize<T>()` / `Deserialize<T>()` 是 `INotifyPropertyChanged` 视图模型上的扩展方法（`VeloxDev.Serialization.ViewModelSerializer`）。`TryDeserialize<T>(out var copy)` 是不抛异常的版本：文本为 null、空白或畸形时返回 `false`。

## 3. 往返验证：把副本跑起来

最有力的验证是重建出来的树能编译、且跑出与原树完全相同的结果：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var tickerCopy = copy.Nodes.OfType<TickerNode>().Single();
var copyGraphs = await new CompilerViewModel().CompileAsync(
    tickerCopy, CompileRole.Root, CancellationToken.None);
var copyCtx = new RuntimeContext();
await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);

Console.WriteLine(copyCtx.Status);   // Completed
Console.WriteLine(copyCtx.Data);     // tick->bias->print   （与原树同一条链）
```

**预期结果：** 重建的 `QuickTree` 跑出 `Ticker → Bias → Printer`，且 `copyCtx.Data == "tick->bias->print"`，与原树上的正向运行一致（见 `编译与运行`）。

## 4. 往返出错的四种形态

| 症状 | 原因 | 修法 |
|---|---|---|
| `MissingWriter` / `MissingReader` | 该类型从未进入闭世界 —— 没有任何标注指向它，也没有成员能走到它。 | 贴 `[Archivable]`，或从已有入口的类型走到它。 |
| 成员在文档里干脆不存在 | 它没有 public setter（`CompileContext` 就是这样被丢掉的）。 | `[Archive(ArchiveOptions.KeepProperty)]` 能写出去 —— 但**仍然读不回来**。 |
| 枚举读回来成了数字 | 枚举默认按底层整数写。 | 在**那一个成员**上贴 `[Archive(ArchiveOptions.EnumName)]`，改写成员名。 |
| 读取时抛 `InvalidOperationException` | 文档缺了一个 `required` 成员。 | 把该成员写进去，或去掉 `required`。 |

归档格式与 `System.Text.Json`、Newtonsoft **不互通**：类型判别符、集合形状、成员集来源三处都不同，外来的 `$type` 在注册表里查不到 —— 读侧会退回声明类型。

## 5. 真实的保存/加载在仓库哪里

Demo 的保存命令是 `TreeViewModel.Save`（`Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs`）—— 它先 `await Helper.CloseAsync();`，再把 `this.Serialize()` 写进指定文件。加载则把文件读回来 `json.Deserialize<TreeViewModel>()`，并经 `WorkflowDemoSession.FromTree` 重建会话（`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`）。

> JSON 的长度**不是**稳定断言 —— 它取决于程序集与类型版本。节点数、连线数与重跑结果是确定性的契约。

进入 `完整代码`，那里有单一可运行程序和运行声明。
