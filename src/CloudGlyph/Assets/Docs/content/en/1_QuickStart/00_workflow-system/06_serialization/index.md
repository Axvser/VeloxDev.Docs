# Workflow System — Serialize & Rebuild the Tree

Persist the whole graph — nodes, slots, links, layout and custom `[VeloxProperty]` state — as JSON, then rebuild it from that JSON. Whole-tree serialization is provided by the extension package `VeloxDev.Core.Extension` (`VeloxDev.MVVM.Serialization.ComponentModelEx`), so this page first adds that reference to the console project from [Install & Create the Project](../01_install/index.md).

## 1. Reference the serialization extension

The compile-and-run pages only needed `VeloxDev.Core`. JSON serialization lives in `VeloxDev.Core.Extension`; add it as a project reference (the demo's save path uses exactly this assembly):

```bash
dotnet add reference ..\Src\Core\VeloxDev.Core.Extension\VeloxDev.Core.Extension.csproj
```

(or, if you consume NuGet packages: `dotnet add package VeloxDev.Core.Extension`).

**Expected result:** `dotnet restore` succeeds and a component file can `using VeloxDev.MVVM.Serialization;`.

## 2. Serialize the tree to JSON and rebuild it

`Serialize()` / `Deserialize<T>()` are extension methods on any `INotifyPropertyChanged` ViewModel (`VeloxDev.MVVM.Serialization.ComponentModelEx`, source: `Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`). The serializer writes **public writable properties only** (the generator's computed properties such as `RuntimeId` are excluded), uses Newtonsoft `TypeNameHandling.Auto` so polymorphic node instances round-trip, and goes through the parameterless constructor on the way back — where `InitializeWorkflow()` re-installs each Helper and its preset default slots before the JSON values are applied:

```csharp
using VeloxDev.MVVM.Serialization;

// Flush running work before saving — the same call the demo's Save does.
await tree.GetHelper().CloseAsync();

var json = tree.Serialize();
var copy = json.Deserialize<QuickTree>();

Console.WriteLine($"copy Nodes={copy.Nodes.Count} Links={copy.Links.Count} " +
                  $"origin={copy.Layout.OriginSize.Width}x{copy.Layout.OriginSize.Height}");
```

**Expected result:** `copy.Nodes.Count == 3`, `copy.Links.Count == 2`, and `copy.Layout.OriginSize` is `2400x850`. The `CompileContext` a node received during a previous compile is *not* persisted (its setter is private) — it is re-injected on the next compile.

## 3. Round-trip: run the rebuilt copy

The strongest round-trip check is that the deserialized tree compiles and runs identically to the original:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var tickerCopy = copy.Nodes.OfType<TickerNode>().Single();
var copyGraphs = await new CompilerViewModel().CompileAsync(
    tickerCopy, CompileRole.Root, CancellationToken.None);
var copyCtx = new RuntimeContext();
await new RuntimeEngine().RunAsync(copyGraphs[0], copyCtx, CancellationToken.None);

Console.WriteLine(copyCtx.Status);   // Completed
Console.WriteLine(copyCtx.Data);     // tick->bias->print   (same chain as the original)
```

**Expected result:** the rebuilt `QuickTree` runs the same `Ticker → Bias → Printer` chain and yields the same `context.Data == "tick->bias->print"` as the forward run on the original tree ([Compile & run forward](../04_compile-and-run/index.md)).

## 4. Where save/load lives in the real repository

The demo's save command is `TreeViewModel.Save` in `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` — it flushes with `await Helper.CloseAsync();`, then writes `this.Serialize()` to the requested file. Loading reads a JSON file back with `json.Deserialize<TreeViewModel>()` (see the per-platform `WorkflowView` / demo code) and rebuilds a session via `WorkflowDemoSession.FromTree` (`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`).

> The JSON length is not a stable assertion (it depends on assembly/type versions); the node/link counts and the re-run result are the deterministic contract.

Go to [Verify & complete code](../07_complete-code/index.md) for the single-file program and the run declaration.
