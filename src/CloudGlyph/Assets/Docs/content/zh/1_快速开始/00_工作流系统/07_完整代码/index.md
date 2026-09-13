# 工作流系统 — 验证与完整代码

## 1. 在仓库里如何验证

**Demo（第一证据源）：** `Examples/Workflow/Common/Lib` 提供一张真实成品链，会话由 `WorkflowDemoSession.Create()` 构建（`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`）：

```text
Controller → Timer → Generate Dataset（普通节点扇出）
            → [Numeric Stats, Frequency Dist, Anomaly Scan]
            → join Merge Report（多输入汇合，收 IGroupData 并按档位打分）
            → Enum Selector（ICompileTimeRouter，Dynamic 运行期按 grade 选支）
            → [Report High / Report Low / Report Zero]
```

它覆盖了 `ChainSegment`（线性）、`ParallelSegment`（扇出）、`IGroupData`（汇合）与 `BranchSegment`（路由器）四类编译段；控制器上的“编译/运行”按钮就是 `ControllerViewModel` 里 `Compiler.CompileAsync(this, CompileRole.Root)` + `new RuntimeEngine().RunAsync(...)`（`Examples/Workflow/Common/Lib/ViewModels/Workflow/ControllerViewModel.cs`）。路由器实现见 `EnumSelectorNodeViewModel.cs`。

**测试（语义边界）：** `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`：

- `CompileDecompositionTests` —— 线性→单 `ChainSegment`、动态 Router 保留全部分支、静态 Router 剪除未选支（下游 `Order = -1`）、普通节点扇出→`ParallelSegment`、`AccessAsync` 拒绝的边被剪枝。
- `RuntimeEngineRunTests` —— 数据沿会话链式传递、动态分支运行期选键、扇出各支读到同一源负载、双上游汇合收 `IGroupData`、无下游路由键=终止支、无 `IRedirectable` 出错→`Stopped`。
- `CompileToReverseTests` —— 目标中途锥从自身入口编译、Router 选中目标支→`TargetReached`、选中兄弟支→目标不驱动不编造值、多源漏斗→汇合、入口缺失时目标自己就是入口、非串-并联锥抛说明性异常。
- `RuntimeRedirectTests`、`EntrySemanticsTests` —— `IRedirectable` 重定向语义与“节点级 / 边级 / 链级”三条执行入口的边界。

## 2. 完整代码

单一最小可运行程序：控制台 `net9.0`，开启 `<ImplicitUsings>enable</ImplicitUsings>`，引用 [01 安装 / 添加依赖](../01_安装/index.md) 的 `VeloxDev.Core` + `VeloxDev.Core.Extension`（含源生成器）。本程序把前几页的 `CalcTree / SlotViewModel / CalcNode(+Helper)` 与四段执行逻辑拼成一份文件 —— 每个标识符都在本文件内定义。

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.MVVM.Serialization;
using VeloxDev.WorkflowSystem;

namespace Demo.QuickStart
{
    [WorkflowBuilder.Tree<TreeHelper>]
    public partial class CalcTree
    {
        public CalcTree() => InitializeWorkflow();
    }

    [WorkflowBuilder.Slot<SlotHelper>]
    public partial class SlotViewModel
    {
        public SlotViewModel() => InitializeWorkflow();
    }

    [WorkflowBuilder.Node<CalcNodeHelper>(workSemaphore: 1)]
    public partial class CalcNode : ICompileTimeAware
    {
        public CalcNode() => InitializeWorkflow();

        [VeloxProperty] private SlotViewModel input = new();
        [VeloxProperty] private SlotViewModel output = new();
        [VeloxProperty] private string title = "";
        [VeloxProperty] private string kind = "pass";
        [VeloxProperty] private double seed = 0;

        public ICompileContext? CompileContext { get; private set; }

        public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
    }

    public class CalcNodeHelper : NodeHelper<CalcNode>
    {
        public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
        {
            if (Component is null) return Task.FromResult<object?>(null);

            object? result = Component.Kind switch
            {
                "seed" => Component.Seed,
                "double" => context.Data is double d ? d * 2 : context.Data,
                _ => context.Data,
            };

            var order = Component.CompileContext is { } cc ? cc.Order : -1;
            Console.WriteLine($"  [{Component.Title}] kind={Component.Kind} order={order} result={result}");
            return Task.FromResult(result);
        }
    }

