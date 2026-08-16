# Workflow System — Quick Start

## Workflow System

### Quick Start

VeloxDev WorkflowSystem is a cross-platform visual workflow editing engine. You build a graph from four kinds of components — **Tree**, **Node**, **Slot**, **Link** — decorate partial ViewModels with `[WorkflowBuilder.*]` attributes, and the Roslyn source generator emits the full ViewModel: properties, commands, helper wiring, undo/redo and serialization plumbing. The engine is UI-framework-agnostic; adapters (WPF / Avalonia) provide rendering behaviors. An optional AI layer (`VeloxDev.Core.Extension`) lets an LLM drive the editor through a toolkit of ~60 tools — that is the separate *Workflow Agent* feature (`01_workflow-agent`), not expanded here.

#### 1. Prerequisites

- **Supported targets** (from `Src/Core/VeloxDev.Core/VeloxDev.Core.csproj`): `netstandard2.0` / `netframework4.6.1` / `net5.0` / `netcoreapp3.0` — usable from .NET Framework 4.6.1+, .NET Core 3.0+ and .NET 5+.
- **SDK / runtime:** a .NET SDK with Roslyn 4.x (5.0+) to run the source generators; the in-repo demos use SDK 8.0+ and target `net9.0` — *tested* configurations, not requirements.
- **Package manager:** NuGet / `dotnet` CLI (`dotnet add package`, `dotnet restore`).
- **Required services:** none — the core engine is self-contained.


#### 2. Install / Add Dependency

Add the core package to a console or library project:

```bash
dotnet add package VeloxDev.Core
```

For a GUI demo, add the adapter for your UI framework:

```bash
dotnet add package VeloxDev.WPF   # or VeloxDev.Avalonia
```

| Framework | Adapter package |
|---|---|
| WPF | `VeloxDev.WPF` |
| Avalonia | `VeloxDev.Avalonia` |

The WPF demo imports `VeloxDev.WorkflowSystem.AttachedBehaviors` from the `VeloxDev.WPF` assembly (`Examples/Workflow/WPF/Demo/Views/Workflow/WorkflowView.xaml`, line 7). WinUI / MAUI adapters exist in the repository and are *inferred* to ship under the same `VeloxDev.*` naming convention.

**Expected result:** the project restores without errors, and `using VeloxDev.WorkflowSystem;` resolves.

#### 3. Basic Setup / Registration

Each component is a `partial` class annotated with a `[WorkflowBuilder.*]` attribute whose type parameter is the component's Helper. `[VeloxProperty]` turns a field into a change-notifying property; `[VeloxCommand]` turns a method into an `IVeloxCommand`. The source generator emits the backing members, `InitializeWorkflow()` and the `GetHelper()` wiring.

**Tree** — `[WorkflowBuilder.Tree<THelper>]`:

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Tree<TreeHelper>]
public partial class MyTree
{
    public MyTree() => InitializeWorkflow();

    [VeloxProperty] private bool isWorkflowRunning = false;
}
```

**Node** — `[WorkflowBuilder.Node<THelper>(workSemaphore: n)]`; `workSemaphore` is the concurrency capacity of the node's `ReceiveCommand`:

```csharp
[WorkflowBuilder.Node<NodeHelper<MyNode>>(workSemaphore: 1)]
public partial class MyNode
{
    public MyNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}
```

**Slot** and **Link**:

```csharp
[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class MyLink
{
    public MyLink() => InitializeWorkflow();

    [VeloxProperty] private bool usePolyline = true;
}
```

**Expected result:** the project compiles. Each component exposes `InitializeWorkflow()` (generated), `GetHelper()`, and the generated command properties (`CreateNodeCommand`, `UndoCommand`, `ReceiveCommand`, `DeleteCommand`, …).

#### 4. Core Usage (Step by Step)

**1. Create the tree and set the canvas size.**

```csharp
var tree = new MyTree();
tree.Layout.OriginSize = new Size(1200, 800);
var helper = tree.GetHelper();
```

**Expected result:** `tree.Layout.OriginSize` is `(1200, 800)`; `helper` is the generated `TreeHelper` instance whose `Install` has subscribed to the tree's `Nodes` / `Links` collections (`Src/Core/VeloxDev.Core/WorkflowSystem/Templates/Helpers/TreeHelper.cs`, lines 109-124).

**2. Register nodes through the helper.**

```csharp
var a = new MyNode { Anchor = new Anchor(40, 200), Size = new Size(200, 120) };
var b = new MyNode { Anchor = new Anchor(400, 200), Size = new Size(200, 120) };
helper.CreateNode(a);
helper.CreateNode(b);
```

`helper.CreateNode(node)` funnels into `StandardCreateNode`, which submits an undoable `WorkflowActionPair` and adds the node to `tree.Nodes` (`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, lines 27-40).

**Expected result:** `tree.Nodes.Count == 2`; `a.Parent` and `b.Parent` reference `tree`. The undo stack now holds one entry per `CreateNode`.

**3. Create slots and configure their channels.**

```csharp
a.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
a.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };
b.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
b.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };
```

`SlotChannel` is a `[Flags]` enum: `OneSource` allows at most 1 incoming connection, `OneTarget` at most 1 outgoing connection (`Src/Core/VeloxDev.Core/WorkflowSystem/Enums/Slot.cs`).

**Expected result:** `a.Input.Channel == SlotChannel.OneSource`; each slot is registered in its parent node's `Slots` collection with `Parent` set.

**4. Connect the slots.**

```csharp
helper.SendConnection(a.Output);
helper.ReceiveConnection(b.Input);
```

