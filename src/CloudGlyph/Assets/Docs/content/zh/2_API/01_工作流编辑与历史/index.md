# 工作流编辑与历史

每次结构性改动都是组件上的命令，每条这样的命令都会在树的撤销栈上记录一个 `IActionPair`。实现这些命令的标准操作是 `VeloxDev.WorkflowSystem.StandardEx` 中的扩展方法。

- [动作与命令](00_动作与命令/index.md) — `IActionPair`、`ActionPair`、`WorkflowCommandEx` 与完整命令集。
- [树操作](01_树操作/index.md) — `WorkflowTreeEx`：节点创建、撤销/重做与拓扑查询。
- [节点插槽连线操作](02_节点插槽连线操作/index.md) — `WorkflowNodeEx`、`WorkflowSlotEx` 与 `WorkflowLinkEx`。

```csharp
var tree = new TreeDefaultViewModel();
var a = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0) };
var b = new NodeDefaultViewModel { Anchor = new Anchor(420, 80, 0) };
tree.GetHelper().CreateNode(a);
tree.GetHelper().CreateNode(b);

tree.GetHelper().Undo();          // 以一项移除 b
tree.GetHelper().Redo();          // 放回 b
Console.WriteLine($"{tree.Nodes.Count}");
```

连线构建操作（`StandardSendConnection`、`StandardReceiveConnection`、`StandardCheckConnection`、预览方法）记录在[连接规则与预览](../02_连接规则与预览/index.md)下，因为它们的规则属于那个特性。任务式教程见[工作流编辑与历史](../../1_快速开始/01_工作流编辑与历史/index.md)。