    internal static class Program
    {
        private static async Task Main()
        {
            // 1. Build the graph on an editable canvas (tree + nodes + channels + links).
            var tree = new CalcTree();
            tree.Layout.OriginSize = new Size(1200, 800);
            var helper = tree.GetHelper();

            var source = new CalcNode { Title = "Source", Kind = "double", Anchor = new Anchor(40, 200, 0) };
            var report = new CalcNode { Title = "Report", Kind = "pass", Anchor = new Anchor(420, 120, 0) };
            var discard = new CalcNode { Title = "Discard", Kind = "pass", Anchor = new Anchor(420, 360, 0) };

            helper.CreateNode(source);
            helper.CreateNode(report);
            helper.CreateNode(discard);

            source.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
            report.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
            discard.Input.SetChannelCommand.Execute(SlotChannel.OneSource);

            helper.SendConnection(source.Output);
            helper.ReceiveConnection(report.Input);
            helper.SendConnection(source.Output);
            helper.ReceiveConnection(discard.Input);

            Console.WriteLine($"Nodes={tree.Nodes.Count} Links={tree.Links.Count} " +
                              $"source.Output.Targets={source.Output.Targets.Count} " +
                              $"channels={source.Output.Channel}|{report.Input.Channel}|{discard.Input.Channel}");

            // 2. Forward compiled run (CompileRole.Root) — seed data 2.0.
            var compiler = new CompilerViewModel();
            var forwardGraphs = await compiler.CompileAsync(source, CompileRole.Root);
            var forwardGraph = forwardGraphs[0];
            Console.WriteLine($"Forward entries={forwardGraph.Entries.Count} " +
                              $"first={forwardGraph.Entries[0].GetType().Name} " +
                              $"second={forwardGraph.Entries[1].GetType().Name}");

            var forwardCtx = new RuntimeContext { Data = 2.0 };
            await new RuntimeEngine().RunAsync(forwardGraph, forwardCtx, CancellationToken.None);
            Console.WriteLine($"Forward status={forwardCtx.Status} data={forwardCtx.Data} " +
                              $"sourceOrder={source.CompileContext?.Order} reportOrder={report.CompileContext?.Order} " +
                              $"discardOrder={discard.CompileContext?.Order}");

            // 3. Terminal (reverse) compiled run: compute the Report value only.
            var terminalGraphs = await compiler.CompileAsync(report, CompileRole.Terminal);
            var terminalGraph = terminalGraphs[0];
            Console.WriteLine($"Terminal entries={terminalGraph.Entries.Count} " +
                              $"first={terminalGraph.Entries[0].GetType().Name}");

            var terminalCtx = new RuntimeContext { Data = 2.0, Target = report };
            await new RuntimeEngine().RunAsync(terminalGraph, terminalCtx, CancellationToken.None);
            Console.WriteLine($"Terminal status={terminalCtx.Status} targetReached={terminalCtx.TargetReached} " +
                              $"data={terminalCtx.Data}");

            // 4. Serialize the whole tree to JSON, then rebuild it from the JSON.
            var json = tree.Serialize();
            var copy = json.Deserialize<CalcTree>();
            Console.WriteLine($"copy Nodes={copy.Nodes.Count} Links={copy.Links.Count} " +
                              $"origin={copy.Layout.OriginSize.Width}x{copy.Layout.OriginSize.Height} jsonLen={json.Length}");

            var copySource = copy.Nodes.OfType<CalcNode>().First(n => n.Title == "Source");
            var copyGraphs = await new CompilerViewModel().CompileAsync(copySource, CompileRole.Root);
            var copyCtx = new RuntimeContext { Data = 2.0 };
            await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);
            Console.WriteLine($"copy run status={copyCtx.Status} data={copyCtx.Data}");
        }
    }
}
```

## 3. 运行声明

- ✅ **实际构建并运行于 2026-09-07。**
  - 环境：Windows 11；.NET SDK 10.0.400；`TargetFramework` `net9.0`；以 `ProjectReference` 引用本仓库 `Src/Core/VeloxDev.Core` 与 `Src/Core/VeloxDev.Core.Extension`（源码生成器经 `VeloxDev.Core` 传递自动启用）。
  - 上述 `Program.cs` 逐字编译运行，记录输出如下：

```text
Nodes=3 Links=2 source.Output.Targets=2 channels=MultipleTargets|OneSource|OneSource
Forward entries=2 first=ChainSegment second=ParallelSegment
  [Source] kind=double order=0 result=4
  [Report] kind=pass order=1 result=4
  [Discard] kind=pass order=2 result=4
Forward status=Completed data=4 sourceOrder=0 reportOrder=1 discardOrder=2
Terminal entries=1 first=ChainSegment
  [Source] kind=double order=0 result=4
  [Report] kind=pass order=1 result=4
Terminal status=Completed targetReached=True data=4
copy Nodes=3 Links=2 origin=1200x800 jsonLen=7366
  [Source] kind=double order=0 result=4
  [Report] kind=pass order=1 result=4
  [Discard] kind=pass order=2 result=4
copy run status=Completed data=4
```

`jsonLen=7366` 仅对当前程序集/类型版本成立；其余断言（节点/连线/编译段/结果值/`TargetReached`）对同一示例是确定性的。
