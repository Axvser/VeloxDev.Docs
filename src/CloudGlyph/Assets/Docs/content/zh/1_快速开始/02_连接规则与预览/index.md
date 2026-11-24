# 连接规则与预览

一条连线只有在框架规则、树 Helper 自己的规则以及宿主的释放时否决三者都同意时才成立。同一套规则也驱动拖拽预览，因此绿色的橡皮筋与最终建立的连线不可能互相矛盾。

本页接着[工作流图模型](../00_工作流图模型/index.md)。

## 1. 前置条件

- `VeloxDev.Core` 与 `VeloxDev.Core.Generator` **12.3.0**，.NET SDK 9+。
- 不需要指针设备：预览 API 由调用驱动，不依赖 GUI。适配器通常在自己的指针事件里调用同一批方法。

## 2. 安装

```powershell
dotnet add package VeloxDev.Core --version 12.3.0
dotnet add package VeloxDev.Core.Generator --version 12.3.0
```

**预期结果：** 项目构建通过，组件类可以编译。

## 3. 通道决定方向与容量

`SlotChannel` 是位标志枚举：一个方向可以向外（`OneTarget`、`MultipleTargets`），可以入槽（`OneSource`、`MultipleSources`），也可以双向（`OneBoth`、`MultipleBoth`）。生成的插槽默认是 `MultipleBoth`。

```csharp
a.Output.SetChannelCommand.Execute(SlotChannel.OneTarget);
b.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
```

**预期结果：** `a.Output` 可向一个目标发送；`b.Input` 可接收一个来源。

通道带来两个行为：

- 通道不允许发送的端口会被拒绝作为发送端（`SenderCannotSend`）；不允许接收的会被拒绝作为接收端（`ReceiverCannotReceive`）。
- 容量不是检查项。完成连线时会**按通道清理已有连线**——`OneTarget` 发送端会丢掉上一条出线，`OneSource` 接收端会丢掉上一条入线。检查通过的含义是「可以接受，可能是在这次清理之后」。

修改通道本身就可能拆掉连线，因此它是搭建期设置，不是可撤销编辑（见[工作流编辑与历史](../01_工作流编辑与历史/index.md)）。

## 4. 先问一对端口能否连接

`StandardCheckConnection` 是纯查询：不触发事件、不改状态、不产生预览。它会指出第一条拒绝该端口的规则。

```csharp
var check = tree.StandardCheckConnection(a.Output, b.Input);
Console.WriteLine($"A->B valid={check.IsValid} reason={check.Reason}");

var same = tree.StandardCheckConnection(a.Output, a.Input);
Console.WriteLine($"A->A valid={same.IsValid} reason={same.Reason}");
```

**预期结果：** `A->B valid=True reason=None`；`A->A valid=False reason=SameNode`。

拒绝原因按检查顺序如下：

| `ConnectionRejectReason` | 含义 |
| --- | --- |
| `SenderCannotSend` | 发送端通道没有向外方向。 |
| `ReceiverCannotReceive` | 接收端通道没有向内方向。 |
| `SameNode` | 两个端口属于同一个节点。 |
| `RejectedByRule` | 树 Helper 的 `ValidateConnection` 返回 `false`。 |
| `RejectedByHost` | 某个 `PreviewValidating` 订阅者只否决了这次预览。 |

## 5. 宿主规则与释放时否决

在树 Helper 上重写 `ValidateConnection`，为整个编辑器声明一条规则：

```csharp
public sealed class GuardedTreeHelper : TreeHelper<DemoTree>
{
    public override bool ValidateConnection(ISlotComponent sender, ISlotComponent receiver)
        => (receiver.Parent as DemoNode)?.Title != "Blocked";
}
```

**预期结果：** 第 4 步通过的那对端口，在指向标题为 `Blocked` 的节点时报告 `RejectedByRule`。

释放时还会再问一次 `ValidateConnection`。若想只否决这一次拖拽、又不继承 Helper，可订阅 `ITreeEvents.Connecting` 并设置 `PreventDefault`；连线不会创建。预览从不咨询这个事件——它是释放时的决定。

```csharp
var events = (ITreeEvents)tree.GetHelper();
events.Connecting += (_, e) => e.Handle.PreventDefault = true;
```

**预期结果：** 释放被否决后，`tree.Links.Count == 0`。

## 6. 驱动拖拽预览

`WorkflowInput.For(tree)` 是每棵树唯一的输入路由。适配器在每次指针移动时报告候选插槽；拖拽状态由这条路由持有。

```csharp
var input = WorkflowInput.For(tree);
input.PreviewChanged += (_, e) =>
    Console.WriteLine($"preview {e.State} reason={e.Check?.Reason}");

tree.GetHelper().SendConnection(a.Output);        // Started：发送端已固定
tree.StandardSetPreviewReceiver(b.Input);         // ValidTarget
tree.StandardSetPreviewReceiver(blocked.Input);   // InvalidTarget：RejectedByRule
tree.GetHelper().ResetVirtualLink();              // None
```

`ConnectionPreviewState` 依次经过 `Started` → `ValidTarget` / `InvalidTarget` → `None`。候选插槽同时带上对应的 `SlotState.PreviewSender` / `SlotState.PreviewReceiver` 位；默认虚拟连线 `LinkDefaultViewModel` 实现了 `IConnectionPreviewLink`，连线视图可直接按 `Preview` 绘制。

