# Workflow System — 完整代码

下面的程序就是整条核心流程 —— 搭画布、正向编译、编译一个结果、序列化并重建 —— 全在一个 `Program.cs` 里。它用到的每样东西都在本快速开始的前面几页定义过，没有任何省略。

| 标识符 | 定义在哪 |
|---|---|
| `QuickTree`、`QuickSlot`、`QuickLink` | `Components.cs` —— 见 `02_定义组件` |
| `TickerNode` / `BiasNode` / `PrinterNode` 及其 Helper | `TickerNode.cs`、`BiasNode.cs`、`PrinterNode.cs` —— 见 `02_定义组件` |
| `FlakyNode` / `FlakyHelper` | 见 `10_重试与补偿` |
| `BoomNode` / `BoomHelper` | 见 `10_重试与补偿` |
| `SourceNode`、`LeftNode`、`RightNode`、`BranchClock` | `FanOutNodes.cs` —— 见 `12_并行与大纲` |
| 项目文件（引用、`net10.0`） | 见 `01_安装` |

组件与节点文件在各自页面里全文给出；每个文件声明一个组件（或一个节点加它的 Helper）。把它们和 `Program.cs` 一起建在 `WorkflowQuickStart` 项目里。

`Program.cs`：

```csharp
using System.Diagnostics;
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM.Serialization;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart
{
    internal static class Program
    {
        private static async Task Main()
        {
            // 1. 在可编辑画布上搭出这张图。
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

            Console.WriteLine($"[1] Nodes={tree.Nodes.Count} Links={tree.Links.Count}");

            // 2. 正向（Root）编译 + 运行时运行。
            var compiler = new CompilerViewModel();
            var rootGraph = (await compiler.CompileAsync(
                ticker, CompileRole.Root, CancellationToken.None))[0];
            var forward = new RuntimeContext();
            await new RuntimeEngine().RunAsync(rootGraph, forward, CancellationToken.None);
            Console.WriteLine($"[2] root: {forward.Status} data={forward.Data} attempt={forward.Attempt} outcome={forward.Outcome}");
            Console.WriteLine($"[2] orders: {ticker.CompileContext!.Order},{bias.CompileContext!.Order},{printer.CompileContext!.Order}");
            Console.WriteLine($"[2] entries={rootGraph.Entries.Count} first={rootGraph.Entries[0].GetType().Name}");
            foreach (var row in CompiledOutline.Of(rootGraph))
                Console.WriteLine($"[2] outline: {new string(' ', row.Depth * 2)}{row.Kind} | {row.Label}");

            // 3. 终端（结果）编译 + 运行时运行。
            var resultGraph = (await compiler.CompileAsync(
                bias, CompileRole.Terminal, CancellationToken.None))[0];
            var result = new RuntimeContext { Target = bias };
            await new RuntimeEngine().RunAsync(resultGraph, result, CancellationToken.None);
            Console.WriteLine($"[3] result: {result.Status} data={result.Data} reached={result.TargetReached}");

            // 4. 把整棵树序列化成 JSON，重建，再跑一遍。
            var json = tree.Serialize();
            var copy = json.Deserialize<QuickTree>();
            var tickerCopy = copy.Nodes.OfType<TickerNode>().Single();
            var copyGraphs = await new CompilerViewModel().CompileAsync(
                tickerCopy, CompileRole.Root, CancellationToken.None);
            var copyCtx = new RuntimeContext();
            await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);
            Console.WriteLine($"[4] copy: Nodes={copy.Nodes.Count} Links={copy.Links.Count} {copyCtx.Status} data={copyCtx.Data}");

            // 5. 执行门：握住运行，再放开。
            var gate = new ManualExecutionGate();
            gate.Pause();
            var gated = new RuntimeContext { ExecutionGate = gate };
            var gatedRun = new RuntimeEngine().RunAsync(rootGraph, gated, CancellationToken.None);
            await Task.Delay(80);
            Console.WriteLine($"[5] paused: status={gated.Status} isPaused={gate.IsPaused} running={gated.IsRunning} data={gated.Data ?? "<null>"}");
            gate.Resume();
            await gatedRun;
            Console.WriteLine($"[5] resumed: status={gated.Status} data={gated.Data} outcome={gated.Outcome}");

            // 6. 干净一轮上的观察者 + 错误接收器。
            var observed = new List<string>();
            var sink = new List<string>();
            var observedCtx = new RuntimeContext
            {
                Observer = new DelegateExecutionObserver(o =>
                {
                    if (o.Kind is ExecutionObservationKind.NodeStarted or ExecutionObservationKind.NodeSucceeded)
                        observed.Add($"{o.Kind}:{o.Node?.GetType().Name}");
                }),
                ErrorSink = new DelegateExecutionErrorSink(e => sink.Add($"{e.Phase}:{e.Message}")),
            };
            await new RuntimeEngine().RunAsync(rootGraph, observedCtx, CancellationToken.None);
            Console.WriteLine($"[6] observed: {string.Join(", ", observed)}");
            Console.WriteLine($"[6] sink on a clean run: {sink.Count} records");

            // 7. 检查点：第一个节点之后停下，再从保存下来的位置恢复。
            var store = new InMemoryCheckpointStore();
            var cts = new CancellationTokenSource();
            var partial = new RuntimeContext
            {
                CheckpointStore = store,
                Observer = new DelegateExecutionObserver(o =>
                {
                    if (o.Kind == ExecutionObservationKind.NodeSucceeded) cts.Cancel();
                }),
            };
            try
            {
                await new RuntimeEngine().RunAsync(rootGraph, partial, cts.Token, null);
            }
            catch (OperationCanceledException) { }
            var saved = (await store.LoadAsync(CancellationToken.None))!;
            Console.WriteLine($"[7] checkpoint: attempt={saved.Attempt} outputs={saved.Outputs.Count} shape=<三个 RuntimeId GUID>");

            var resumed = new RuntimeContext();
            await new RuntimeEngine().RunAsync(rootGraph, resumed, CancellationToken.None, saved);
            Console.WriteLine($"[7] resume: status={resumed.Status} data={resumed.Data} outcome={resumed.Outcome}");

            var refused = new RuntimeContext();
            try
            {
                await new RuntimeEngine().RunAsync(copyGraphs[0], refused, CancellationToken.None, saved);
                Console.WriteLine("[7] refused: NO (unexpected)");
            }
            catch (InvalidOperationException ex)
            {
                Console.WriteLine($"[7] refused on a serialized copy: {ex.Message.Split(':')[0]} status={refused.Status}");
            }

            // 8. 抖动节点上的重试策略。
            var flakyTree = new QuickTree();
            var flaky = new FlakyNode { Anchor = new Anchor(0, 0, 0) };
            flakyTree.GetHelper().CreateNode(flaky);
            var retryGraph = (await compiler.CompileAsync(
                flaky, CompileRole.Root, CancellationToken.None))[0];
            var retryCtx = new RuntimeContext
            {
                RetryPolicy = new ExponentialBackoffRetry(maxAttempts: 3, baseDelayMs: 1),
            };
            await new RuntimeEngine().RunAsync(retryGraph, retryCtx, CancellationToken.None);
            Console.WriteLine($"[8] retry: status={retryCtx.Status} data={retryCtx.Data} drives={FlakyHelper.Attempts} attempt={retryCtx.Attempt}");
            Console.WriteLine($"[8] retry logs: {string.Join(" | ", retryCtx.Logs)}");

            // 9. 日志写入器 + 有界的日志保留。
            var logPath = Path.Combine(Path.GetTempPath(), "veloxqs-run.log");
            if (File.Exists(logPath)) File.Delete(logPath);
            RuntimeContext capped;
            using (var writer = TextWriterLogWriter.For(logPath))
            {
                capped = new RuntimeContext { LogWriter = writer, MaxRetainedLogs = 2 };
                await new RuntimeEngine().RunAsync(rootGraph, capped, CancellationToken.None);
            }
            var fileLines = File.ReadAllLines(logPath);
            Console.WriteLine($"[9] logfile: fileLines={fileLines.Length} retained={capped.Logs.Count} snapshot={capped.SnapshotLogs().Length}");
            Console.WriteLine($"[9] retained: {string.Join(" | ", capped.SnapshotLogs())}");
            Console.WriteLine($"[9] file head: {fileLines[0]}");

            // 10. 失败一轮上的补偿。
            var boomTree = new QuickTree();
            var boom = new BoomNode { Anchor = new Anchor(0, 0, 0) };
            boomTree.GetHelper().CreateNode(boom);
            var boomGraph = (await compiler.CompileAsync(
                boom, CompileRole.Root, CancellationToken.None))[0];
            var compensated = new List<string>();
            var boomCtx = new RuntimeContext
            {
                Compensation = new DelegateExecutionCompensation(c => compensated.Add(c.Node.GetType().Name)),
            };
            try
            {
                await new RuntimeEngine().RunAsync(boomGraph, boomCtx, CancellationToken.None);
            }
            catch (InvalidOperationException) { }
            Console.WriteLine($"[10] compensate: status={boomCtx.Status} outcome={boomCtx.Outcome} currentOrder={boomCtx.CurrentOrder} reversed=[{string.Join(", ", compensated)}]");

            // 11. 并行扇出：默认并发，MaxParallelBranches = 1 时串行。
            var fanTree = new QuickTree();
            var fanHelper = fanTree.GetHelper();
            var source = new SourceNode { Anchor = new Anchor(0, 0, 0) };
            var left = new LeftNode { Anchor = new Anchor(200, 0, 0) };
            var right = new RightNode { Anchor = new Anchor(400, 0, 0) };
            fanHelper.CreateNode(source);
            fanHelper.CreateNode(left);
            fanHelper.CreateNode(right);
            SetChannel(source.OutputSlot, SlotChannel.MultipleTargets);
            SetChannel(left.InputSlot, SlotChannel.OneSource);
            SetChannel(right.InputSlot, SlotChannel.OneSource);
            Connect(fanHelper, source.OutputSlot!, left.InputSlot!);
            Connect(fanHelper, source.OutputSlot!, right.InputSlot!);

            var fanGraph = (await compiler.CompileAsync(
                source, CompileRole.Root, CancellationToken.None))[0];
            Console.WriteLine($"[11] segments: {string.Join(", ", fanGraph.Entries.Select(e => e.GetType().Name))}");

            BranchClock.Starts.Clear(); BranchClock.Ends.Clear();
            await new RuntimeEngine().RunAsync(fanGraph, new RuntimeContext(), CancellationToken.None);
            Console.WriteLine($"[11] MaxParallelBranches=null: overlap={Overlap(BranchClock.Starts, BranchClock.Ends)}");

            BranchClock.Starts.Clear(); BranchClock.Ends.Clear();
            var oneAtATime = new RuntimeContext { MaxParallelBranches = 1 };
            await new RuntimeEngine().RunAsync(fanGraph, oneAtATime, CancellationToken.None);
            Console.WriteLine($"[11] MaxParallelBranches=1:    overlap={Overlap(BranchClock.Starts, BranchClock.Ends)}");
        }

        private static bool Overlap(List<(int Index, int Tick)> starts, List<(int Index, int Tick)> ends)
        {
            if (starts.Count < 2 || ends.Count < 2) return false;
            var s0 = starts.First(s => s.Index == 0).Tick;
            var s1 = starts.First(s => s.Index == 1).Tick;
            var e0 = ends.First(e => e.Index == 0).Tick;
            var e1 = ends.First(e => e.Index == 1).Tick;
            return s0 < e1 && s1 < e0;
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

**预期结果：** 第 1–4 步与前面几页一致（`Nodes=3 Links=2`、`Completed data=tick->bias->print`、`reached=True`、重建的副本跑出同一条链）；第 5–11 步走一遍宿主能力层。完整的实测输出在 `13_验证与运行声明`。

没有省略号，上面每个标识符都在本文件里定义，或在本页顶部的表格点名的某个组件文件里定义。`namespace WorkflowQuickStart` 必须与各组件文件用的那个一致。

下一步去 `08_暂停与恢复` 看第一项能力，或去 `13_验证与运行声明` 看实测运行。
