# 工作流图模型

图模型位于 `VeloxDev.Core`，命名空间 `VeloxDev.WorkflowSystem`。树持有节点，节点持有插槽，连线把发送端插槽接到接收端插槽。四个角色各有一个接口、一个默认视图模型，以及一个承载其行为的助手。

下面按角色拆分整个公开面：

- [组件契约](00_组件契约/index.md) — 四个组件接口、助手契约与共同的生命周期成员。
- [默认视图模型](01_默认视图模型/index.md) — 生成器特性与四个 sealed 默认实现。
- [组件助手](02_组件助手/index.md) — `TreeHelper<T>`、`NodeHelper<T>`、`SlotHelper<T>` 与 `LinkHelper<T>`。
- [几何模型](03_几何模型/index.md) — `Anchor`、`Size`、`Offset`、`Scale`、`CanvasLayout`、`Viewport`、`ZoomCenter` 与 `WorkflowBounds`。

```csharp
var tree = new TreeDefaultViewModel();
var node = new NodeDefaultViewModel { Anchor = new Anchor(60, 80, 0), Size = new Size(220, 120) };
tree.GetHelper().CreateNode(node);

Console.WriteLine($"{tree.Nodes.Count} {node.Slots.Count} {node.GetWorldAnchor()}");
```

大多数宿主走生成组件路径（`[WorkflowBuilder.*]` 加 `InitializeWorkflow`）；默认视图模型则是生成器的助手在未指定自定义类型时实例化的具体类型。任务式教程见[工作流图模型](../../1_快速开始/00_工作流图模型/index.md)。
