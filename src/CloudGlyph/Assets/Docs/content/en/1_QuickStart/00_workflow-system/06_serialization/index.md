# Workflow System — Serialize & Rebuild the Tree

The archive engine is `VeloxDev.Serialization`, and it ships in **`VeloxDev.Core`** — the package the earlier pages already reference, so there is nothing new to install. Two documents live in `VeloxDev.Core.Extension` instead: a compiled graph and a run's checkpoint (`Compile a result (Terminal)`).

Serialization is **closed-world**: a type round-trips only if the source generator emitted a reader and a writer for it. There is no reflection and no fallback, so an unseen type fails loudly instead of coming back half-empty.

## 1. What the generator accepts

Four ways into the closed world, any one of which is enough (`Src/Generators/VeloxDev.Core.Generator/Base/VeloxJsonModel.cs:588-614`):

| Way in | For |
|---|---|
| Implement one of the four component interfaces | `IWorkflowTreeViewModel` / `IWorkflowNodeViewModel` / `IWorkflowSlotViewModel` / `IWorkflowLinkViewModel` |
| Carry a `[WorkflowBuilder.*]` attribute | a generated component template |
| Have a `[VeloxProperty]` **field** | your own view models — this is `QuickTree`'s route |
| Carry `[Archivable]` | a plain document that is not a view model |

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

Members are collected as **public properties with a public setter, in declaration order**; `[VeloxProperty]` fields follow, inherited members last. That order is a byte-level contract, so it is not a style choice.

## 2. Save and rebuild

```csharp
using VeloxDev.Serialization;

// Flush running work before saving — the same call the demo's Save makes.
await tree.GetHelper().CloseAsync();

var json = tree.Serialize();
var copy = json.Deserialize<QuickTree>();

Console.WriteLine($"copy Nodes={copy.Nodes.Count} Links={copy.Links.Count} " +
                  $"origin={copy.Layout.OriginSize.Width}x{copy.Layout.OriginSize.Height}");
```

**Expected result:** `copy.Nodes.Count == 3`, `copy.Links.Count == 2`, and `copy.Layout.OriginSize` is `2400x850`. The `CompileContext` a node received during an earlier compile is **not** in the document — its setter is not public — and is injected again on the next compile.

`Serialize<T>()` / `Deserialize<T>()` are extension methods on any `INotifyPropertyChanged` view model (`VeloxDev.Serialization.ViewModelSerializer`). `TryDeserialize<T>(out var copy)` is the non-throwing form: it returns `false` on null, blank or malformed text instead of throwing.

## 3. Round-trip: run the rebuilt copy

The strongest check is that the rebuilt tree compiles and runs identically to the original:

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

**Expected result:** the rebuilt `QuickTree` runs `Ticker → Bias → Printer` and yields the same `copyCtx.Data == "tick->bias->print"` as the forward run on the original (`Compile a graph (Root) and run it`).

## 4. The four ways a round trip goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `MissingWriter` / `MissingReader` | The type never entered the closed world — nothing annotated it and no member reaches it. | Add `[Archivable]`, or reach it from a type that has it. |
| The member is simply absent from the document | It has no public setter (this is how `CompileContext` is dropped). | `[Archive(ArchiveOptions.KeepProperty)]` writes it — but it still will not read back. |
| An enum comes back as a number | Enums are written as their underlying integer by default. | `[Archive(ArchiveOptions.EnumName)]` on that one member writes the value's name. |
| `InvalidOperationException` on read | The document is missing a `required` member. | Write the member, or drop `required`. |

The archive format is **not** interchangeable with `System.Text.Json` or Newtonsoft: the type discriminator, the collection shapes and the member set all differ, and a foreign `$type` does not resolve in the registry — the reader falls back to the declared type.

## 5. Where save and load live in the repository

The demo's save command is `TreeViewModel.Save` in `Examples/Workflow/Common/Lib/ViewModels/Workflow/TreeViewModel.cs` — it flushes with `await Helper.CloseAsync();`, then writes `this.Serialize()` to the requested file. Loading reads the file back with `json.Deserialize<TreeViewModel>()` and rebuilds a session via `WorkflowDemoSession.FromTree` (`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`).

> The JSON length is not a stable assertion — it depends on assembly and type versions. The node and link counts, and the re-run result, are the deterministic contract.

Go to `Complete code` for the single-file program and the run declaration.
