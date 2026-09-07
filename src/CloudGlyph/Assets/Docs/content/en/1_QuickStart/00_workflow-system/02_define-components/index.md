# Workflow System — Define the Components

Create these files in the `WorkflowQuickStart` project. Every component is a `partial` class carrying a `[WorkflowBuilder.*]` attribute whose type argument is the component's **Helper**; the source generator turns it into a full ViewModel (`InitializeWorkflow()`, `GetHelper()`, command wiring, slot registration, undo/redo plumbing).

## 1. Tree, Slot and Link components

File `Components.cs`:

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

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
```

`QuickTree` is the canvas that owns the `Nodes` / `Links` collections; `QuickSlot` is an input (receiver) or output (sender) endpoint of a connection; `QuickLink` is the visible connection between two slots. The three match the real demo components `TreeViewModel`, `SlotViewModel`, `LinkViewModel` in `Examples/Workflow/Common/Lib/ViewModels/Workflow/`.

**Expected result:** `QuickTree.GetHelper()`, `QuickSlot.GetHelper()`, `QuickLink.GetHelper()` all exist (generated) and return their `TreeHelper` / `SlotHelper` / `LinkHelper` instances.

## 2. Node components and their execution logic

Each node pairs a `[WorkflowBuilder.Node<TNodeHelper>]` ViewModel with a custom helper derived from `NodeHelper<TNode>` that overrides `ReceiveAsync`. The helper is how a node computes: the runtime drives `node.GetHelper().ReceiveAsync(context, ct)` and the returned value becomes the node's output (chained downstream as `context.Data`).

File `Nodes.cs`:

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

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
```

Notes on what is real:

- `ICompileTimeAware` is the compile-injection hook (`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/Contracts/ICompileTimeAware.cs`). When compilation finishes, the compiler hands each such node an `ICompileContext` with its fixed `Order` / `ChainIndex` / `Offset`; `Order == -1` marks the absolute-stop state.
- `workSemaphore: 1` is the concurrency capacity of the node's receive task (same default as the demo nodes, e.g. `TimerNodeViewModel`).
- A custom helper returning a value mirrors the demo `TimerHelper` / `EnumSelectorHelper` overrides exactly (`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/TimerHelper.cs`).

**Expected result:** the project compiles. Each node exposes generated `InputSlot` / `OutputSlot` (registered into its `Slots` collection) and `GetHelper()` returning its typed helper; the compile step later fills each node's `CompileContext`.

Go to [Build the graph](../03_build-a-graph/index.md).
