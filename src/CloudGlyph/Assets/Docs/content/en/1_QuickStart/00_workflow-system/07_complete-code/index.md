# Workflow System — Verify & Complete Code

## 1. Verification against the real repository

- **Compiler / runtime tests** — `Src/Core/VeloxDev.Core.Test/WorkflowSystem/CompilerEx/`:
    `CompileDecompositionTests.cs` (segment shapes), `RuntimeEngineRunTests.cs` (chain data flow, dynamic router, fan-out, `IGroupData` joins, terminal branch, error stop), `RuntimeRedirectTests.cs` (redirect contract), `EntrySemanticsTests.cs` (the three entry points), `CompileToReverseTests.cs` (Terminal / ancestor-cone / no-fabrication rules). Their `ProbeGraph.cs` / `ProbeNodes.cs` show the minimal wiring the compiler and engine actually consume.
- **Value-type / topology tests** — `Src/Core/VeloxDev.Core.Test/WorkflowSystem/` (`AnchorTests`, `SlotEnumeratorTests`, `WorkflowTreeExTests`, …).
- **Serialization tests** — `Src/Core/VeloxDev.Core.Extension.Test/Serialization/ComponentModelExTests.cs` and `Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions/WorkflowSerializationTests.cs`.
- **Demo** — the shared, framework-agnostic session builder `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs` builds the full voltage-analysis chain (`Controller → Timer → Generate Dataset → [Stats, Dist, Anomaly] → Merge Report (IGroupData) → Enum Selector → [Report High/Low/Zero]`). Per-platform demos (`Examples/Workflow/<WPF|Avalonia|WinUI|MAUI|WinForms|Blazor> Trimmed/Demo`) render it. The Workflow Agent feature (`01_workflow-agent`) and this feature's API/SE pages exercise the same compile & run APIs used here.

## 2. Complete code — one self-contained `Program.cs`

