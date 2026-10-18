# 工作流系统 — 构建图

添加 `Program.cs`（`WorkflowQuickStart` 中的静态 `Main`），构建 `Ticker → Bias → Printer` 三节点链。下面各步是同一个 `Build()` 方法的片段 —— 按顺序放进方法体，位于 `return tree;` 之前。这些调用都是 demo 会话构建器用到的树 Helper API（`Examples/Workflow/Common/Lib/ViewModels/Workflow/WorkflowDemoSession.cs`）。

## 1. 创建树并注册节点

```csharp
using VeloxDev.WorkflowSystem;

namespace WorkflowQuickStart;

public static class GraphBuilder
{
    public static QuickTree Build()
    {
        var tree = new QuickTree();
        tree.Layout.OriginSize = new Size(2400, 850);
        var helper = tree.GetHelper();

        var ticker = new TickerNode { Anchor = new Anchor(60, 60, 0) };
        var bias = new BiasNode { Anchor = new Anchor(460, 60, 0) };
        var printer = new PrinterNode { Anchor = new Anchor(860, 60, 0) };

        helper.CreateNode(ticker);
        helper.CreateNode(bias);
        helper.CreateNode(printer);

        return tree;
    }
}
```

`helper.CreateNode(node)`（`IWorkflowTreeViewModelHelper` 上的方法）提交一个可撤销的 `WorkflowActionPair`，并把节点加入 `tree.Nodes` —— 见 `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs` 的 `StandardCreateNode`。

**预期结果：** `tree.Nodes.Count == 3`；每个节点的 `Parent` 指向树；撤销栈中每次 `CreateNode` 有一条记录。

## 2. 配置槽通道

槽的 `SlotChannel`（`VeloxDev.WorkflowSystem` 中的 `[Flags]` 枚举）声明每个方向的连接容量：`OneSource` = 最多一条入向连接，`OneTarget` = 最多一条出向连接（`Src/Core/VeloxDev.Core/WorkflowSystem/Enums/Slot.cs`）。通过槽的 `SetChannelCommand` 设置，绝不要用新实例替换生成的槽（demo 警告：替换预置槽会触发它的 `DeleteCommand`，产生幽灵撤销记录）：

```csharp
private static void SetChannel(QuickSlot slot, SlotChannel channel)
    => slot.SetChannelCommand.Execute(channel);
```

配置三条有效边的四个端点：`Ticker.Output`、`Bias.Input`、`Bias.Output`、`Printer.Input`：

```csharp
SetChannel(ticker.OutputSlot, SlotChannel.OneTarget);
SetChannel(bias.InputSlot, SlotChannel.OneSource);
SetChannel(bias.OutputSlot, SlotChannel.OneTarget);
SetChannel(printer.InputSlot, SlotChannel.OneSource);
```

**预期结果：** 每个配置过的槽报告新的 `Channel`；不产生撤销记录（`SetChannelCommand` 是标准、不可撤销路径）。

## 3. 连接槽

连接协议在树 Helper 上分两阶段：`SendConnection(outputSlot)` 从发送端打开预览，`ReceiveConnection(inputSlot)` 校验容量与用户规则、清理同向冲突连线，然后创建 `QuickLink` —— 整个连接作为一个可撤销动作提交（见 `WorkflowTreeEx.cs` 的 `StandardSendConnection` / `StandardReceiveConnection`）：

```csharp
helper.SendConnection(ticker.OutputSlot!);
helper.ReceiveConnection(bias.InputSlot!);

helper.SendConnection(bias.OutputSlot!);
helper.ReceiveConnection(printer.InputSlot!);
```

**预期结果：** `tree.Links.Count == 2`；`tree.LinksMap[ticker.OutputSlot][bias.InputSlot]` 与 `tree.LinksMap[bias.OutputSlot][printer.InputSlot]` 已设置；`bias.InputSlot.Sources` 含 `ticker.OutputSlot`，`bias.OutputSlot.Targets` 含 `printer.InputSlot`。每个连接是一个 `WorkflowActionPair`，所以 `tree.UndoCommand.Execute(null)` 移除最近创建的连线，再撤销一次移除另一条（`tree.RedoCommand.Execute(null)` 以同样方式恢复）。

编译器消费的拓扑正是这些槽的 `Targets` / `Sources` 边。前往「编译并运行」。