预览只能**收紧**框架规则。订阅 `PreviewValidating` 并调用 `Reject`，即可否决一个框架已接受的候选；框架已经拒绝的候选不会交给你。

```csharp
input.PreviewValidating += (_, e) => e.Reject("blocked by policy");
tree.GetHelper().SendConnection(a.Output);
tree.StandardSetPreviewReceiver(b.Input);
```

**预期结果：** 状态变为 `InvalidTarget`，原因 `RejectedByHost`；释放时规则不受影响。

同一个候选不会在每次指针移动时重新校验。异步结论返回后，调用 `tree.StandardRefreshConnectionPreview()` 对指针下的当前候选重跑一次检查。

## 7. 验证

```powershell
dotnet run
```

预期输出：

```text
A->B valid=True reason=None
A->A valid=False reason=SameNode
A->Blocked valid=False reason=RejectedByRule
B.Input as sender: valid=False reason=SenderCannotSend
preview Started (sender=True, receiver=False, reason=)
preview ValidTarget (sender=True, receiver=True, reason=None)
preview InvalidTarget (sender=True, receiver=True, reason=RejectedByRule)
preview None (sender=False, receiver=False, reason=)
preview Started (sender=True, receiver=False, reason=)
preview InvalidTarget (sender=True, receiver=True, reason=RejectedByHost)
after preview veto: InvalidTarget / RejectedByHost
preview None (sender=False, receiver=False, reason=)
after release veto: links=0
```

## 8. 完整代码

```csharp
using VeloxDev.MVVM;
using VeloxDev.WorkflowSystem;
using VeloxDev.WorkflowSystem.StandardEx;

namespace QuickStart.ConnectionRules;

[WorkflowBuilder.Node<NodeHelper>]
public partial class DemoNode
{
    public DemoNode() => InitializeWorkflow();
    [VeloxProperty] public partial SlotViewModel Input { get; set; }
    [VeloxProperty] public partial SlotViewModel Output { get; set; }
    [VeloxProperty] private string title = "Node";
}

[WorkflowBuilder.Slot<SlotHelper>]
public partial class SlotViewModel
{
    public SlotViewModel() => InitializeWorkflow();
}

[WorkflowBuilder.Tree<GuardedTreeHelper>]
public partial class DemoTree
{
    public DemoTree() => InitializeWorkflow();
}

/// <summary>The host's own rule: a connection into a node titled "Blocked" is refused.</summary>
public sealed class GuardedTreeHelper : TreeHelper<DemoTree>
{
    public override bool ValidateConnection(ISlotComponent sender, ISlotComponent receiver)
        => (receiver.Parent as DemoNode)?.Title != "Blocked";
}

public static class Program
{
    public static void Main()
    {
        var tree = new DemoTree();
        var a = new DemoNode { Title = "A" };
        var b = new DemoNode { Title = "B" };
        var blocked = new DemoNode { Title = "Blocked" };
        foreach (var n in new[] { a, b, blocked }) tree.GetHelper().CreateNode(n);

        a.Output.SetChannelCommand.Execute(SlotChannel.OneTarget);
        b.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
        blocked.Input.SetChannelCommand.Execute(SlotChannel.OneSource);

        var check = tree.StandardCheckConnection(a.Output, b.Input);
        Console.WriteLine($"A->B valid={check.IsValid} reason={check.Reason}");
        var same = tree.StandardCheckConnection(a.Output, a.Input);
        Console.WriteLine($"A->A valid={same.IsValid} reason={same.Reason}");
        var rule = tree.StandardCheckConnection(a.Output, blocked.Input);
        Console.WriteLine($"A->Blocked valid={rule.IsValid} reason={rule.Reason}");
        var capacity = tree.StandardCheckConnection(b.Input, a.Output);
        Console.WriteLine($"B.Input as sender: valid={capacity.IsValid} reason={capacity.Reason}");

        var input = WorkflowInput.For(tree);
        input.PreviewChanged += (_, e) =>
            Console.WriteLine($"preview {e.State} (sender={e.Sender is not null}, receiver={e.Receiver is not null}, reason={e.Check?.Reason})");

        tree.GetHelper().SendConnection(a.Output);
        tree.StandardSetPreviewReceiver(b.Input);
        tree.StandardSetPreviewReceiver(blocked.Input);
        tree.GetHelper().ResetVirtualLink();

        // A preview-only refusal: the host refuses this candidate without changing the release rules.
        input.PreviewValidating += (_, e) => e.Reject("blocked by policy");
        tree.GetHelper().SendConnection(a.Output);
        tree.StandardSetPreviewReceiver(b.Input);
        Console.WriteLine($"after preview veto: {input.PreviewState} / {input.PreviewCheck?.Reason}");

        // The release-time veto, raised only when the pointer is released.
        var events = (ITreeEvents)tree.GetHelper();
        events.Connecting += (_, e) => e.Handle.PreventDefault = true;
        tree.GetHelper().SendConnection(a.Output);
        tree.GetHelper().ReceiveConnection(b.Input);
        Console.WriteLine($"after release veto: links={tree.Links.Count}");
    }
}
```

## 9. 运行声明

- ✅ 2026-11-25 使用 .NET SDK 10.0.401、针对 `VeloxDev.Core` 12.3.0 实际构建并运行；输出与「验证」一节完全一致。