The earlier pages defined the components and the build steps as separate files. This page consolidates the `QuickTree` / `QuickSlot` / `QuickLink` components, the `Ticker` / `Bias` / `Printer` nodes with their helpers ([Define the components](../02_define-components/index.md)), and the build/compile/run/serialize flow ([Build the graph](../03_build-a-graph/index.md), [Compile & run forward](../04_compile-and-run/index.md), [Compile a result (Terminal)](../05_terminal-compile/index.md), [Serialize & rebuild](../06_serialization/index.md)) into **one** file. Copy it into a console project that references `VeloxDev.Core` and `VeloxDev.Core.Extension` (see [Install & Create the Project](../01_install/index.md)); every identifier used below is defined in this file.

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.MVVM.Serialization;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart
{
    [WorkflowBuilder.Tree<TreeHelper>]
    public partial class QuickTree
    {
        public QuickTree() => InitializeWorkflow();
    }

    [WorkflowBuilder.Slot<SlotHelper>]
    public partial class QuickSlot
    {
        public QuickSlot() => InitializeWorkflow();
    }

    [WorkflowBuilder.Link<LinkHelper>]
    public partial class QuickLink
    {
        public QuickLink() => InitializeWorkflow();

        [VeloxProperty] private bool usePolyline = true;
    }

    [WorkflowBuilder.Node<TickerHelper>(workSemaphore: 1)]
    public partial class TickerNode : ICompileTimeAware
    {
        public TickerNode() => InitializeWorkflow();

        [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
        [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

        public ICompileContext? CompileContext { get; private set; }

        public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
    }

    public class TickerHelper : NodeHelper<TickerNode>
    {
        public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
        {
            if (Component is null) return Task.FromResult<object?>(null);
            return Task.FromResult<object?>("tick");
        }
    }

    [WorkflowBuilder.Node<BiasHelper>(workSemaphore: 1)]
    public partial class BiasNode : ICompileTimeAware
    {
        public BiasNode() => InitializeWorkflow();

        [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
        [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

        public ICompileContext? CompileContext { get; private set; }

        public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
    }

    public class BiasHelper : NodeHelper<BiasNode>
    {
        public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
        {
            if (Component is null) return Task.FromResult<object?>(null);
            var value = context.Data as string ?? "none";
            return Task.FromResult<object?>($"{value}->bias");
        }
    }

    [WorkflowBuilder.Node<PrinterHelper>(workSemaphore: 1)]
    public partial class PrinterNode : ICompileTimeAware
    {
        public PrinterNode() => InitializeWorkflow();

        [VeloxProperty] public partial QuickSlot InputSlot { get; set; }
        [VeloxProperty] public partial QuickSlot OutputSlot { get; set; }

        public ICompileContext? CompileContext { get; private set; }

        public void AttachCompileTimeContext(ICompileContext context) => CompileContext = context;
    }

    public class PrinterHelper : NodeHelper<PrinterNode>
    {
        public override Task<object?> ReceiveAsync(ITaskContext context, CancellationToken ct)
        {
            if (Component is null) return Task.FromResult<object?>(null);
            var value = context.Data as string ?? "none";
            return Task.FromResult<object?>($"{value}->print");
        }
    }

    internal static class Program
    {
        private static async Task Main()
        {
            // 1. Build the graph on an editable canvas (tree + nodes + channels + links).
            var tree = new QuickTree();
            tree.Layout.OriginSize = new Size(2400, 850);
            var helper = tree.GetHelper();

            var ticker = new TickerNode { Anchor = new Anchor(60, 60, 0) };
            var bias = new BiasNode { Anchor = new Anchor(460, 60, 0) };
            var printer = new PrinterNode { Anchor = new Anchor(860, 60, 0) };

            helper.CreateNode(ticker);
            helper.CreateNode(bias);
            helper.CreateNode(printer);

            SetChannel(ticker.OutputSlot, SlotChannel.OneTarget);
            SetChannel(bias.InputSlot, SlotChannel.OneSource);
            SetChannel(bias.OutputSlot, SlotChannel.OneTarget);
            SetChannel(printer.InputSlot, SlotChannel.OneSource);

            Connect(helper, ticker.OutputSlot!, bias.InputSlot!);
            Connect(helper, bias.OutputSlot!, printer.InputSlot!);

            Console.WriteLine($"Nodes={tree.Nodes.Count} Links={tree.Links.Count}");
            // Nodes=3 Links=2

            // 2. Forward (Root) compile + runtime run: compile everything reachable from Ticker.
            var compiler = new CompilerViewModel();
            var rootGraph = (await compiler.CompileAsync(
                ticker, CompileRole.Root, CancellationToken.None))[0];
            var forward = new RuntimeContext();
            await new RuntimeEngine().RunAsync(rootGraph, forward, CancellationToken.None);
            Console.WriteLine($"root:   {forward.Status}  data={forward.Data}");
            // root:   Completed  data=tick->bias->print

            // 3. Terminal (result) compile + runtime run: compile only the ancestor cone of Bias.
            var resultGraph = (await compiler.CompileAsync(
                bias, CompileRole.Terminal, CancellationToken.None))[0];
            var result = new RuntimeContext { Target = bias };
            await new RuntimeEngine().RunAsync(resultGraph, result, CancellationToken.None);
            Console.WriteLine($"result: {result.Status}  data={result.Data}  reached={result.TargetReached}");
            // result: Completed  data=tick->bias  reached=True

            // 4. Serialize the whole tree to JSON, then rebuild and re-run the copy.
            var json = tree.Serialize();
            var copy = json.Deserialize<QuickTree>();
            Console.WriteLine($"copy Nodes={copy.Nodes.Count} Links={copy.Links.Count}");

            var tickerCopy = copy.Nodes.OfType<TickerNode>().Single();
            var copyGraphs = await new CompilerViewModel().CompileAsync(
                tickerCopy, CompileRole.Root, CancellationToken.None);
            var copyCtx = new RuntimeContext();
            await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);
            Console.WriteLine($"copy:   {copyCtx.Status}  data={copyCtx.Data}");
            // copy:   Completed  data=tick->bias->print
        }

        private static void SetChannel(QuickSlot slot, SlotChannel channel)
            => slot.SetChannelCommand.Execute(channel);

        private static void Connect(IWorkflowTreeViewModelHelper helper, QuickSlot sender, QuickSlot receiver)
        {
            helper.SendConnection(sender);
            helper.ReceiveConnection(receiver);
        }
    }
}
```

**Expected result:** the forward root run reports `data=tick->bias->print` (the whole chain); the terminal result run stops at the target and reports `data=tick->bias reached=True`; the deserialized copy re-runs the same chain. This is the same API surface the tests and the `WorkflowDemoSession` demo exercise.

## 3. Run declaration

- ⚠️ **Not actually built/run during documentation authoring — statically verified only.** Every type, member and signature above was cross-checked against the real sources: component patterns from `Examples/Workflow/Common/Lib/ViewModels/Workflow/` (`WorkflowDemoSession.cs`, `ControllerViewModel.cs`, `TimerNodeViewModel.cs`, `TreeViewModel.cs`, `Helper/TimerHelper.cs`); compile API `CompilerViewModel.CompileAsync(node, CompileRole, ct)` and model types `ChainSegment` / `BranchSegment` / `ParallelSegment` in `Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/`; runtime `RuntimeEngine.RunAsync` + `RuntimeContext` (`Target` / `TargetReached` / `Status` / `Data` / `Attempt`); helpers `NodeHelper<T>` / `IWorkflowNodeViewModelHelper`; serialization `VeloxDev.MVVM.Serialization.ComponentModelEx` in `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`. The sample targets `net10.0` and requires a .NET SDK 9.0+ (C# 13 partial properties). Build it inside a real console project to execute; the test and demo references in section 1 show where each behavior is exercised by the test suite.
