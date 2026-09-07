# 工作流系统 — 构建画布

把 [02 定义组件](../02_define-components/index.md) 的 `CalcTree` / `CalcNode` 实例注册进画布并连成一张**扇出图**：`Source` 的出线同时接到 `Report` 与 `Discard`（本页类型沿用前页定义，最终代码见 [07 完整代码](../07_complete-code/index.md)）。

#### 1. 建树并设定画布尺寸

```csharp
var tree = new CalcTree();
tree.Layout.OriginSize = new Size(1200, 800);
var helper = tree.GetHelper();
```

`tree.Layout.OriginSize` 是世界坐标范围；`helper` 是生成的 `TreeHelper`，其 `Install` 已订阅树的 `Nodes` / `Links` 集合。

**预期结果：** `tree.Layout.OriginSize.Width == 1200`；`helper` 非空。

#### 2. 创建并注册三个节点

```csharp
var source = new CalcNode { Title = "Source", Kind = "double", Anchor = new Anchor(40, 200, 0) };
var report = new CalcNode { Title = "Report", Kind = "pass", Anchor = new Anchor(420, 120, 0) };
var discard = new CalcNode { Title = "Discard", Kind = "pass", Anchor = new Anchor(420, 360, 0) };

helper.CreateNode(source);
helper.CreateNode(report);
helper.CreateNode(discard);
```

`helper.CreateNode(node)` 汇入 `StandardCreateNode`：把“加入 `tree.Nodes` 并把 `node.Parent` 指向树”作为一条可撤销的 `WorkflowActionPair` 提交。

**预期结果：** `tree.Nodes.Count == 3`；`source.Parent == tree`；每次 `CreateNode` 对应一条撤销历史。

#### 3. 配置通道容量

```csharp
source.Output.SetChannelCommand.Execute(SlotChannel.MultipleTargets);
report.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
discard.Input.SetChannelCommand.Execute(SlotChannel.OneSource);
```

`SlotChannel` 是位掩码：`Target` = 该槽能主动连出的目标数，`Source` = 能被连入的来源数。此处 `Output` 需要多条出向连接 → `MultipleTargets`；两个 `Input` 各只接受 1 条入向 → `OneSource`。通道要在节点已挂进树之后设置（`SetChannel` 会清理已存在的越限连线，故需 `slot.Parent.Parent` 就绪）。

**预期结果：** `source.Output.Channel == SlotChannel.MultipleTargets`，`report.Input.Channel == OneSource`，`discard.Input.Channel == OneSource`。

#### 4. 连线（两阶段连接协议）

```csharp
helper.SendConnection(source.Output);
helper.ReceiveConnection(report.Input);
helper.SendConnection(source.Output);
helper.ReceiveConnection(discard.Input);
```

连接协议是两阶段的（见 `Src/Core/VeloxDev.Core/WorkflowSystem/StandardEx/WorkflowTreeEx.cs`）：`SendConnection` 校验发送端容量并进入预览态；`ReceiveConnection` 校验接收端容量 + `ValidateConnection`，再 `CreateLink` 建立一条连线，整条连线作为一条 `WorkflowActionPair` 提交（可撤销/重做）。

**预期结果：** `tree.Links.Count == 2`；`source.Output.Targets` 含 `report.Input` 与 `discard.Input`；`report.Input.Sources`、`discard.Input.Sources` 各含 `source.Output`。整段构建打印：

```text
Nodes=3 Links=2 source.Output.Targets=2 channels=MultipleTargets|OneSource|OneSource
```

#### 5. 撤销 / 重做

画布编辑统一走一条可撤销历史：节点创建、连线都是通过 `TreeHelper.Submit(WorkflowActionPair)` 入栈的（撤销/重做语义由 `Src/Core/VeloxDev.Core.Test/WorkflowSystem/WorkflowHistoryTests.cs` 等覆盖）。GUI Demo 里对应的就是工具栏的撤销/重做按钮。

**预期结果：** 一次 `tree.UndoCommand.Execute(null)` 会撤销最近的一次操作 —— 本示例中 `tree.Links.Count` 由 2 变为 1（移除最后创建的那条连线）。

> 说明：`UndoCommand` 的 `Execute` 是异步命令的同步入口；在真实 GUI 中由按钮触发、由 UI 线程协调。控制台里若要按序连续撤销多次，建议改用 `await tree.UndoCommand.ExecuteAsync(null)` 并逐个等待，避免同步竞态。

## 下一步

图画好了，进入 [04 编译与正向运行](../04_compile-and-run/index.md) 编译并驱动它。
