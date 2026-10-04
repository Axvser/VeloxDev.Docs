# Workflow System — Complete Code

The program below is the whole core flow — build the canvas, compile forward, compile a result, serialize and rebuild — in one `Program.cs`. Everything it uses is defined on an earlier page of this Quick Start; nothing is elided.

| Identifier | Defined in |
|---|---|
| `QuickTree`, `QuickSlot`, `QuickLink` | `Components.cs` — see `02_define-components` |
| `TickerNode` / `BiasNode` / `PrinterNode` and their helpers | `TickerNode.cs`, `BiasNode.cs`, `PrinterNode.cs` — see `02_define-components` |
| `FlakyNode` / `FlakyHelper` | see `10_retry-and-compensate` |
| `BoomNode` / `BoomHelper` | see `10_retry-and-compensate` |
| `SourceNode`, `LeftNode`, `RightNode`, `BranchClock` | `FanOutNodes.cs` — see `12_parallel-and-outline` |
| the project file (references, `net10.0`) | see `01_install` |

The component and node files are reproduced in full on those pages; each declares one component (or one node plus its helper). Create them in the `WorkflowQuickStart` project alongside `Program.cs`.

`Program.cs`:

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
            // 1. Build the graph on an editable canvas.
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

            // 2. Forward (Root) compile + runtime run.
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

            // 3. Terminal (result) compile + runtime run.
            var resultGraph = (await compiler.CompileAsync(
                bias, CompileRole.Terminal, CancellationToken.None))[0];
            var result = new RuntimeContext { Target = bias };
            await new RuntimeEngine().RunAsync(resultGraph, result, CancellationToken.None);
            Console.WriteLine($"[3] result: {result.Status} data={result.Data} reached={result.TargetReached}");

            // 4. Serialize the whole tree to JSON, rebuild, re-run.
            var json = tree.Serialize();
            var copy = json.Deserialize<QuickTree>();
            var tickerCopy = copy.Nodes.OfType<TickerNode>().Single();
            var copyGraphs = await new CompilerViewModel().CompileAsync(
                tickerCopy, CompileRole.Root, CancellationToken.None);
            var copyCtx = new RuntimeContext();
            await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);
            Console.WriteLine($"[4] copy: Nodes={copy.Nodes.Count} Links={copy.Links.Count} {copyCtx.Status} data={copyCtx.Data}");

            // 5. Execution gate: hold the run, then let it go.
            var gate = new ManualExecutionGate();
            gate.Pause();
            var gated = new RuntimeContext { ExecutionGate = gate };
            var gatedRun = new RuntimeEngine().RunAsync(rootGraph, gated, CancellationToken.None);
            await Task.Delay(80);
            Console.WriteLine($"[5] paused: status={gated.Status} isPaused={gate.IsPaused} running={gated.IsRunning} data={gated.Data ?? "<null>"}");
            gate.Resume();
            await gatedRun;
            Console.WriteLine($"[5] resumed: status={gated.Status} data={gated.Data} outcome={gated.Outcome}");

            // 6. Observer + error sink on a clean run.
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

            // 7. Checkpoint: stop after the first node, then resume from the saved place.
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
            Console.WriteLine($"[7] checkpoint: attempt={saved.Attempt} outputs={saved.Outputs.Count} shape=<three RuntimeId GUIDs>");

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

            // 8. Retry policy on a flaky node.
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

            // 9. Log writer + bounded log retention.
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

            // 10. Compensation on a failing run.
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

            // 11. Parallel fan-out: concurrent by default, serialised when MaxParallelBranches = 1.
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

**Expected result:** steps 1–4 mirror the earlier pages (`Nodes=3 Links=2`, `Completed data=tick->bias->print`, `reached=True`, the rebuilt copy re-runs the same chain); steps 5–11 exercise the host-capability layer. The full recorded output is on `13_verify-and-run-declaration`.

No ellipses, and every identifier above is defined in this file or in one of the component files named in the table at the top. The `namespace WorkflowQuickStart` must match the one the component files use.

Go to `08_pause-and-resume` for the first capability, or `13_verify-and-run-declaration` for the recorded run.
