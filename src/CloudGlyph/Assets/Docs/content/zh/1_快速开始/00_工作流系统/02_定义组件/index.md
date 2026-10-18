# 工作流系统 — 定义组件

在 `WorkflowQuickStart` 工程里创建这些文件。每个组件都是一个 `partial` 类，携带 `[WorkflowBuilder.*]` 特性，泛型参数是它的 **Helper**；源生成器会把它变成完整 ViewModel（`InitializeWorkflow()`、`GetHelper()`、命令接线、槽注册、撤销/重做管线）。

## 1. Tree、Slot 与 Link 组件

文件 `Components.cs`：

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

`QuickTree` 是拥有 `Nodes` / `Links` 集合的画布；`QuickSlot` 是连接的输入（接收）或输出（发送）端点；`QuickLink` 是两个槽之间的可见连线。三者对应 `Examples/Workflow/Common/Lib/ViewModels/Workflow/` 中的真实 demo 组件 `TreeViewModel`、`SlotViewModel`、`LinkViewModel`。

**预期结果：** 生成的 `QuickTree.GetHelper()`、`QuickSlot.GetHelper()`、`QuickLink.GetHelper()` 都存在，并分别返回 `TreeHelper` / `SlotHelper` / `LinkHelper` 实例。

## 2. 节点组件及其执行逻辑

每个节点把一个 `[WorkflowBuilder.Node<TNodeHelper>]` ViewModel 与一个派生自 `NodeHelper<TNode>`、重写 `ReceiveAsync` 的 Helper 配成一对。Helper 就是节点的计算方式：运行时驱动 `node.GetHelper().ReceiveAsync(context, ct)`，返回值成为该节点的输出（作为 `context.Data` 继续链下去）。

文件 `Nodes.cs`：

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

要点：

- `ICompileTimeAware` 是编译注入钩子（`Src/Core/VeloxDev.Core/WorkflowSystem/CompilerEx/Compile/Contracts/ICompileTimeAware.cs`）。编译结束时，编译器给每个这样的节点一个 `ICompileContext`，携带固定的 `Order` / `ChainIndex` / `Offset`；`Order == -1` 表示绝对停止态。
- `workSemaphore: 1` 是该节点接收任务的并发容量（与 demo 节点相同，例如 `TimerNodeViewModel`）。
- 自定义 Helper 返回值的写法与 demo 的 `TimerHelper` / `EnumSelectorHelper` 重写完全一致（`Examples/Workflow/Common/Lib/ViewModels/Workflow/Helper/TimerHelper.cs`）。

**预期结果：** 工程可编译。每个节点暴露生成的 `InputSlot` / `OutputSlot`（注册进它的 `Slots` 集合）与返回类型化 Helper 的 `GetHelper()`；后续编译步骤会填充每个节点的 `CompileContext`。

前往「构建图」。
