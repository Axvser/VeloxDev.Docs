# 工作流系统 — 定义组件

四种组件都以 `[WorkflowBuilder.*]` 修饰一个 `partial class`，类型参数是它的 Helper；`[VeloxProperty]` 把字段/分部属性变成可通知属性。下面的类就是[完整代码](../07_complete-code/index.md)里的类型，抄进去即可编译。

```csharp
using VeloxDev.Core.WorkflowSystem.CompilerEx;
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;

namespace Demo.QuickStart;

// Tree —— 一张画布。自带 Layout / Nodes / Links / LinksMap 与 undo-redo 命令。
[WorkflowBuilder.Tree<TreeHelper>]
public partial class CalcTree
{
    public CalcTree() => InitializeWorkflow();
}

// Slot —— 连接端点（输入口/输出口共用一种 ViewModel）。
[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

// Node —— 一个可执行节点。声明两个 Slot 型属性（自动预置默认槽位），
// 并实现 ICompileTimeAware：编译结束后收到自己的编译身份 CompileContext。
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
```

要点：

- **槽位是节点的一部分。** 每个 `Slot` 型的 `[VeloxProperty]` 成员在构造（`InitializeWorkflow`）时被预置一个默认 `SlotViewModel` 并注册进 `Slots`；随后用 `SetChannelCommand` 配置通道容量（见 [03 构建画布](../03_build-canvas/index.md)）。
- **节点不写 `ReceiveAsync`，业务写在 Helper 上。** `CalcNodeHelper` 继承 `NodeHelper<CalcNode>` 并重写 `ReceiveAsync`：入参是 `ITaskContext`（数据流任务上下文），返回值会被写回运行时上下文的 `Data`，供下游节点读取。实现 `ICompileTimeAware` 后还能读出本次编译分配的全局序号 `Order`（`-1` = 绝对停止态）。

在**同一文件、同一命名空间**内追加这个 Helper 类（继续上面声明的 `Demo.QuickStart`）：

```csharp
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
```

`WorkSemaphore: 1` 表示该节点 `ReceiveCommand` 的并发容量为 1（与仓库示例一致）。

**关于 Link：** 不需要自己声明 Link 类 —— 树默认用 `LinkDefaultViewModel`（`TreeHelper.CreateLink`）。若想给连线加样式/业务字段，照 Demo 的 `Examples/Workflow/Common/Lib/ViewModels/Workflow/LinkViewModel.cs` 那样 `[WorkflowBuilder.Link<LinkHelper>]` 声明一个即可，本示例不展开。

**预期结果：** 项目编译通过；`new CalcNode()` 后 `node.Input`、`node.Output` 非空且都已注册进 `node.Slots`（每个 Slot 型 `[VeloxProperty]` 对应一个预置默认槽位）；`new CalcTree()` 暴露 `Layout`、`Nodes`、`Links`、`GetHelper()` 与 undo/redo 命令。

## 下一步

组件定义好了，进入 [03 构建画布](../03_build-canvas/index.md) 把节点连成图。