The connection protocol is two-phase (`Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`, lines 97-171): `SendConnection` checks the sender's capacity, shows the `VirtualLink` and marks `SlotState.PreviewSender`; `ReceiveConnection` validates capacity + `ValidateConnection`, cleans up conflicting same-direction connections, then `CreateLink` builds the link and the whole connection is submitted as one undoable `WorkflowActionPair`.

**Expected result:** `tree.Links.Count == 1`; `tree.LinksMap[a.Output][b.Input]` is the created link; `a.Output.Targets` contains `b.Input` and `b.Input.Sources` contains `a.Output`. Calling `tree.UndoCommand.Execute(null)` removes the link; `tree.RedoCommand.Execute(null)` restores it.

**5. Compile and run the graph.**

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;

var compiler = new CompilerViewModel();
await compiler.CompileAsync(a);                              // start node = a
var graph = compiler.Graphs.FirstOrDefault();
if (graph is not null)
    await new CompilerEngine().RunAsync(
        graph, new RuntimeContext { Data = "seed" }, CancellationToken.None);
```

`CompileAsync` decomposes the subgraph reachable from `a` into acyclic `CompiledGraph`s (linear segments → `ExecuteEntry`; nodes implementing `ICompileTimeRouter` → `BranchEntry`; a route key pointing to multiple downstreams → `ParallelEntry`). `RunAsync` drives each entry, injecting the `RuntimeContext` into `IRuntimeAware` nodes and chaining return values through `ReceiveAsync` (`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/CompilerViewModel.cs`, `CompilerEngine.cs`).

**Expected result:** after the run, `graph.Entries` is non-empty and `context.Status` is `"Completed"` (or `"Stopped"` on cancellation).

**6. Serialize / deserialize the whole tree.**

```csharp
using VeloxDev.MVVM.Serialization;

var json = tree.Serialize();
var copy = json.Deserialize<MyTree>();
copy.Layout.UpdateCommand.Execute(null);
```

`ComponentModelEx.Serialize<T>` writes the whole graph (nodes, slots, links, layout, custom `[VeloxProperty]` data) to JSON via Newtonsoft; `Deserialize<T>` rebuilds it. `CanvasLayout.UpdateCommand` re-applies the layout (`Src/Core/VeloxDev.Core.Extension/ComponentModelEx.cs`; `Src/Core/VeloxDev.Core/WorkflowSystem/CanvasLayout.cs`).

**Expected result:** `copy.Nodes.Count == 2`, the connection `LinksMap` is restored, and `copy.Layout.OriginSize == (1200, 800)`.

#### 5. Verification

- **Tests:** the `WorkflowSystem` test project covers the value types (`AnchorTests`, `SizeTests`, `ViewportTests`, `OffsetTests`, `CellKeyTests`, `CanvasLayoutTests`), the spatial index (`SpatialGridHashMapTests`), the selector (`SlotEnumeratorTests`), action pairs (`WorkflowActionPairTests`, `WorkflowHistoryTests`, `WorkflowUndoCountTests`) and tree operations (`WorkflowTreeExTests`) — `Src/Core/VeloxDev.Core.Test/WorkflowSystem`. Compiler semantics (`CompilerExTests`, `ParallelFanOutTests`, `RedirectTests`, `TerminalBranchTests`) and serialization (`WorkflowSerializationTests`) live in `Src/Core/VeloxDev.Core.Extension.Test/Agent/Workflow/Functions`.
- **Demo:** the WPF demo (`Examples/Workflow/WPF/Demo`) opens a ready-made multi-controller graph with Undo / Redo / Save / Load and a 1000-node performance test. Its session builder shows the same API you just used — `WorkflowDemoSession.Create()` in `Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`.

#### 6. Complete Code

A minimal, self-contained, end-to-end sample combining all the steps above. Every identifier is defined below or comes from the `VeloxDev.*` packages.

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.MVVM.Serialization;
using VeloxDev.WorkflowSystem;

[WorkflowBuilder.Tree<TreeHelper>]
public partial class MyTree
{
    public MyTree() => InitializeWorkflow();
}

[WorkflowBuilder.Node<NodeHelper<MyNode>>(workSemaphore: 1)]
public partial class MyNode
{
    public MyNode() => InitializeWorkflow();

    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Link<LinkHelper>]
public partial class MyLink
{
    public MyLink() => InitializeWorkflow();
}

public static class Program
{
    public static async Task RunAsync()
    {
        var tree = new MyTree();
        tree.Layout.OriginSize = new Size(1200, 800);
        var helper = tree.GetHelper();

        var a = new MyNode { Anchor = new Anchor(40, 200), Size = new Size(200, 120) };
        var b = new MyNode { Anchor = new Anchor(400, 200), Size = new Size(200, 120) };
        helper.CreateNode(a);
        helper.CreateNode(b);

        a.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
        a.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };
        b.Input = new SlotViewModel { Channel = SlotChannel.OneSource };
        b.Output = new SlotViewModel { Channel = SlotChannel.OneTarget };

        helper.SendConnection(a.Output);
        helper.ReceiveConnection(b.Input);

        var compiler = new CompilerViewModel();
        await compiler.CompileAsync(a);
        var graph = compiler.Graphs.FirstOrDefault();
        if (graph is not null)
            await new CompilerEngine().RunAsync(
                graph, new RuntimeContext { Data = "seed" }, CancellationToken.None);

        var json = tree.Serialize();
        var copy = json.Deserialize<MyTree>();
        copy.Layout.UpdateCommand.Execute(null);
    }
}
```

#### 7. Run Declaration

- ⚠️ Not actually run — statically verified only. This sample was written against the real source (compiler, `StandardEx`, demo session) and mirrors `WorkflowDemoSession.Create()` and `ControllerViewModel`, but it was not compiled in a console project during documentation authoring. Treat the `Program.RunAsync` body as a guide; build it inside a real project to execute.
