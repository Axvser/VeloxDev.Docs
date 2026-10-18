# 工作流系统 — 序列化并重建树

归档引擎是 `VeloxDev.Serialization`，随 **`VeloxDev.Core`** 发布 —— 前面页面已经引用该包，因此不需要新安装。另外两份文档放在 `VeloxDev.Core.Extension`：编译图与运行检查点（「编译结果（Terminal）」）。

序列化是**封闭世界**的：只有当源生成器为某类型生成了 reader 与 writer，它才能往返。没有反射、没有回退，所以未登记的类型会大声失败，而不是半空地回来。

## 1. 生成器接受哪些类型

进入封闭世界有四种方式，任一种即可（`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:588-614`）：

| 方式 | 适用 |
|---|---|
| 实现四个组件接口之一 | `IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel` |
| 携带 `[WorkflowBuilder.*]` 特性 | 生成的组件模板 |
| 拥有 `[VeloxProperty]` **字段** | 你自己的 view model —— `QuickTree` 走的就是这条路 |
| 携带 `[Archivable]` | 不是 view model 的普通文档 |

```csharp
// A view model: the [VeloxProperty] field promotes an observable property,
// so the class must be partial.
// Source: Src/Core/VeloxDev.Core.Extension.Test/Serialization/ViewModelSerializerContractTests.cs:23-26
internal sealed partial class ContractModel
{
    [VeloxProperty] private int count;
}

// A plain document: [Archivable] alone is enough, and partial is not needed.
// Source: Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Runtime/Model/ExecutionCheckpoints.cs:27-28
[Archivable]
public sealed class ExecutionCheckpoint
```

成员按**声明顺序**收集为「带 public setter 的 public 属性」；`[VeloxProperty]` 字段随后，继承成员最后。这个顺序是字节级契约，不是风格选择。

## 2. 保存并重建

```csharp
using VeloxDev.Serialization;

// Flush running work before saving — the same call the demo's Save makes.
await tree.GetHelper().CloseAsync();

var json = tree.Serialize();
var copy = json.Deserialize<QuickTree>();

Console.WriteLine($"copy Nodes={copy.Nodes.Count} Links={copy.Links.Count} " +
                  $"origin={copy.Layout.OriginSize.Width}x{copy.Layout.OriginSize.Height}");
```

**预期结果：** `copy.Nodes.Count == 3`、`copy.Links.Count == 2`，且 `copy.Layout.OriginSize` 为 `2400x850`。节点早先编译时收到的 `CompileContext` **不在**文档里 —— 它的 setter 不是 public —— 下次编译时会再次注入。

`Serialize<T>()` / `Deserialize<T>()` 是任意 `INotifyPropertyChanged` view model 上的扩展方法（`VeloxDev.Serialization.ViewModelSerializer`）。`TryDeserialize<T>(out var copy)` 是不抛异常的版本：对 null、空白或格式错误文本返回 `false`。

## 3. 往返：运行重建后的副本

最强的检查是重建后的树编译、运行结果与原树完全一致：

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var tickerCopy = copy.Nodes.OfType<TickerNode>().Single();
var copyGraphs = await new CompilerViewModel().CompileAsync(
    tickerCopy, CompileRole.Root, CancellationToken.None);
var copyCtx = new RuntimeContext();
await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);

Console.WriteLine(copyCtx.Status);   // Completed
Console.WriteLine(copyCtx.Data);     // tick->bias->print   (the same chain as the original)
```

**预期结果：** 重建的 `QuickTree` 运行 `Ticker → Bias → Printer`，得到与原始树正向运行相同的 `copyCtx.Data == "tick->bias->print"`（「编译并运行（Root）」）。

## 4. 往返出错的四种方式

| 症状 | 原因 | 修复 |
|---|---|---|
| `MissingWriter` / `MissingReader` | 该类型从未进入封闭世界 —— 没有标注，也没有成员触及它。 | 加 `[Archivable]`，或从已有该特性的类型触及它。 |
| 成员在文档里直接缺席 | 它没有 public setter（`CompileContext` 就是这样被丢掉的）。 | `[Archive(ArchiveOptions.KeepProperty)]` 能写出它 —— 但仍读不回来。 |
| 枚举回来变成数字 | 枚举默认写为底层整数。 | 在那一成员上加 `[Archive(ArchiveOptions.EnumName)]`，写值名。 |
| 读取时 `InvalidOperationException` | 文档缺少 `required` 成员。 | 写入该成员，或去掉 `required`。 |

归档格式**不与** `System.Text.Json` 或 Newtonsoft 互通：类型判别符、集合形状与成员集合都不同，外部 `$type` 在注册表里解析不到 —— reader 回退到声明类型。

## 5. 保存与加载在仓库中的位置

demo 的保存命令是 `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` 中的 `TreeViewModel.Save` —— 它先 `await Helper.CloseAsync();` 冲刷，再把 `this.Serialize()` 写到请求的文件。加载时读回文件，用 `json.Deserialize<TreeViewModel>()` 重建，并通过 `WorkflowDemoSession.FromTree` 恢复会话（`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`）。

> JSON 长度不是稳定断言 —— 它依赖程序集与类型版本。节点/连线数量与重跑结果才是确定性契约。

前往「完整代码」，查看单文件程序与运行声明。
