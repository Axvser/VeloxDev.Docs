# 平台适配器 — 配置：生成七个视图

`VeloxDev.WPF.Templates` 包提供**七个项模板**，可搭出已接好行为的工作流视图。在[安装](../01_安装/index.md)一节创建的 WPF 工程根目录运行。下面的类名不是随意取的：`WorkflowView.xaml` 会按名字引用 `NodeView`、`LinkView`、`GridDecorator`、`MinimapOverlay` 与 `TemplateSelector`，而 `NodeView` 内嵌 `SlotView`，所以要把它们放进同一个命名空间。

## 1. 生成视图套件

```powershell
dotnet new wpf-v-tree     -n WorkflowView      -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-node     -n NodeView          -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-slot     -n SlotView          -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-link     -n LinkView          -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-selector -n TemplateSelector  -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-decorator -n GridDecorator    -ns Demo.Views.Workflow -o Views
dotnet new wpf-v-minimap  -n MinimapOverlay    -ns Demo.Views.Workflow -o Views
```

**预期结果：** `Views/` 下生成十一个文件（`WorkflowView`、`NodeView`、`SlotView`、`LinkView` 各一个 `.xaml` + `.xaml.cs`；`TemplateSelector`、`GridDecorator`、`MinimapOverlay` 各一个 `.cs`），全部位于 `Demo.Views.Workflow` 命名空间。

## 2. 每个生成文件的作用

| 文件 | 模板 | 角色 |
|---|---|---|
| `WorkflowView.xaml(.cs)` | `wpf-v-tree` | 表面宿主：`WorkflowSurfaceBehavior`（含 `ZoomEnabled`）、命名的部件 `PART_ScrollViewer` / `PART_Canvas` / `PART_GridDecorator` / `PART_SurfaceBorder` / `PART_MinimapOverlay`、绑定 `Helper.VisibleItems` 的 `ViewPool`、`NodeTemplate` / `LinkTemplate` 两个 `DataTemplate` 及 `TemplateSelector` |
| `NodeView.xaml(.cs)` | `wpf-v-node` | 节点卡片：`WorkflowSlotLayoutBehavior`（`PART_InputSlot`、`PART_OutputSlots`、`CoordinateHostName="PART_Canvas"`），头部还有 `WorkflowNodeDragBehavior` |
| `SlotView.xaml(.cs)` | `wpf-v-slot` | 连接器：`WorkflowSlotConnectionBehavior.IsEnabled="True"`，外加执行 `SendConnectionCommand` / `ReceiveConnectionCommand` 的指针处理器；`SlotState` 决定颜色 |
| `LinkView.xaml(.cs)` | `wpf-v-link` | 被动的正交折线连线，`CanRender` 且连线可渲染时才绘制 |
| `TemplateSelector.cs` | `wpf-v-selector` | `DataTemplateSelector`，把 `IWorkflowLinkViewModel` / `IWorkflowSlotViewModel` / `IWorkflowNodeViewModel` / `IWorkflowTreeViewModel` 映射到四个 `DataTemplate` 属性 |
| `GridDecorator.cs` | `wpf-v-decorator` | 基于 `Grid` 的装饰层，实现 `IWorkflowGridDecorator`（网格层 + 浮动标尺），由表面行为喂偏移 |
| `MinimapOverlay.cs` | `wpf-v-minimap` | `WorkflowMinimapOverlay` 的子类，套用配色模板符号 |

每个生成文件的完整内容都在[完整代码](../05_完整代码/index.md)子页面里逐字重现。

## 3. 构建

```powershell
dotnet build
```

**预期结果：** 从 `VeloxDev.WPF` 包解析到行为命名空间 `VeloxDev.WorkflowSystem.AttachedBehaviors`，编译通过。运行时宿主仍需要一个 `IWorkflowTreeViewModel` 作为 `DataContext`——下一页讲解。
